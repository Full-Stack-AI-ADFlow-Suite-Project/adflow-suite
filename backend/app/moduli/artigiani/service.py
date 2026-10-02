"""Logica del modulo artigiani: l'unica parte che gli altri moduli possono importare."""

from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db


def profilo_di(
    db: Annotated[Session, Depends(get_db)],
    utente_id: int,
) -> Any | None:
    """Restituisce il profilo della bottega dell'utente, o None se assente.

    Usata da ``campagne`` (verifica prima dell'invio) e da ``revisione``
    (visualizzazione dati artigiano). Restituire ``None`` — e non sollevare
    ``NonTrovato`` — permette al chiamante di distinguere tra utente senza
    profilo (onboarding in corso) e utente inesistente (errore diverso).

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        utente_id: chiave primaria dell'utente di cui si cerca il profilo.

    Returns:
        Il record ``ProfiloBottega`` se esiste, altrimenti ``None``.

    Raises:
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04
