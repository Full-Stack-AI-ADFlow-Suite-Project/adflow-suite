"""Job del modulo contenuti: chiamano service.py, senza logica di business."""

import logging
import traceback

from procrastinate import JobContext, RetryStrategy

from app.core.coda import GENERA_CAMPAGNA, app
from app.core.db import transazione
from app.core.orologio import adesso

from . import generazione

logger = logging.getLogger(__name__)


class NuovaEsecuzione(Exception):
    """Chiede a Procrastinate di rieseguire il job dopo l'attesa."""


def esegui_generazione(campagna_id: int, esecuzione: int) -> bool:
    """Una esecuzione di `genera_campagna`; vero se ne serve un'altra.

    Ogni passo ha la sua transazione: ciò che è salvato resta (R-24). Se un
    passo fallisce, l'errore si registra in una transazione nuova (R-35).
    """
    try:
        for _ in range(generazione.MAX_PASSI):
            with transazione() as db:
                if not generazione.passo(db, campagna_id, adesso()):
                    return False
        raise RuntimeError("La generazione non arriva alla fine.")
    except Exception as errore:
        # Solo il tipo e i punti del codice: il messaggio può contenere dati.
        logger.error(
            "genera_campagna %s, esecuzione %s: %s\n%s",
            campagna_id,
            esecuzione,
            type(errore).__name__,
            "".join(traceback.format_tb(errore.__traceback__)),
        )
        try:
            with transazione() as db:
                return generazione.registra_errore(db, campagna_id, errore, esecuzione)
        except Exception as secondo:
            # Neppure l'errore si è salvato (il database non risponde): si riprova.
            logger.error(
                "genera_campagna %s: errore non registrato (%s)",
                campagna_id,
                type(secondo).__name__,
            )
            return True


@app.task(
    name=GENERA_CAMPAGNA,
    pass_context=True,
    # Quante volte rieseguire lo decide `registra_errore()`: qui c'è solo il
    # tetto, una esecuzione in meno perché la prima non è un nuovo tentativo.
    retry=RetryStrategy(
        max_attempts=generazione.ESECUZIONI - 1,
        wait=generazione.ATTESA_SECONDI,
        retry_exceptions=[NuovaEsecuzione],
    ),
)
def genera_campagna(context: JobContext, campagna_id: int) -> None:
    """Genera analisi, piano e testi della campagna, a tappe (plan §4)."""
    if esegui_generazione(campagna_id, context.job.attempts + 1):
        raise NuovaEsecuzione(f"Campagna {campagna_id}: serve una nuova esecuzione.")
