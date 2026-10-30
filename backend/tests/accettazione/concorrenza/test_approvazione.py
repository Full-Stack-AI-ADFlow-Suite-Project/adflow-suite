"""Due operatori approvano la stessa campagna insieme (T4-103, R-03).

Atteso (§7.3 e R-14): la campagna passa una volta sola; la seconda richiesta
trova lo stato cambiato e riceve 409. Se passano entrambe, la campagna ha due
decisioni `approvata` e i post due approvazioni: R-03 è confermato.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.moduli.revisione import service
from tests.accettazione.concorrenza.conftest import crea_con_commit, esegui_in_parallelo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare

RIPETIZIONI = 50


def _campagna_pronta(motore, bottega) -> dict:
    def costruisci(sessione):
        campagna = campagna_in_revisione(sessione, profilo_id=bottega.id)
        post = [post_da_approvare(sessione, campagna_id=campagna.id) for _ in range(2)]
        return {"campagna": campagna.id, "post": [p.id for p in post]}

    return crea_con_commit(motore, costruisci)


@pytest.mark.xfail(
    strict=False,
    reason="RL-021 (R-03): due approvazioni in parallelo passano entrambe in "
    "49/50 ripetizioni; la campagna prende due decisioni `approvata` e i post "
    "due approvazioni. Correzione proposta: blocco della riga o UPDATE "
    "condizionale (WHERE stato = 'in_revisione')",
)
def test_due_operatori_approvano_insieme(motore_concorrenza, mondo_concorrenza):
    """50 volte, due operatori approvano insieme: mai due esiti positivi (R-03)."""
    doppie = 0
    errori_visti = {}
    for _ in range(RIPETIZIONI):
        mondo = _campagna_pronta(motore_concorrenza, mondo_concorrenza["bottega"])
        adesso = datetime.now(timezone.utc)
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: service.approva(
                    s, mondo["campagna"], mondo_concorrenza["operatore"], adesso
                ),
                lambda s: service.approva(
                    s, mondo["campagna"], mondo_concorrenza["operatore2"], adesso
                ),
            ],
        )
        if errori == [None, None]:
            doppie += 1
        else:
            for errore in errori:
                if errore is not None:
                    errori_visti[type(errore).__name__] = (
                        errori_visti.get(type(errore).__name__, 0) + 1
                    )
    assert doppie == 0, (
        f"approvazione doppia in {doppie}/{RIPETIZIONI} ripetizioni "
        f"(errori visti: {errori_visti}): R-03 confermato"
    )
