"""Nomi dei job e funzione di accodamento (plan §4)."""

from threading import Lock
from typing import Any

import procrastinate
from sqlalchemy import make_url

from app.core.config import leggi_impostazioni


def indirizzo_psycopg(url: str) -> str:
    """L'indirizzo di `.env` senza il nome del driver: psycopg non accetta `+psycopg`."""
    return make_url(url).set(drivername="postgresql").render_as_string(False)


app = procrastinate.App(
    connector=procrastinate.PsycopgConnector(
        conninfo=indirizzo_psycopg(leggi_impostazioni().database_url)
    )
)
_apertura = Lock()

# I nomi fanno parte del contratto tra i moduli; manteniamo le costanti T1-02.
GENERA_CAMPAGNA = "genera_campagna"
TICK_PUBBLICAZIONE = "tick_pubblicazione"
RIGENERA_POST = "rigenera_post"
INVIA_NOTIFICA = "invia_notifica"
RITOCCA_FOTO = "ritocca_foto"
PROMEMORIA = "promemoria"
RACCOGLI_METRICHE = "raccogli_metriche"
REPORT_SETTIMANALE = "report_settimanale"

# Alias espliciti per i chiamanti che preferiscono la convenzione JOB_*.
JOB_GENERA_CAMPAGNA = GENERA_CAMPAGNA
JOB_TICK_PUBBLICAZIONE = TICK_PUBBLICAZIONE
JOB_RIGENERA_POST = RIGENERA_POST
JOB_INVIA_NOTIFICA = INVIA_NOTIFICA
JOB_RITOCCA_FOTO = RITOCCA_FOTO
JOB_PROMEMORIA = PROMEMORIA
JOB_RACCOGLI_METRICHE = RACCOGLI_METRICHE
JOB_REPORT_SETTIMANALE = REPORT_SETTIMANALE

_NOMI_JOB = {
    GENERA_CAMPAGNA,
    TICK_PUBBLICAZIONE,
    RIGENERA_POST,
    INVIA_NOTIFICA,
    RITOCCA_FOTO,
    PROMEMORIA,
    RACCOGLI_METRICHE,
    REPORT_SETTIMANALE,
}


def accoda(nome: str, **kwargs: Any) -> int:
    """Accoda un job per nome senza importare il modulo destinatario.

    Restituisce l'id del job. Il job parte quando lo prende il worker.
    """
    if nome not in _NOMI_JOB:
        raise ValueError(f"Nome job non valido: {nome}")

    job = app.configure_task(nome)
    try:
        return job.defer(**kwargs)
    except procrastinate.exceptions.AppNotOpen:
        # Nell'API la coda si apre al primo job; nel worker è già aperta.
        with _apertura:
            app.open()
        return job.defer(**kwargs)
