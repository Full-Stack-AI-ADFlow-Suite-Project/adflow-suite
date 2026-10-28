"""Job del modulo contenuti: chiamano service.py, senza logica di business."""

import logging
import traceback

from procrastinate import JobContext, RetryStrategy

from app.adapters.ai import ErroreAI
from app.core.coda import GENERA_CAMPAGNA, RIGENERA_IMMAGINE, RIGENERA_POST, app
from app.core.db import transazione
from app.core.errori import DatiNonValidi
from app.core.orologio import adesso

from . import generazione, interventi

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


def esegui_rigenerazione(
    post_id: int, testo_proposto: str | None, nota: str | None, esecuzione: int
) -> bool:
    """Una esecuzione di `rigenera_post`; vero se ne serve un'altra (R-31).

    Un errore lascia il post com'è. Alla terza esecuzione fallita, o subito se
    non ha senso riprovare (chiave del provider sbagliata, richiesta senza
    testo proposto), l'intervento si spegne senza contare il ciclo.
    """
    try:
        with transazione() as db:
            interventi.rigenera(db, post_id, testo_proposto, nota, adesso())
        return False
    except Exception as errore:
        # Solo il tipo e i punti del codice: il messaggio può contenere dati.
        logger.error(
            "rigenera_post %s, esecuzione %s: %s\n%s",
            post_id,
            esecuzione,
            type(errore).__name__,
            "".join(traceback.format_tb(errore.__traceback__)),
        )
        inutile = isinstance(errore, DatiNonValidi) or (
            isinstance(errore, ErroreAI) and errore.tipo == "configurazione"
        )
        if not inutile and esecuzione < generazione.ESECUZIONI:
            return True
        try:
            with transazione() as db:
                interventi.spegni_intervento(db, post_id)
            return False
        except Exception as secondo:
            # Neppure lo spegnimento si è salvato (il database non risponde): si riprova.
            logger.error(
                "rigenera_post %s: intervento non spento (%s)",
                post_id,
                type(secondo).__name__,
            )
            return True


@app.task(
    name=RIGENERA_POST,
    pass_context=True,
    # Come genera_campagna: 3 esecuzioni in tutto, a 30 secondi una dall'altra.
    retry=RetryStrategy(
        max_attempts=generazione.ESECUZIONI - 1,
        wait=generazione.ATTESA_SECONDI,
        retry_exceptions=[NuovaEsecuzione],
    ),
)
def rigenera_post(
    context: JobContext,
    post_id: int,
    testo_proposto: str | None = None,
    nota: str | None = None,
) -> None:
    """Rigenera il testo di un post, da zero o da un testo proposto (plan §4, R-31).

    ``testo_proposto`` e ``nota`` arrivano da ``POST /post/{id}/rigenera``
    attraverso gli argomenti del job: il post salva solo il tipo di intervento.
    """
    if esegui_rigenerazione(post_id, testo_proposto, nota, context.job.attempts + 1):
        raise NuovaEsecuzione(f"Post {post_id}: serve una nuova esecuzione.")


def esegui_rigenerazione_immagine(
    post_id: int,
    nota: str | None,
    riscrivi_testo: bool,
    nota_testo: str | None,
    esecuzione: int,
) -> bool:
    """Una esecuzione di `rigenera_immagine`; vero se ne serve un'altra (R-31, R-49).

    Un errore lascia i post com'è. Alla terza esecuzione fallita, o subito se
    non ha senso riprovare (chiave del provider sbagliata, dati non validi),
    l'intervento si spegne su tutti i post toccati senza creare versioni.
    """
    try:
        with transazione() as db:
            interventi.rigenera_immagine(
                db, post_id, nota, riscrivi_testo, nota_testo, adesso()
            )
        return False
    except Exception as errore:
        # Solo il tipo e i punti del codice: il messaggio può contenere dati.
        logger.error(
            "rigenera_immagine %s, esecuzione %s: %s\n%s",
            post_id,
            esecuzione,
            type(errore).__name__,
            "".join(traceback.format_tb(errore.__traceback__)),
        )
        inutile = isinstance(errore, DatiNonValidi) or (
            isinstance(errore, ErroreAI) and errore.tipo == "configurazione"
        )
        if not inutile and esecuzione < generazione.ESECUZIONI:
            return True
        try:
            with transazione() as db:
                interventi.spegni_rigenerazione_immagine(db, post_id)
            return False
        except Exception as secondo:
            # Neppure lo spegnimento si è salvato: si riprova.
            logger.error(
                "rigenera_immagine %s: intervento non spento (%s)",
                post_id,
                type(secondo).__name__,
            )
            return True


@app.task(
    name=RIGENERA_IMMAGINE,
    pass_context=True,
    # Come genera_campagna: 3 esecuzioni in tutto, a 30 secondi una dall'altra.
    retry=RetryStrategy(
        max_attempts=generazione.ESECUZIONI - 1,
        wait=generazione.ATTESA_SECONDI,
        retry_exceptions=[NuovaEsecuzione],
    ),
)
def rigenera_immagine(
    context: JobContext,
    post_id: int,
    nota: str | None = None,
    riscrivi_testo: bool = False,
    nota_testo: str | None = None,
) -> None:
    """Rigenera l'immagine AI di un post, con la nota (plan §4, R-49).

    ``nota``, ``riscrivi_testo`` e ``nota_testo`` arrivano da
    ``POST /post/{id}/rigenera-immagine`` attraverso gli argomenti del job: il
    post salva solo il tipo di intervento.
    """
    if esegui_rigenerazione_immagine(
        post_id, nota, riscrivi_testo, nota_testo, context.job.attempts + 1
    ):
        raise NuovaEsecuzione(f"Post {post_id}: serve una nuova esecuzione.")
