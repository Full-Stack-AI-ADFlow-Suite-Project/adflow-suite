# Congelato per l'MVP, ADR-114: non estendere.
"""Job del modulo notifiche: chiamano service.py, senza logica di business."""

import logging

from procrastinate import JobContext, RetryStrategy

from app.core.coda import INVIA_NOTIFICA, app
from app.core.db import transazione
from app.core.orologio import adesso

from . import service

logger = logging.getLogger(__name__)

# Tre tentativi in tutto (plan §4): il primo più due riprove.
TENTATIVI = 3
ATTESA_SECONDI = 30


class InvioDaRiprovare(Exception):
    """Chiede a Procrastinate di rieseguire il job dopo l'attesa."""


def esegui_invio(notifica_id: int, contenuto: dict | None, tentativo: int) -> bool:
    """Un tentativo di ``invia_notifica``; vero se ne serve un altro.

    Al terzo fallimento la notifica diventa ``fallita`` e il job finisce:
    l'operatore la vede nel database e può gestirla a mano.
    """
    try:
        with transazione() as db:
            service.invia(db, notifica_id, contenuto, adesso())
        return False
    except Exception as errore:
        # Solo il tipo: il messaggio dell'eccezione può contenere dati
        # personali (es. l'indirizzo del destinatario) e non va nei log.
        logger.error(
            "invia_notifica %s, tentativo %s: %s",
            notifica_id,
            tentativo,
            type(errore).__name__,
        )
        if tentativo < TENTATIVI:
            return True
        try:
            with transazione() as db:
                service.segna_fallita(db, notifica_id)
        except Exception as secondo:
            logger.error(
                "invia_notifica %s: stato fallita non registrato (%s)",
                notifica_id,
                type(secondo).__name__,
            )
        return False


@app.task(
    name=INVIA_NOTIFICA,
    pass_context=True,
    # Una riprova in meno dei tentativi: la prima esecuzione non è un retry.
    retry=RetryStrategy(
        max_attempts=TENTATIVI - 1,
        wait=ATTESA_SECONDI,
        retry_exceptions=[InvioDaRiprovare],
    ),
)
def invia_notifica(
    context: JobContext, notifica_id: int, contenuto: dict | None = None
) -> None:
    """Manda l'email di una notifica, con 3 tentativi (plan §4).

    ``contenuto`` arriva dagli argomenti del job: lo prepara chi crea la
    notifica, perché ``notifiche`` non conosce campagne né post.
    """
    if esegui_invio(notifica_id, contenuto, context.job.attempts + 1):
        raise InvioDaRiprovare(f"Notifica {notifica_id}: serve un nuovo tentativo.")
