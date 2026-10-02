"""Dati di prova del modulo accesso; nessun commit."""
from functools import lru_cache
from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.moduli.accesso.models import Utente

PASSWORD_DI_PROVA = "PasswordSoloTest!2026"


@lru_cache
def _hash_di_prova() -> str:
    # Calcolato una volta per esecuzione: scrypt è lento apposta.
    return hash_password(PASSWORD_DI_PROVA)


def utente(db: Session, ruolo: str = "artigiano", **campi) -> Utente:
    dati = dict(
        email=f"{uuid4().hex}@example.test",
        password_hash=_hash_di_prova(),
        nome="Utente di prova",
        ruolo=ruolo,
        attivo=True,
    )
    dati.update(campi)
    record = Utente(**dati)
    db.add(record)
    db.flush()
    return record
