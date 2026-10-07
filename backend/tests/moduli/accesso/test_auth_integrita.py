"""Identità ambigue e confini della transazione del chiamante."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.moduli.accesso import service
from app.moduli.accesso.models import Sessione, Utente
from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente


@pytest.mark.parametrize("ordine", [("admin", "artigiano"), ("artigiano", "admin")])
def test_email_legacy_ambigua_non_sceglie_un_account_arbitrario(db, client, ordine):
    # Il vincolo preesistente è case-sensitive, mentre il login normalizza.
    utente(db, ordine[0], email="Persona@example.test")
    utente(db, ordine[1], email="persona@example.test")
    risposta = client.post(
        "/api/auth/login",
        json={"email": "PERSONA@example.test", "password": PASSWORD_DI_PROVA},
    )
    assert risposta.status_code == 401
    assert risposta.json() == {"detail": "Email o password non corrette."}
    assert list(db.scalars(select(Sessione))) == []


def test_vincolo_di_record_pendente_non_diventa_errore_del_nuovo_utente(db):
    utente(db, email="esistente@example.test")
    db.add(
        Utente(
            email="esistente@example.test",
            nome="Pendente",
            ruolo="admin",
            password_hash="finto",
        )
    )
    # no_autoflush non impedisce a begin_nested di flushare prima del savepoint.
    # L'errore riguarda il record del chiamante, non quello creato dal service.
    with db.no_autoflush, pytest.raises(IntegrityError):
        service.crea_utente(
            db, "nuovo@example.test", PASSWORD_DI_PROVA, "Nuovo", "admin"
        )


def test_email_legacy_unica_con_maiuscole_continua_a_funzionare(db, client):
    record = utente(db, email="Persona@Example.test")
    risposta = client.post(
        "/api/auth/login",
        json={"email": "persona@example.test", "password": PASSWORD_DI_PROVA},
    )
    assert risposta.status_code == 200
    assert risposta.json()["id"] == record.id


def test_record_pendenti_validi_e_nuovo_utente_restano_nella_transazione(db):
    primo = Utente(
        email="pendente@example.test",
        nome="Pendente",
        ruolo="admin",
        password_hash="finto",
    )
    with db.begin_nested() as esterna:
        db.add(primo)
        with db.no_autoflush:
            secondo = service.crea_utente(
                db, "nuovo@example.test", PASSWORD_DI_PROVA, "Nuovo", "admin"
            )
        ids = (primo.id, secondo.id)
        assert all(record_id is not None for record_id in ids)
        esterna.rollback()
    assert list(db.scalars(select(Utente).where(Utente.id.in_(ids)))) == []
