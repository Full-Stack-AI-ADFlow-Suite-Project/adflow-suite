"""CA-101: una campagna senza foto, 30 post per canale, tutti con l'immagine AI (R-28).

Il numero delle immagini AI non è una regola del piano: senza foto il piano ha
i post chiesti e ognuno ha il suo rimpiazzo `immagine_ai`, senza errori.
"""

from contextlib import contextmanager
from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.adapters.ai import AIFinto, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.orologio import adesso
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import jobs
from app.moduli.contenuti.models import ErroreGenerazione
from app.moduli.contenuti.service import post_della_campagna
from tests.moduli.artigiani.fabbrica import profilo

# 5 post a settimana (f5_piu) × 42 giorni ÷ 7 = 30 post per canale.
GIORNI = 42
POST_PER_CANALE = 30
PRIMO_GIORNO = 10


@pytest.fixture
def ai_archivio():
    """Il provider finto e l'archivio finto, come in sviluppo (nessuna rete)."""
    with usa_ai(AIFinto()) as finto, usa_archivio(ArchivioFinto()):
        yield finto


@pytest.fixture(autouse=True)
def transazioni_di_prova(db: Session, monkeypatch) -> None:
    """Il job apre le sue transazioni sulla sessione del test, all'ora vera."""

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


def _genera(campagna_id: int) -> None:
    for esecuzione in range(1, jobs.generazione.ESECUZIONI + 1):
        if not jobs.esegui_generazione(campagna_id, esecuzione):
            return
    raise AssertionError("Alla terza esecuzione il job chiede di ripartire.")


def test_ca101_campagna_senza_foto_trenta_post_per_canale_con_immagine_ai(
    client: TestClient, utente_di_prova, db: Session, ai_archivio
):
    """CA-101: 30 post per canale su Facebook e Instagram, 30 immagini AI, nessun errore."""
    artigiano = utente_di_prova("artigiano")
    profilo(
        db,
        utente_id=artigiano.id,
        canali=["facebook", "instagram"],
        frequenza="f5_piu",
    )
    inizio = adesso().date() + timedelta(days=PRIMO_GIORNO)
    fine = inizio + timedelta(days=GIORNI - 1)

    creata = client.post(
        "/api/campagne",
        json={
            "titolo": "Campagna senza foto",
            "inizio": inizio.isoformat(),
            "fine": fine.isoformat(),
            "descrizione": "Nessuna foto: solo immagini create dall'AI.",
            "canali": ["facebook", "instagram"],
        },
    )
    assert creata.status_code == 201, creata.text
    campagna_id = creata.json()["id"]

    inviata = client.post(
        f"/api/campagne/{campagna_id}/invia", json={"dichiarazione": True}
    )
    assert inviata.status_code == 200, inviata.text

    _genera(campagna_id)
    db.expire_all()

    campagna = campagne.campagna(db, campagna_id)
    assert campagna.stato == "in_revisione"
    assert (
        db.scalars(
            select(ErroreGenerazione).where(
                ErroreGenerazione.campagna_id == campagna_id
            )
        ).all()
        == []
    )

    post = post_della_campagna(db, campagna_id)
    for canale in ("facebook", "instagram"):
        suoi = [uno for uno in post if uno.canale == canale]
        assert len(suoi) == POST_PER_CANALE
        assert all(uno.riempitivo == "immagine_ai" for uno in suoi)
        assert all(uno.versione_corrente is not None for uno in suoi)
        assert all(len(uno.versione_corrente.legami_foto) == 1 for uno in suoi)

    # Un'uscita con lo stesso tema sui due canali usa la stessa immagine (R-28).
    immagini_ai = [
        una
        for una in campagne.foto_della_campagna(db, campagna_id)
        if una.origine == "creata_ai"
    ]
    assert len(immagini_ai) == POST_PER_CANALE
