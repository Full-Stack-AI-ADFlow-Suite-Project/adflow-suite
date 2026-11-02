"""Voti sulla stessa chiamata AI da due operatori (T4-103, R-50).

Atteso: una riga per voto; un secondo voto non cancella il primo, nemmeno se
è della stessa persona (costituzione §1.2). Due voti in parallelo devono
lasciare due righe.
"""

from __future__ import annotations

from sqlalchemy import func, select

from app.moduli.contenuti import storico_ai
from app.moduli.contenuti.models import ValutazioneAI
from tests.accettazione.concorrenza.conftest import crea_con_commit, esegui_in_parallelo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import chiamata_ai

RIPETIZIONI = 50


def _chiamata(motore, bottega) -> int:
    def costruisci(sessione):
        campagna = campagna_in_revisione(sessione, profilo_id=bottega.id)
        return chiamata_ai(sessione, campagna).id

    return crea_con_commit(motore, costruisci)


def test_due_operatori_votano_insieme(motore_concorrenza, mondo_concorrenza):
    """50 volte: due voti in parallelo sulla stessa chiamata → due righe."""
    persi = 0
    for _ in range(RIPETIZIONI):
        chiamata_id = _chiamata(motore_concorrenza, mondo_concorrenza["bottega"])
        operatore = mondo_concorrenza["operatore"].id
        operatore2 = mondo_concorrenza["operatore2"].id
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: storico_ai.vota(s, chiamata_id, operatore, 4, "buono"),
                lambda s: storico_ai.vota(s, chiamata_id, operatore2, 2, "da rivedere"),
            ],
        )
        assert errori == [None, None], f"un voto è fallito: {errori}"
        voti = crea_con_commit(
            motore_concorrenza,
            lambda s: s.scalar(
                select(func.count())
                .select_from(ValutazioneAI)
                .where(ValutazioneAI.chiamata_ai_id == chiamata_id)
            ),
        )
        if voti != 2:
            persi += 1
    assert persi == 0, f"voti persi in {persi}/{RIPETIZIONI} ripetizioni (lost update)"


def test_lo_stesso_operatore_vota_due_volte_insieme(
    motore_concorrenza, mondo_concorrenza
):
    """Anche due voti della stessa persona restano entrambi (R-50, §1.2)."""
    for _ in range(RIPETIZIONI):
        chiamata_id = _chiamata(motore_concorrenza, mondo_concorrenza["bottega"])
        operatore = mondo_concorrenza["operatore"].id
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: storico_ai.vota(s, chiamata_id, operatore, 5, None),
                lambda s: storico_ai.vota(s, chiamata_id, operatore, 1, "ripensamento"),
            ],
        )
        assert errori == [None, None], f"un voto è fallito: {errori}"
        voti = crea_con_commit(
            motore_concorrenza,
            lambda s: s.scalar(
                select(func.count())
                .select_from(ValutazioneAI)
                .where(ValutazioneAI.chiamata_ai_id == chiamata_id)
            ),
        )
        assert voti == 2, f"attese 2 righe di voto, trovate {voti}"
