"""T1-13: creazione utenti e CLI reale su adflow_test."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app import cli
from app.core.errori import DatiNonValidi
from app.core.security import verifica_password
from app.moduli.accesso import service
from app.moduli.accesso.models import Utente
from tests.moduli.accesso.fabbrica import utente

PASSWORD = "PasswordPerCreazione!2026"


@pytest.mark.parametrize("ruolo", ["artigiano", "operatore", "admin"])
def test_crea_utente_con_ruolo_e_password_scrypt(db, client, ruolo):
    record = service.crea_utente(
        db, "  Persona@Example.test  ", PASSWORD, " Persona ", ruolo
    )
    assert record.id is not None
    assert record.email == "persona@example.test"
    assert record.nome == "Persona"
    assert record.ruolo == ruolo
    assert record.attivo
    assert record.password_hash.startswith("scrypt$")
    assert PASSWORD not in record.password_hash
    assert verifica_password(PASSWORD, record.password_hash)
    assert not verifica_password("sbagliata", record.password_hash)
    risposta = client.post(
        "/api/auth/login", json={"email": record.email, "password": PASSWORD}
    )
    assert risposta.status_code == 200
    assert client.get("/api/auth/me").json()["id"] == record.id


@pytest.mark.parametrize("email", ["persona@example.test", " PERSONA@EXAMPLE.TEST "])
def test_email_duplicata_non_modifica_utente_esistente(db, email):
    primo = service.crea_utente(db, "persona@example.test", PASSWORD, "Primo", "admin")
    with pytest.raises(DatiNonValidi, match="Email già registrata"):
        service.crea_utente(db, email, "altra", "Secondo", "artigiano")
    assert db.scalar(select(func.count()).select_from(Utente)) == 1
    assert primo.nome == "Primo"
    assert verifica_password(PASSWORD, primo.password_hash)


def test_email_precedente_con_maiuscole_non_si_duplica(db):
    utente(db, email="Persona@Example.test")
    with pytest.raises(DatiNonValidi, match="Email già registrata"):
        service.crea_utente(db, "persona@example.test", PASSWORD, "Persona", "admin")


@pytest.mark.parametrize(
    "campo,valore",
    [
        ("email", ""),
        ("email", "senza-chiocciola"),
        ("email", "persona@"),
        ("email", "persona@example"),
        ("email", "persona @example.test"),
        ("email", "persona@@example.test"),
        ("email", "x" * 321 + "@example.test"),
        ("nome", " "),
        ("password", ""),
        ("password", "x" * 1025),
        ("ruolo", "superadmin"),
        ("ruolo", "Admin"),
        ("ruolo", ""),
    ],
)
def test_dati_non_validi_non_inseriscono_utenti(db, campo, valore):
    dati = dict(
        email="persona@example.test", password=PASSWORD, nome="Persona", ruolo="admin"
    )
    dati[campo] = valore
    with pytest.raises(DatiNonValidi):
        service.crea_utente(db, **dati)
    assert db.scalar(select(func.count()).select_from(Utente)) == 0


def test_creazione_non_fa_commit(db):
    with db.begin_nested() as savepoint:
        record = service.crea_utente(
            db, "persona@example.test", PASSWORD, "Persona", "admin"
        )
        record_id = record.id
        savepoint.rollback()
    assert db.get(Utente, record_id) is None


def test_due_creazioni_concorrenti_stessa_email(motore_test, monkeypatch):
    email = f"{uuid4().hex}@example.test"
    barriera = Barrier(2)
    hash_reale = service.hash_password

    def hash_dopo_controllo(password):
        risultato = hash_reale(password)
        barriera.wait(timeout=15)
        return risultato

    monkeypatch.setattr(service, "hash_password", hash_dopo_controllo)

    def crea():
        with Session(motore_test) as sessione, sessione.begin():
            try:
                service.crea_utente(sessione, email, PASSWORD, "Persona", "admin")
                return "creato"
            except DatiNonValidi as errore:
                # Il savepoint ha evitato che il vincolo abortisca la transazione.
                assert sessione.scalar(text("select 1")) == 1
                return errore.messaggio

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            esiti = list(pool.map(lambda _: crea(), range(2)))
        assert sorted(esiti) == ["Email già registrata.", "creato"]
        with Session(motore_test) as sessione:
            assert (
                sessione.scalar(
                    select(func.count())
                    .select_from(Utente)
                    .where(Utente.email == email)
                )
                == 1
            )
    finally:
        with motore_test.begin() as connessione:
            connessione.execute(delete(Utente).where(Utente.email == email))


@pytest.fixture
def cli_reale_su_test(db, monkeypatch):
    @contextmanager
    def transazione_test():
        with db.begin_nested():
            yield db

    monkeypatch.setattr(cli, "transazione", transazione_test)
    monkeypatch.setattr(cli, "getpass", lambda _: PASSWORD)


def test_cli_crea_utente_con_service_reale(db, cli_reale_su_test, capsys):
    assert (
        cli.main(
            [
                "crea-utente",
                "--email",
                "CLI@Example.test",
                "--nome",
                "Persona",
                "--ruolo",
                "artigiano",
            ]
        )
        == 0
    )
    record = db.scalar(select(Utente).where(Utente.email == "cli@example.test"))
    assert record is not None
    assert verifica_password(PASSWORD, record.password_hash)
    uscita = capsys.readouterr()
    assert "artigiano: cli@example.test (creato)" in uscita.out
    assert PASSWORD not in uscita.out + uscita.err
    assert record.password_hash not in uscita.out + uscita.err


@pytest.mark.parametrize("ruolo", ["admin", "inesistente"])
def test_cli_restituisce_errore_di_dominio(db, cli_reale_su_test, capsys, ruolo):
    utente(db, email="persona@example.test")
    assert (
        cli.main(
            [
                "crea-utente",
                "--email",
                "persona@example.test",
                "--nome",
                "Persona",
                "--ruolo",
                ruolo,
            ]
        )
        == 1
    )
    uscita = capsys.readouterr()
    assert "già registrata" in uscita.err or "Ruolo non ammesso" in uscita.err
    assert PASSWORD not in uscita.out + uscita.err
    assert db.scalar(select(func.count()).select_from(Utente)) == 1
