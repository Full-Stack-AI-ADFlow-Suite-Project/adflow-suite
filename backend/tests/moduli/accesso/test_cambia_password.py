"""Cambio password e CLI: revoca, isolamento e transazioni PostgreSQL."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app import cli
from app.core.errori import DatiNonValidi, NonTrovato
from app.core.security import hash_token, verifica_password
from app.moduli.accesso import service
from app.moduli.accesso.models import Sessione
from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente

NUOVA_PASSWORD = "NuovaPasswordSoloTest!2026"
ORA = datetime(2026, 10, 8, tzinfo=timezone.utc)


def sessione(db, record, token):
    db.add(
        Sessione(
            utente_id=record.id,
            token_hash=hash_token(token),
            scade_il=ORA + timedelta(days=7),
        )
    )
    db.flush()


@pytest.mark.parametrize("ruolo", ["artigiano", "operatore", "admin"])
def test_cambia_password_scrypt_revoca_solo_sessioni_utente(db, ruolo):
    record = utente(db, ruolo, deve_cambiare_password=True)
    altro = utente(db)
    sessione(db, record, "prima")
    sessione(db, record, "seconda")
    sessione(db, altro, "altra")
    vecchio_hash = record.password_hash
    service.cambia_password(db, f" {record.email.upper()} ", NUOVA_PASSWORD)
    assert record.password_hash != vecchio_hash
    assert verifica_password(NUOVA_PASSWORD, record.password_hash)
    assert not verifica_password(PASSWORD_DI_PROVA, record.password_hash)
    assert not record.deve_cambiare_password
    assert record.attivo
    assert list(db.scalars(select(Sessione.utente_id))) == [altro.id]


def test_cambia_password_non_fa_commit_e_revoca_atomica(db):
    record = utente(db)
    sessione(db, record, "prima")
    vecchio_hash = record.password_hash
    with db.begin_nested() as savepoint:
        service.cambia_password(db, record.email, NUOVA_PASSWORD)
        assert db.scalar(select(Sessione)) is None
        savepoint.rollback()
    assert record.password_hash == vecchio_hash
    assert db.scalar(select(Sessione)) is not None


@pytest.mark.parametrize("password", ["", "x" * 1025, "\ud800"])
def test_password_invalida_non_modifica_hash_o_sessioni(db, password):
    record = utente(db)
    sessione(db, record, "prima")
    vecchio_hash = record.password_hash
    with pytest.raises(DatiNonValidi):
        service.cambia_password(db, record.email, password)
    assert record.password_hash == vecchio_hash
    assert db.scalar(select(Sessione)) is not None


@pytest.mark.parametrize("password", ["x", "x" * 1024, "  à😊\x00  "])
def test_password_non_normalizzata_ed_estremi_ammessi(db, password):
    record = utente(db)
    service.cambia_password(db, record.email, password)
    assert verifica_password(password, record.password_hash)


def test_cambio_non_riattiva_utente_disabilitato(db):
    record = utente(db, attivo=False)
    service.cambia_password(db, record.email, NUOVA_PASSWORD)
    assert not record.attivo


def test_cambio_email_assente(db):
    with pytest.raises(NonTrovato, match="Utente non trovato"):
        service.cambia_password(db, "assente@example.test", NUOVA_PASSWORD)


def test_cambio_identita_legacy_ambigua_non_sceglie_account(db):
    records = [
        utente(db, email="Persona@example.test"),
        utente(db, email="persona@example.test"),
    ]
    hashes = [record.password_hash for record in records]
    with pytest.raises(DatiNonValidi, match="Identità utente ambigua"):
        service.cambia_password(db, "PERSONA@example.test", NUOVA_PASSWORD)
    assert [record.password_hash for record in records] == hashes


@pytest.mark.parametrize("campo", ["email", "nome", "password"])
def test_crea_utente_unicode_non_rappresentabile(db, campo):
    dati = dict(
        email="persona@example.test",
        nome="Persona",
        password=NUOVA_PASSWORD,
        ruolo="admin",
    )
    dati[campo] = "\ud800"
    with pytest.raises(DatiNonValidi):
        service.crea_utente(db, **dati)


def test_cli_cambia_password_service_reale_senza_segreti(db, monkeypatch, capsys):
    record = utente(db)
    sessione(db, record, "prima")

    @contextmanager
    def transazione_test():
        with db.begin_nested():
            yield db

    monkeypatch.setattr(cli, "transazione", transazione_test)
    monkeypatch.setattr(cli, "getpass", lambda _: NUOVA_PASSWORD)
    assert cli.main(["cambia-password", "--email", record.email]) == 0
    assert verifica_password(NUOVA_PASSWORD, record.password_hash)
    assert db.scalar(select(Sessione)) is None
    output = capsys.readouterr()
    assert output.out == "Password cambiata.\n"
    assert NUOVA_PASSWORD not in output.out + output.err
    assert record.password_hash not in output.out + output.err
