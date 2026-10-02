from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import Session

from app.core.config import leggi_impostazioni
from app.core.db import get_db
from app.main import app


@pytest.fixture(scope="session")
def motore_test() -> Iterator[Engine]:
    """adflow_test svuotato e portato all'ultima migrazione, una volta per esecuzione."""
    url = leggi_impostazioni().database_url_test
    nome = make_url(url).database or ""
    assert nome.endswith("_test"), f"DATABASE_URL_TEST punta a '{nome}': rifiuto."

    motore = create_engine(url)
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


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    """Client dell'API che usa la stessa sessione del test."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
