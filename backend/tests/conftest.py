from collections.abc import Callable, Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from procrastinate.testing import InMemoryConnector
from sqlalchemy import Engine, make_url, text
from sqlalchemy.orm import Session

from app.core import coda as modulo_coda
from app.core.config import leggi_impostazioni
from app.core.db import crea_motore, get_db
from app.main import app
from app.moduli.accesso.models import Utente
from app.moduli.accesso.service import utente_corrente
from tests.moduli.accesso.fabbrica import utente


@pytest.fixture(scope="session")
def motore_test() -> Iterator[Engine]:
    """adflow_test svuotato e portato all'ultima migrazione, una volta per esecuzione."""
    url = leggi_impostazioni().database_url_test
    nome = make_url(url).database or ""
    assert nome.endswith("_test"), f"DATABASE_URL_TEST punta a '{nome}': rifiuto."

    motore = crea_motore(url)
    with motore.begin() as connessione:
        connessione.execute(text("DROP SCHEMA public CASCADE"))
        connessione.execute(text("CREATE SCHEMA public"))

    alembic = Config("alembic.ini")
    alembic.attributes["url"] = url
    command.upgrade(alembic, "head")

    yield motore
    motore.dispose()


@pytest.fixture
def db(motore_test: Engine) -> Iterator[Session]:
    """Sessione su adflow_test: a fine test tutto viene annullato, anche dopo un commit."""
    with motore_test.connect() as connessione:
        esterna = connessione.begin()
        with Session(connessione, join_transaction_mode="create_savepoint") as sessione:
            yield sessione
        esterna.rollback()


@pytest.fixture(autouse=True)
def coda() -> Iterator[InMemoryConnector]:
    """Coda in memoria in ogni test: `accoda()` non tocca nessun database.

    I job accodati si leggono in `coda.jobs` (id → nome, argomenti, stato).
    """
    connettore = InMemoryConnector()
    with modulo_coda.app.replace_connector(connettore):
        yield connettore


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    """Client dell'API che usa la stessa sessione del test."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def utente_di_prova(db: Session, client: TestClient) -> Callable[..., Utente]:
    """Utente al posto di `utente_corrente` nei test delle API.

    `utente_di_prova("operatore")` crea l'utente con la fabbrica e lo rende
    l'utente autenticato delle richieste di `client`; vale anche per
    `richiede_ruolo()`. Richiamata, cambia l'utente autenticato.
    """

    def entra(ruolo: str = "artigiano", **campi) -> Utente:
        record = utente(db, ruolo, **campi)
        app.dependency_overrides[utente_corrente] = lambda: record
        return record

    return entra
