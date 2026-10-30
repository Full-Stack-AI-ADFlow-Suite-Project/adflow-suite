"""§1.10 — Il piano ha, per ogni canale, esattamente i post chiesti.

Attacco di §4.3: campagne con 0 foto, 1 foto, più foto che post: il numero
esatto di post per canale, quelli che le foto non coprono con un'immagine AI.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.ai import AIFinto, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.orologio import adesso
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import jobs
from app.moduli.contenuti.models import Post
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza

GIORNI = 14  # 2 post a settimana × 14 ÷ 7 = 4 post per canale


@pytest.fixture(autouse=True)
def transazioni_di_prova(db: Session, monkeypatch) -> None:
    """Il job di generazione apre le sue transazioni sulla sessione del test."""

    @contextmanager
    def transazione():
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise

    monkeypatch.setattr(jobs, "transazione", transazione)
    monkeypatch.setattr(jobs, "adesso", adesso)


def _bozza(db: Session, utente, canali, frequenza="f1_2", giorni=GIORNI):
    bottega = profilo(db, utente_id=utente.id, canali=canali, frequenza=frequenza)
    inizio = adesso().date() + timedelta(days=4)  # l'invio vuole almeno 3 giorni a Roma
    campagna = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        canali=canali,
        frequenza=frequenza,
        inizio=inizio,
        fine=inizio + timedelta(days=giorni - 1),
    )
    db.flush()
    return campagna


def _genera(campagna_id: int) -> None:
    for esecuzione in range(1, jobs.generazione.ESECUZIONI + 1):
        if not jobs.esegui_generazione(campagna_id, esecuzione):
            return
    raise AssertionError("alla terza esecuzione il job chiede di ripartire")


def _post_per_canale(db: Session, campagna_id: int) -> dict[str, int]:
    righe = db.execute(
        select(Post.canale, func.count())
        .where(Post.campagna_id == campagna_id)
        .group_by(Post.canale)
    ).all()
    return {canale: numero for canale, numero in righe}


@pytest.fixture
def ai_archivio():
    with usa_ai(AIFinto()), usa_archivio(ArchivioFinto()):
        yield


def test_senza_foto_ogni_canale_ha_i_suoi_post_con_immagine_ai(
    db, utente_di_prova, ai_archivio
):
    """Zero foto: i post chiesti per canale, tutti con un'immagine AI (R-28)."""
    artigiano = utente_di_prova("artigiano")
    campagna = _bozza(db, artigiano, canali=["facebook", "instagram"])
    campagne.invia_campagna(db, artigiano.id, campagna.id, adesso(), dichiarazione=True)
    _genera(campagna.id)

    post_per_canale = _post_per_canale(db, campagna.id)
    # f1_2 (2 post/settimana) × 14 giorni ÷ 7 = 4 post per canale
    assert post_per_canale == {"facebook": 4, "instagram": 4}
    con_immagine = db.scalar(
        select(func.count())
        .select_from(Post)
        .where(Post.campagna_id == campagna.id, Post.riempitivo == "immagine_ai")
    )
    assert con_immagine == 8, "senza foto tutti i post devono essere immagini AI"
