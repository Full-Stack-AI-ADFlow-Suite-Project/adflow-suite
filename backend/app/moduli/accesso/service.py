"""Logica del modulo accesso: l'unica parte che gli altri moduli possono importare."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db


def utente_corrente() -> Any:
    """Dipendenza FastAPI: restituisce l'utente autenticato dalla sessione.

    Si usa nei router con ``Depends``::

        def mio_endpoint(utente: Annotated[Any, Depends(utente_corrente)]):
            ...

    Returns:
        Il record utente corrispondente al cookie ``adflow_sessione``.

    Raises:
        NonAutenticato: se il cookie è assente, scaduto o non valido.
        NotImplementedError: stub — implementazione in T1-12.
    """
    raise NotImplementedError  # T1-12


def richiede_ruolo(*ruoli: str) -> Callable[..., Any]:
    """Dipendenza FastAPI: verifica che l'utente abbia uno dei ruoli ammessi.

    Factory che restituisce una dipendenza. Si usa nei router::

        @router.get("/riservato")
        def endpoint(
            utente: Annotated[Any, Depends(richiede_ruolo("operatore", "admin"))]
        ):
            ...

    Args:
        *ruoli: uno o più ruoli ammessi (es. ``"operatore"``, ``"admin"``).
                Almeno un ruolo deve essere passato.

    Returns:
        Funzione dipendenza che restituisce l'utente se il ruolo è ammesso.

    Raises:
        NonPermesso: se l'utente autenticato non ha nessuno dei ruoli richiesti.
        NotImplementedError: stub — implementazione in T1-12.
    """
    raise NotImplementedError  # T1-12


def crea_utente(
    db: Annotated[Session, Depends(get_db)],
    email: str,
    password: str,
    nome: str,
    ruolo: str,
) -> Any:
    """Crea un nuovo utente con password cifrata con scrypt.

    Usata da ``cli.py`` per il comando ``crea-utente`` e dal seed.
    Non espone mai la password in chiaro nei log o nelle eccezioni.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        email: indirizzo email univoco nel sistema.
        password: password in chiaro — viene cifrata prima del salvataggio.
        nome: nome visualizzato dell'utente.
        ruolo: uno tra ``artigiano``, ``operatore``, ``admin``.

    Returns:
        Il record utente appena creato.

    Raises:
        DatiNonValidi: se l'email è già registrata o il ruolo non è ammesso.
        NotImplementedError: stub — implementazione in T1-13.
    """
    raise NotImplementedError  # T1-13
