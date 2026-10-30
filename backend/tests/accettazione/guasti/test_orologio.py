"""Orologio: cambio d'ora, fine anno, anno bisestile (T4-105, §7.4).

Scadenze e slot sono in Europe/Rome: la mezzanotte di Roma è 22:00 o 23:00 UTC
a seconda dell'ora legale. Il 28/03/2027 scatta l'ora legale (02:00 → 03:00):
la mezzanotte di Roma è ancora 23:00 UTC. Il 29/02/2028 è bisestile.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select

from app.moduli.campagne.models import Campagna
from app.moduli.revisione import service
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_inviata


def _campagna_senza_piano(db, utente, giorno: date) -> int:
    bottega = profilo(db, utente_id=utente.id)
    campagna = campagna_inviata(
        db,
        profilo_id=bottega.id,
        inizio=giorno,
        fine=giorno,
    )
    db.flush()
    return campagna.id


def _stato(db, campagna_id: int) -> str:
    return db.scalar(select(Campagna.stato).where(Campagna.id == campagna_id))


def test_la_scadenza_di_mezzanotte_roma_regge_il_cambio_d_ora(db, utente_di_prova):
    """Campagna che inizia il 28/03/2027 (ora legale): non scade alle 22:59 UTC."""
    artigiano = utente_di_prova("artigiano")
    campagna_id = _campagna_senza_piano(db, artigiano, date(2027, 3, 28))

    service.scadenze(db, datetime(2027, 3, 27, 22, 59, tzinfo=timezone.utc))
    assert _stato(db, campagna_id) != "scaduta", "scaduta un'ora troppo presto"

    service.scadenze(db, datetime(2027, 3, 27, 23, 0, tzinfo=timezone.utc))
    assert _stato(db, campagna_id) == "scaduta"


def test_la_scadenza_di_mezzanotte_roma_a_fine_anno(db, utente_di_prova):
    """Campagna che inizia il 01/01/2028: scade alle 23:00 UTC del 31/12."""
    artigiano = utente_di_prova("artigiano")
    campagna_id = _campagna_senza_piano(db, artigiano, date(2028, 1, 1))

    service.scadenze(db, datetime(2027, 12, 31, 22, 59, tzinfo=timezone.utc))
    assert _stato(db, campagna_id) != "scaduta"

    service.scadenze(db, datetime(2027, 12, 31, 23, 0, tzinfo=timezone.utc))
    assert _stato(db, campagna_id) == "scaduta"


def test_la_scadenza_di_mezzanotte_roma_nel_giorno_bisestile(db, utente_di_prova):
    """29/02/2028: la mezzanotte di Roma è 23:00 UTC del 28/02."""
    artigiano = utente_di_prova("artigiano")
    campagna_id = _campagna_senza_piano(db, artigiano, date(2028, 2, 29))

    service.scadenze(db, datetime(2028, 2, 28, 22, 59, tzinfo=timezone.utc))
    assert _stato(db, campagna_id) != "scaduta"

    service.scadenze(db, datetime(2028, 2, 28, 23, 0, tzinfo=timezone.utc))
    assert _stato(db, campagna_id) == "scaduta"
