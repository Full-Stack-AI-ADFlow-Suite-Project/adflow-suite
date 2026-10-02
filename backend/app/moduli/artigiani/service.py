"""Logica del modulo artigiani: l'unica parte che gli altri moduli possono importare."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ProfiloBottega


def profilo_di(
    db: Session,
    utente_id: int,
) -> ProfiloBottega | None:
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
    """
    return db.scalar(
        select(ProfiloBottega).where(ProfiloBottega.utente_id == utente_id)
    )
