"""Worker Procrastinate: registra i job dei moduli e il tick di pubblicazione."""

import logging

# Il modello intero: un job salva righe con chiavi verso tabelle di altri moduli.
from app import tabelle  # noqa: F401
from app.core.coda import TICK_PUBBLICAZIONE, app
from app.core.db import transazione
from app.core.orologio import adesso
from app.moduli.pubblicazione import service as servizio_pubblicazione
from app.moduli.revisione.service import scadenze
from app.moduli.accesso import jobs as accesso
from app.moduli.artigiani import jobs as artigiani
from app.moduli.campagne import jobs as campagne
from app.moduli.contenuti import jobs as contenuti
from app.moduli.notifiche import jobs as notifiche
from app.moduli.pubblicazione import jobs as pubblicazione
from app.moduli.revisione import jobs as revisione

logger = logging.getLogger(__name__)

# Ogni job si registra nel `jobs.py` del suo modulo con `@app.task(name=...)`:
# importarli qui basta perché il worker li conosca.
JOB_DEI_MODULI = (
    accesso,
    notifiche,
    artigiani,
    campagne,
    contenuti,
    revisione,
    pubblicazione,
)


@app.periodic(
    cron="* * * * *",
    lock=TICK_PUBBLICAZIONE,
    queueing_lock=TICK_PUBBLICAZIONE,
)
@app.task(name=TICK_PUBBLICAZIONE)
def tick_pubblicazione(timestamp: int) -> None:
    """Ogni minuto applica le scadenze e poi pubblica il dovuto, senza tick sovrapposti.

    Una transazione per fase (RL-025, ADR-121): il tentativo e `chiamata_il`
    sono confermati *prima* della chiamata al social, così un processo morto
    dopo la risposta di Meta non lascia un post da ripubblicare.

    `timestamp` è il minuto per cui Procrastinate ha accodato il tick.
    """
    ora = adesso()
    with transazione() as db:
        scadenze(db, ora)
        ids = servizio_pubblicazione.prepara_tentativi(db, ora)

    for tentativo_id in ids:
        try:
            with transazione() as db:
                richiesta = servizio_pubblicazione.avvia_chiamata(
                    db, tentativo_id, adesso()
                )
            if richiesta is None:
                continue
            esito = servizio_pubblicazione.chiama_social(richiesta)
            with transazione() as db:
                servizio_pubblicazione.registra_esito(db, tentativo_id, esito, adesso())
        except Exception:
            # Un tentativo rotto non ferma gli altri. Se `chiamata_il` è già
            # confermato, il tick dopo lo segnala `fallito` e non ripubblica.
            logger.exception("Pubblicazione del tentativo %s interrotta", tentativo_id)

    with transazione() as db:
        servizio_pubblicazione.chiudi_campagne(db, adesso())
