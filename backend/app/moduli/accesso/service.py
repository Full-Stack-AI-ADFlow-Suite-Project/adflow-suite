"""Logica del modulo accesso: l'unica parte che gli altri moduli possono importare."""

from collections.abc import Callable
from datetime import datetime, timedelta
from functools import lru_cache
import re
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errori import DatiNonValidi, NonAutenticato, NonPermesso
from app.core.orologio import adesso
from app.core.security import genera_token, hash_password, hash_token, verifica_password

from .models import Sessione, Utente

DURATA_SESSIONE = timedelta(hours=8)
COOKIE_SESSIONE = "adflow_sessione"
RUOLI_AMMESSI = ("artigiano", "operatore", "admin")


@lru_cache
def _hash_fittizio() -> str:
    """Anche un'email sconosciuta richiede una verifica scrypt."""
    return hash_password(genera_token())


def login(
    db: Session,
    email: str,
    password: str,
    ora: datetime,
    token_precedente: str | None = None,
) -> tuple[Utente, str]:
    """Verifica le credenziali e crea una sessione; ruota il cookie precedente.

    Il token in chiaro torna solo al router. Non revoca le altre sessioni
    dell'utente (ad esempio su un altro dispositivo).
    """
    record = db.scalar(
        select(Utente).where(func.lower(Utente.email) == email.strip().lower())
    )
    password_valida = verifica_password(
        password, record.password_hash if record is not None else _hash_fittizio()
    )
    if record is None or not password_valida or not record.attivo:
        raise NonAutenticato("Email o password non corrette.")
    logout(db, token_precedente)
    token = genera_token()
    db.add(
        Sessione(
            token_hash=hash_token(token),
            utente_id=record.id,
            scade_il=ora + DURATA_SESSIONE,
        )
    )
    db.flush()
    return record, token


def logout(db: Session, token: str | None) -> None:
    """Revoca solo la sessione indicata; è idempotente anche senza cookie."""
    if token:
        db.execute(delete(Sessione).where(Sessione.token_hash == hash_token(token)))


def utente_della_sessione(db: Session, token: str | None, ora: datetime) -> Utente:
    """Legge l'utente solo con token valido, sessione non scaduta e account attivo."""
    if not token:
        raise NonAutenticato("Sessione non valida o scaduta.")
    record = db.scalar(
        select(Utente)
        .join(Sessione, Sessione.utente_id == Utente.id)
        .where(
            Sessione.token_hash == hash_token(token),
            Sessione.scade_il > ora,
            Utente.attivo.is_(True),
        )
    )
    if record is None:
        raise NonAutenticato("Sessione non valida o scaduta.")
    return record


def utente_corrente(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    ora: Annotated[datetime, Depends(adesso)],
) -> Utente:
    """Dipendenza FastAPI: restituisce l'utente autenticato dalla sessione.

    Si usa nei router con ``Depends``::

        def mio_endpoint(utente: Annotated[Utente, Depends(utente_corrente)]):
            ...

    I test possono sostituirla con la fixture ``utente_di_prova`` (T1-06).

    Returns:
        Il record utente corrispondente al cookie ``adflow_sessione``.

    Raises:
        NonAutenticato: se il cookie è assente, scaduto o non valido.
    """
    return utente_della_sessione(db, request.cookies.get(COOKIE_SESSIONE), ora)


def richiede_ruolo(*ruoli: str) -> Callable[..., Utente]:
    """Dipendenza FastAPI: verifica che l'utente abbia uno dei ruoli ammessi.

    Factory che restituisce una dipendenza costruita su ``utente_corrente``.
    Si usa nei router::

        @router.get("/riservato")
        def endpoint(
            utente: Annotated[Utente, Depends(richiede_ruolo("operatore", "admin"))]
        ):
            ...

    La factory funziona già: chi sostituisce ``utente_corrente`` (fixture
    ``utente_di_prova``) ottiene anche il controllo del ruolo.

    Args:
        *ruoli: uno o più ruoli ammessi (es. ``"operatore"``, ``"admin"``).

    Returns:
        Funzione dipendenza che restituisce l'utente se il ruolo è ammesso
        e solleva ``NonPermesso`` (403) altrimenti.
    """

    def controlla(utente: Annotated[Utente, Depends(utente_corrente)]) -> Utente:
        if utente.ruolo not in ruoli:
            raise NonPermesso("Non hai i permessi per questa operazione.")
        return utente

    return controlla


def crea_utente(
    db: Session,
    email: str,
    password: str,
    nome: str,
    ruolo: str,
) -> Utente:
    """Crea un nuovo utente con password protetta da un hash scrypt.

    Usata da ``cli.py`` per il comando ``crea-utente``. Il seed esistente
    continua a inserire direttamente gli utenti (corsia 0).
    Non espone mai la password in chiaro nei log o nelle eccezioni.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        email: indirizzo email univoco nel sistema.
        password: password in chiaro — viene trasformata in hash prima del salvataggio.
        nome: nome visualizzato dell'utente.
        ruolo: uno tra ``artigiano``, ``operatore``, ``admin``.

    Returns:
        Il record utente appena creato.

    Raises:
        DatiNonValidi: se l'email è già registrata o il ruolo non è ammesso.
    """
    email = email.strip().lower()
    nome = nome.strip()
    if len(email) > 320 or re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is None:
        raise DatiNonValidi("Indirizzo email non valido.")
    if ruolo not in RUOLI_AMMESSI:
        raise DatiNonValidi("Ruolo non ammesso.")
    if not nome:
        raise DatiNonValidi("Il nome non può essere vuoto.")
    if not password or len(password) > 1024:
        raise DatiNonValidi("La password deve contenere da 1 a 1024 caratteri.")
    if (
        db.scalar(select(Utente.id).where(func.lower(Utente.email) == email))
        is not None
    ):
        raise DatiNonValidi("Email già registrata.")
    record = Utente(
        email=email,
        nome=nome,
        ruolo=ruolo,
        password_hash=hash_password(password),
        attivo=True,
    )
    # Il vincolo DB risolve anche la gara tra due creazioni della stessa email.
    # Il savepoint mantiene utilizzabile la transazione del chiamante.
    try:
        with db.begin_nested():
            db.add(record)
            db.flush()
    except IntegrityError as errore:
        if (
            getattr(errore.orig, "sqlstate", None) == "23505"
            and getattr(getattr(errore.orig, "diag", None), "constraint_name", None)
            == "utente_email_key"
        ):
            raise DatiNonValidi("Email già registrata.") from None
        raise
    return record
