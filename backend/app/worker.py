"""Worker Procrastinate: registra i job e pubblica i post dovuti."""

from app.core.coda import (
    GENERA_CAMPAGNA,
    INVIA_NOTIFICA,
    PROMEMORIA,
    RACCOGLI_METRICHE,
    REPORT_SETTIMANALE,
    RIGENERA_POST,
    RITOCCA_FOTO,
    TICK_PUBBLICAZIONE,
    app,
)
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

JOB_DEI_MODULI = (
    accesso,
    notifiche,
    artigiani,
    campagne,
    contenuti,
    revisione,
    pubblicazione,
)


@app.task(name=GENERA_CAMPAGNA)
async def genera_campagna(campagna_id: int) -> None:
    """Stub registrato fino all'implementazione del job T1-34."""


@app.periodic(
    cron="* * * * *",
    lock=TICK_PUBBLICAZIONE,
    queueing_lock=TICK_PUBBLICAZIONE,
)
@app.task(name=TICK_PUBBLICAZIONE)
async def tick_pubblicazione() -> None:
    """Esegue la pubblicazione dovuta ogni minuto, senza tick sovrapposti."""
    with transazione() as db:
        pubblica_dovuti(db, adesso())


@app.task(name=RIGENERA_POST)
async def rigenera_post(post_id: int) -> None:
    """Stub registrato fino all'implementazione del job di rigenerazione."""


@app.task(name=INVIA_NOTIFICA)
async def invia_notifica(notifica_id: int) -> None:
    """Stub registrato fino all'implementazione del job di notifica."""


@app.task(name=RITOCCA_FOTO)
async def ritocca_foto(post_id: int) -> None:
    """Stub registrato fino all'implementazione del job di ritocco."""


@app.task(name=PROMEMORIA)
async def promemoria() -> None:
    """Stub registrato fino all'implementazione del job di promemoria."""


@app.task(name=RACCOGLI_METRICHE)
async def raccogli_metriche() -> None:
    """Stub registrato fino all'implementazione del job metriche."""


@app.task(name=REPORT_SETTIMANALE)
async def report_settimanale() -> None:
    """Stub registrato fino all'implementazione del job report."""
