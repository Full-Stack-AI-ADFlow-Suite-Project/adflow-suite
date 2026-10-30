"""§1.9 — Nella stessa campagna una foto non esce due volte sullo stesso canale.

Attacco di §4.3: Cambia foto combinato con Sposta per far uscire due volte la
stessa foto sullo stesso canale. Il caso in sequenza (seriale) è qui; il caso
in parallelo è in `tests/accettazione/concorrenza/test_interventi.py` ed è il
rilievo RL-023 (confermato, 50/50).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.core.errori import DatiNonValidi
from app.moduli.campagne.models import Foto
from app.moduli.revisione import interventi
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare


def test_in_sequenza_la_stessa_foto_non_si_mette_su_due_post(db, utente_di_prova):
    """Due post instagram della stessa campagna: la foto del primo non va sul secondo."""
    artigiano = utente_di_prova("artigiano")
    operatore = utente_di_prova("operatore")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    primo = post_da_approvare(db, campagna_id=campagna.id)
    secondo = post_da_approvare(db, campagna_id=campagna.id)
    db.flush()
    libera = db.scalars(
        select(Foto.id).where(Foto.campagna_id == campagna.id, Foto.n_utilizzi == 0)
    ).first()
    assert libera is not None
    adesso = datetime.now(timezone.utc)

    interventi.cambia_foto(db, primo.id, libera, operatore, adesso)
    db.flush()

    with pytest.raises(DatiNonValidi):
        interventi.cambia_foto(db, secondo.id, libera, operatore, adesso)
