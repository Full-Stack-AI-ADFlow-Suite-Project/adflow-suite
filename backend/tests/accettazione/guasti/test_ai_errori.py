"""Guasti dell'AI: i cinque tipi di errore (T4-105, §7.4, R-35).

Atteso: ogni guasto produce uno dei cinque tipi d'errore, **nessuna campagna
resta bloccata a metà** (né `inviata` né `in_generazione`), la chiamata si
registra nello storico AI anche se fallisce (R-50, CA-109).
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
from app.moduli.campagne.models import Campagna
from app.moduli.contenuti import jobs
from app.moduli.contenuti.models import ChiamataAI
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza, foto, gruppo

TIPI = ("temporaneo", "risposta", "configurazione", "richiesta", "rifiuto")
STATI_FINALI = {"in_revisione", "generazione_fallita"}


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


def _campagna_inviata(db: Session, utente) -> int:
    bottega = profilo(db, utente_id=utente.id)
    oggi = adesso().date()
    campagna = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        inizio=oggi + timedelta(days=4),
        fine=oggi + timedelta(days=17),
    )
    # una foto vera nel gruppo: senza foto la tappa di analisi non parte e
    # l'errore comandato non verrebbe mai chiamato
    mazzo = gruppo(db, campagna)
    foto(db, gruppo=mazzo)
    db.flush()
    campagne.invia_campagna(db, utente.id, campagna.id, adesso(), dichiarazione=True)
    return campagna.id


def _genera(campagna_id: int) -> None:
    for esecuzione in range(1, jobs.generazione.ESECUZIONI + 1):
        if not jobs.esegui_generazione(campagna_id, esecuzione):
            return


@pytest.mark.parametrize("tipo", TIPI)
def test_un_guasto_dell_ai_non_lascia_mai_la_campagna_a_meta(db, utente_di_prova, tipo):
    """Per ogni tipo d'errore la campagna arriva a uno stato finale (§7.4)."""
    artigiano = utente_di_prova("artigiano")
    campagna_id = _campagna_inviata(db, artigiano)
    finto = AIFinto()
    finto.comanda_errore("analizza_gruppo", tipo, volte=None)
    with usa_ai(finto), usa_archivio(ArchivioFinto()):
        _genera(campagna_id)
    campagna = db.get(Campagna, campagna_id)
    assert campagna.stato in STATI_FINALI, f"{tipo}: campagna in {campagna.stato}"


def test_un_errore_di_configurazione_ferma_subito(db, utente_di_prova):
    """R-35: `configurazione` porta a `generazione_fallita` alla prima esecuzione."""
    artigiano = utente_di_prova("artigiano")
    campagna_id = _campagna_inviata(db, artigiano)
    finto = AIFinto()
    finto.comanda_errore("analizza_gruppo", "configurazione", volte=None)
    with usa_ai(finto), usa_archivio(ArchivioFinto()):
        _genera(campagna_id)
    assert db.get(Campagna, campagna_id).stato == "generazione_fallita"


def test_la_chiamata_fallita_resta_nello_storico(db, utente_di_prova):
    """R-50: una chiamata che fallisce è comunque una riga di storico AI."""
    artigiano = utente_di_prova("artigiano")
    campagna_id = _campagna_inviata(db, artigiano)
    finto = AIFinto()
    finto.comanda_errore("analizza_gruppo", "temporaneo", volte=None)
    with usa_ai(finto), usa_archivio(ArchivioFinto()):
        _genera(campagna_id)
    righe = db.scalar(
        select(func.count())
        .select_from(ChiamataAI)
        .where(ChiamataAI.campagna_id == campagna_id)
    )
    assert righe >= 1, "nessuna chiamata registrata dopo un guasto dell'AI"
    esisti = set(
        db.scalars(
            select(ChiamataAI.esito).where(ChiamataAI.campagna_id == campagna_id)
        ).all()
    )
    assert esisti - {None, "ok"}, f"nessun esito d'errore registrato: {esisti}"
