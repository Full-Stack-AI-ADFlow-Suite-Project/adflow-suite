"""Logica del modulo accesso: l'unica parte che gli altri moduli possono importare."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.errori import NonPermesso

from .models import Utente


def utente_corrente() -> Utente:
    """Dipendenza FastAPI: restituisce l'utente autenticato dalla sessione.

    Si usa nei router con ``Depends``::

        def mio_endpoint(utente: Annotated[Utente, Depends(utente_corrente)]):
            ...

    Fino a T1-12 i test la sostituiscono con la fixture ``utente_di_prova``
    (T1-06).

    Returns:
        Il record utente corrispondente al cookie ``adflow_sessione``.

    Raises:
        NonAutenticato: se il cookie è assente, scaduto o non valido.
        NotImplementedError: stub — implementazione in T1-12.
    """
    raise NotImplementedError  # T1-12


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


def crea_utente(
    db: Session,
    email: str,
    password: str,
    nome: str,
    ruolo: str,
) -> Utente:
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


def cambia_password(db: Session, email: str, password: str) -> None:
    """Cambia la password con scrypt; contratto CLI, implementazione in T1-13.

    Solleva NonTrovato per un'email assente e DatiNonValidi per dati invalidi.
    Non registra password, non esegue commit.
    """
    raise NotImplementedError  # T1-13
