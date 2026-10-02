"""Dati di prova del modulo accesso; nessun commit."""
from hashlib import scrypt
from secrets import token_hex
from uuid import uuid4
from sqlalchemy.orm import Session
from app.moduli.accesso.models import Utente


def utente(db: Session, ruolo: str = "artigiano", **campi) -> Utente:
    # Solo fabbrica di test: il formato definitivo del servizio arriva con T1-06.
    salt = token_hex(16)
    digest = scrypt(
        b"PasswordSoloTest!2026", salt=bytes.fromhex(salt), n=16384, r=8, p=1
    ).hex()
    dati = dict(
        email=f"{uuid4().hex}@example.test",
        password_hash=f"scrypt$16384$8$1${salt}${digest}",
        nome="Utente di prova",
        ruolo=ruolo,
        attivo=True,
    )
    dati.update(campi)
    record = Utente(**dati)
    db.add(record)
    db.flush()
    return record
