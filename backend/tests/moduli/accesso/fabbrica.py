"""Dati di prova del modulo accesso; nessun commit."""
from functools import lru_cache
from hashlib import scrypt
from uuid import uuid4
from sqlalchemy.orm import Session
from app.moduli.accesso.models import Utente

PASSWORD_DI_PROVA = "PasswordSoloTest!2026"


@lru_cache
def _hash_di_prova() -> str:
    # Solo fabbrica di test: il formato definitivo del servizio arriva con T1-06.
    # Calcolato una volta per esecuzione: scrypt è lento apposta.
    salt = "00" * 16
    digest = scrypt(
        PASSWORD_DI_PROVA.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1
    ).hex()
    return f"scrypt$16384$8$1${salt}${digest}"


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
