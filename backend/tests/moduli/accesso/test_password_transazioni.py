"""Cambio password con connessioni distinte e login concorrente."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Event
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import cli
from app.core import db as modulo_db
from app.core.security import verifica_password
from app.moduli.accesso import service
from app.moduli.accesso.models import Sessione, Utente

PASSWORD = "PasswordSoloTest!2026"
NUOVA = "NuovaPasswordSoloTest!2026"
ORA = datetime(2026, 10, 8, tzinfo=timezone.utc)


def pulisci(motore, email):
    with motore.begin() as connessione:
        ids = select(Utente.id).where(Utente.email == email)
        connessione.execute(delete(Sessione).where(Sessione.utente_id.in_(ids)))
        connessione.execute(delete(Utente).where(Utente.email == email))


def test_cambio_revoca_anche_login_in_corso(motore_test, monkeypatch):
    email = f"{uuid4().hex}@example.test"
    login_bloccato = Event()
    libera_login = Event()
    cambio_avviato = Event()
    verifica_reale = service.verifica_password

    def verifica_con_pausa(password, digest):
        risultato = verifica_reale(password, digest)
        login_bloccato.set()
        assert libera_login.wait(timeout=15)
        return risultato

    def login():
        with Session(motore_test) as db, db.begin():
            return service.login(db, email, PASSWORD, ORA)[1]

    def cambia():
        cambio_avviato.set()
        with Session(motore_test) as db, db.begin():
            service.cambia_password(db, email, NUOVA)

    try:
        with Session(motore_test) as db, db.begin():
            service.crea_utente(db, email, PASSWORD, "Persona", "artigiano")
        monkeypatch.setattr(service, "verifica_password", verifica_con_pausa)
        with ThreadPoolExecutor(max_workers=2) as pool:
            login_futuro = pool.submit(login)
            try:
                assert login_bloccato.wait(timeout=15)
                cambio_futuro = pool.submit(cambia)
                assert cambio_avviato.wait(timeout=15)
            finally:
                libera_login.set()
            token = login_futuro.result(timeout=20)
            cambio_futuro.result(timeout=20)
        with Session(motore_test) as db:
            assert (
                db.scalar(
                    select(Sessione.id).where(
                        Sessione.token_hash == service.hash_token(token)
                    )
                )
                is None
            )
            record = db.scalar(select(Utente).where(Utente.email == email))
            assert verifica_reale(NUOVA, record.password_hash)
            assert not verifica_reale(PASSWORD, record.password_hash)
    finally:
        libera_login.set()
        pulisci(motore_test, email)


def test_cli_creazione_e_cambio_commit_osservabili(motore_test, monkeypatch, capsys):
    email = f"{uuid4().hex}@example.test"
    monkeypatch.setattr(modulo_db, "motore", lambda: motore_test)
    try:
        monkeypatch.setattr(cli, "getpass", lambda _: PASSWORD)
        assert (
            cli.main(
                [
                    "crea-utente",
                    "--email",
                    email,
                    "--nome",
                    "Persona",
                    "--ruolo",
                    "operatore",
                ]
            )
            == 0
        )
        with Session(motore_test) as db, db.begin():
            assert verifica_password(
                PASSWORD,
                db.scalar(select(Utente.password_hash).where(Utente.email == email)),
            )
            service.login(db, email, PASSWORD, ORA)
        monkeypatch.setattr(cli, "getpass", lambda _: NUOVA)
        assert cli.main(["cambia-password", "--email", email]) == 0
        with Session(motore_test) as db:
            record = db.scalar(select(Utente).where(Utente.email == email))
            assert verifica_password(NUOVA, record.password_hash)
            assert (
                db.scalar(select(Sessione.id).where(Sessione.utente_id == record.id))
                is None
            )
        output = capsys.readouterr()
        assert PASSWORD not in output.out + output.err
        assert NUOVA not in output.out + output.err
    finally:
        pulisci(motore_test, email)
