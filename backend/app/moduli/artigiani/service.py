"""Logica del modulo artigiani: l'unica parte che gli altri moduli possono importare."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AccountSocial, ProfiloBottega
from .domain import CANALI, POST_A_SETTIMANA
from .schemas import CanaleCollegato


def stato_canali(db: Session, utente_id: int) -> list[CanaleCollegato]:
    """Stato di ogni canale MVP del solo utente autenticato (T1-14, R-22)."""
    profilo = profilo_di(db, utente_id)
    collegati = set(canali_collegati(db, profilo.id)) if profilo else set()
    return [
        CanaleCollegato(canale=canale, collegato=canale in collegati)
        for canale in CANALI
    ]


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


def profilo(db: Session, profilo_id: int) -> ProfiloBottega | None:
    """Profilo della bottega con l'id indicato, o None se non esiste (plan §6).

    Usata da ``campagne`` per i dati della bottega di una campagna quando chi
    guarda non è il proprietario. Il record si legge, non si modifica.
    """
    return db.get(ProfiloBottega, profilo_id)


def post_a_settimana(frequenza: str | None) -> int:
    """Post alla settimana per canale di una frequenza (plan §2, spec R-05).

    Senza frequenza, o con un valore fuori da ``domain.FREQUENZE``, vale
    ``decidete_voi``.
    """
    return POST_A_SETTIMANA.get(frequenza or "", POST_A_SETTIMANA["decidete_voi"])


def canali_collegati(db: Session, profilo_id: int) -> list[str]:
    """Canali con account nello stato collegato, in ordine di piattaforma (R-22)."""
    return list(
        db.scalars(
            select(AccountSocial.piattaforma)
            .where(
                AccountSocial.profilo_id == profilo_id,
                AccountSocial.stato == "collegato",
            )
            .order_by(AccountSocial.piattaforma)
        )
    )
