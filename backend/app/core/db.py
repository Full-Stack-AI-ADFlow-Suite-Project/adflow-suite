"""Base dei modelli e sessioni del database."""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import leggi_impostazioni


class Base(DeclarativeBase):
    pass


@lru_cache
def motore() -> Engine:
    return create_engine(leggi_impostazioni().database_url)


@contextmanager
def transazione() -> Iterator[Session]:
    """Sessione per i job: commit alla fine, rollback se c'è un errore."""
    with Session(motore()) as db, db.begin():
        yield db


def get_db() -> Iterator[Session]:
    """Sessione per i router: una transazione per richiesta."""
    with transazione() as db:
        yield db
