"""L'invio della stessa campagna da due schede (T4-103).

Atteso: la campagna in bozza passa a `inviata` una volta sola; la seconda
richiesta trova lo stato cambiato e riceve 409. Se passano entrambe, la
generazione viene accodata due volte sulla stessa bozza.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.moduli.campagne import service
from tests.accettazione.concorrenza.conftest import crea_con_commit, esegui_in_parallelo
from tests.moduli.campagne.fabbrica import campagna_in_bozza

RIPETIZIONI = 50


def _bozza(motore, bottega) -> int:
    return crea_con_commit(
        motore,
        lambda sessione: campagna_in_bozza(sessione, profilo_id=bottega.id).id,
    )


def test_due_invii_insieme_della_stessa_bozza(motore_concorrenza, mondo_concorrenza):
    """50 volte: due invii in parallelo, mai due esiti positivi."""
    doppie = 0
    errori_visti = {}
    for _ in range(RIPETIZIONI):
        campagna_id = _bozza(motore_concorrenza, mondo_concorrenza["bottega"])
        adesso = datetime.now(timezone.utc)
        utente_id = mondo_concorrenza["artigiano"].id
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: service.invia_campagna(
                    s, utente_id, campagna_id, adesso, dichiarazione=True
                ),
                lambda s: service.invia_campagna(
                    s, utente_id, campagna_id, adesso, dichiarazione=True
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
        f"due invii passano entrambi in {doppie}/{RIPETIZIONI} ripetizioni "
        f"(errori visti: {errori_visti}): la generazione parte due volte"
    )
