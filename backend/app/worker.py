"""Worker Procrastinate: registra i job dei moduli e il tick di pubblicazione."""

from app.core.coda import TICK_PUBBLICAZIONE, app
from app.core.db import transazione
from app.core.orologio import adesso
from app.moduli.pubblicazione.service import pubblica_dovuti
from app.moduli.accesso import jobs as accesso
from app.moduli.artigiani import jobs as artigiani
from app.moduli.campagne import jobs as campagne
from app.moduli.contenuti import jobs as contenuti
from app.moduli.notifiche import jobs as notifiche
from app.moduli.pubblicazione import jobs as pubblicazione
from app.moduli.revisione import jobs as revisione

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
    """Esegue la pubblicazione dovuta ogni minuto, senza tick sovrapposti.

    `timestamp` è il minuto per cui Procrastinate ha accodato il tick.
    """
    with transazione() as db:
        pubblica_dovuti(db, adesso())
