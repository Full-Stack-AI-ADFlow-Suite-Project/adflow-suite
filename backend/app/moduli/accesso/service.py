"""Logica del modulo accesso: l'unica parte che gli altri moduli possono importare."""

from collections.abc import Callable
from datetime import datetime, timedelta
from functools import lru_cache
import re
from typing import Annotated

from fastapi import Depends, Request, Response
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import leggi_impostazioni
from app.core.db import get_db
from app.core.orologio import adesso
from app.core.errori import DatiNonValidi, NonAutenticato, NonPermesso, NonTrovato
from app.core.security import genera_token, hash_password, hash_token, verifica_password

from .models import Sessione, Utente


COOKIE_SESSIONE = "adflow_sessione"


def durata_sessione(ruolo: str) -> timedelta:
    """Durata per ruolo configurata in T1-09; nessun ruolo sconosciuto."""
    impostazioni = leggi_impostazioni()
    if ruolo == "artigiano":
        return timedelta(days=impostazioni.sessione_artigiano_giorni)
    if ruolo in ("operatore", "admin"):
        return timedelta(hours=impostazioni.sessione_operatore_ore)
    raise NonAutenticato("Sessione non valida o scaduta.")


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
    candidati = list(
        db.scalars(
            select(Utente)
            .where(func.lower(Utente.email) == email.strip().lower())
            .limit(2)
            .with_for_update()
        )
    )
    # Il vincolo storico distingue maiuscole/minuscole: in presenza di due
    # identità equivalenti non scegliamo arbitrariamente quella con più privilegi.
    record = candidati[0] if len(candidati) == 1 else None
    password_valida = verifica_password(
        password, record.password_hash if record is not None else _hash_fittizio()
    )
    if (
        record is None
        or not password_valida
        or not record.attivo
        or record.ruolo not in ("artigiano", "operatore", "admin")
    ):
        raise NonAutenticato("Email o password non corrette.")
    logout(db, token_precedente)
    token = genera_token()
    db.add(
        Sessione(
            token_hash=hash_token(token),
            utente_id=record.id,
            scade_il=ora + durata_sessione(record.ruolo),
        )
    )
    db.flush()
    return record, token


def logout(db: Session, token: str | None) -> None:
    """Revoca solo la sessione indicata; è idempotente anche senza cookie."""
    if token:
        db.execute(delete(Sessione).where(Sessione.token_hash == hash_token(token)))


def utente_della_sessione(db: Session, token: str | None, ora: datetime) -> Utente:
    """Verifica account e sessione e rinnova atomicamente la scadenza (R-29).

    Il rinnovo condizionale non ricrea una sessione revocata o scaduta.
    La transazione resta del chiamante; nessun commit nel service.
    """
    if not token:
        raise NonAutenticato("Sessione non valida o scaduta.")
    digest = hash_token(token)
    record = db.scalar(
        select(Utente)
        .join(Sessione, Sessione.utente_id == Utente.id)
        .where(
            Sessione.token_hash == digest,
            Sessione.scade_il > ora,
            Utente.attivo.is_(True),
            Utente.ruolo.in_(("artigiano", "operatore", "admin")),
        )
        .execution_options(populate_existing=True)
    )
    if record is None:
        raise NonAutenticato("Sessione non valida o scaduta.")
    rinnovata = db.scalar(
        update(Sessione)
        .where(
            Sessione.token_hash == digest,
            Sessione.utente_id == record.id,
            Sessione.scade_il > ora,
            Sessione.utente_id.in_(
                select(Utente.id).where(
                    Utente.attivo.is_(True), Utente.ruolo == record.ruolo
                )
            ),
        )
        .values(scade_il=ora + durata_sessione(record.ruolo))
        .returning(Sessione.id)
    )
    if rinnovata is None:
        raise NonAutenticato("Sessione non valida o scaduta.")
    return record


def utente_corrente(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    ora: Annotated[datetime, Depends(adesso)],
) -> Utente:
    """Dipendenza reale: valida la sessione e rinnova anche il cookie browser."""
    token = request.cookies.get(COOKIE_SESSIONE)
    record = utente_della_sessione(db, token, ora)
    response.set_cookie(
        COOKIE_SESSIONE,
        token,
        max_age=int(durata_sessione(record.ruolo).total_seconds()),
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return record


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
        if utente.ruolo not in ruoli and not (
            utente.ruolo == "admin" and "operatore" in ruoli
        ):
            raise NonPermesso("Non hai i permessi per questa operazione.")
        return utente

    return controlla


RUOLI_AMMESSI = ("artigiano", "operatore", "admin")


def _testo_valido(testo: str, *, campo_postgres: bool = False) -> bool:
    if campo_postgres and "\x00" in testo:
        return False
    try:
        testo.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _normalizza_email(email: str) -> str:
    email = email.strip().lower()
    if (
        not _testo_valido(email, campo_postgres=True)
        or len(email) > 320
        or re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is None
    ):
        raise DatiNonValidi("Indirizzo email non valido.")
    return email


def _valida_password(password: str) -> None:
    if not _testo_valido(password) or not password or len(password) > 1024:
        raise DatiNonValidi("La password deve contenere da 1 a 1024 caratteri.")


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
    email = _normalizza_email(email)
    nome = nome.strip()
    if not _testo_valido(email, campo_postgres=True):
        raise DatiNonValidi("Indirizzo email non valido.")
    if not _testo_valido(nome, campo_postgres=True):
        raise DatiNonValidi("Nome non valido.")
    if not _testo_valido(password):
        raise DatiNonValidi("Password non valida.")
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
    # begin_nested fa flush anche sotto no_autoflush: gli errori dei record
    # già pendenti devono propagarsi fuori dalla gestione del nuovo utente.
    db.flush()
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


def cambia_password(db: Session, email: str, password: str) -> None:
    """Cambia l'hash scrypt e revoca tutte le sessioni, senza commit.

    Il blocco sull'utente coordina questa operazione con il login di T1-11.
    Un'identità legacy ambigua non viene selezionata arbitrariamente.
    """
    email = _normalizza_email(email)
    _valida_password(password)
    nuovo_hash = hash_password(password)
    candidati = list(
        db.scalars(
            select(Utente)
            .where(func.lower(Utente.email) == email)
            .limit(2)
            .with_for_update()
        )
    )
    if not candidati:
        raise NonTrovato("Utente non trovato.")
    if len(candidati) != 1:
        raise DatiNonValidi("Identità utente ambigua.")
    record = candidati[0]
    record.password_hash = nuovo_hash
    record.deve_cambiare_password = False
    db.execute(delete(Sessione).where(Sessione.utente_id == record.id))
    db.flush()
