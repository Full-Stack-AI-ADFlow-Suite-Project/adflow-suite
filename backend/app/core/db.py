"""Base dei modelli e sessioni del database."""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import leggi_impostazioni


class Base(DeclarativeBase):
    pass


def crea_motore(url: str) -> Engine:
    """Motore con la sessione PostgreSQL in UTC: le date tornano in UTC su ogni macchina."""
    return create_engine(url, connect_args={"options": "-c timezone=UTC"})


@lru_cache
def motore() -> Engine:
    return crea_motore(leggi_impostazioni().database_url)


@contextmanager
def transazione() -> Iterator[Session]:
    """Sessione per i job: commit alla fine, rollback se c'è un errore."""
    with Session(motore()) as db, db.begin():
        yield db


def get_db() -> Iterator[Session]:
    """Sessione per i router: una transazione per richiesta."""
    with transazione() as db:
        yield db
