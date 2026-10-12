"""Notifiche di prova, senza commit."""
from sqlalchemy.orm import Session

from app.moduli.accesso.models import Utente
from app.moduli.campagne.models import Campagna
from app.moduli.notifiche.models import Notifica
from tests.moduli.accesso.fabbrica import utente as crea_utente
from tests.moduli.campagne.fabbrica import campagna_in_revisione


def notifica(
    db: Session,
    campagna: Campagna | None = None,
    utente: Utente | None = None,
    **campi,
) -> Notifica:
    """Una notifica ``campagna_pronta`` all'operatore, ancora da inviare."""
    if campagna is None:
        campagna = campagna_in_revisione(db)
    if utente is None:
        utente = crea_utente(db, "operatore")
    dati = dict(
        utente_id=utente.id,
        campagna_id=campagna.id,
        tipo="campagna_pronta",
    )
    dati.update(campi)
    record = Notifica(**dati)
    db.add(record)
    db.flush()
    return record
