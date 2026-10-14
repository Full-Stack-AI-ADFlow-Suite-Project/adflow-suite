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

# Chi accoda salva alla fine della sua richiesta: un job partito prima troverebbe
# lo stato vecchio e non farebbe nulla. Per questo parte qualche secondo dopo.
ATTESA_PARTENZA_SECONDI = 3

# I nomi fanno parte del contratto tra i moduli (plan §4). Solo i job dell'MVP:
# ritocco, promemoria e metriche sono in roadmap (ADR-114).
GENERA_CAMPAGNA = "genera_campagna"
TICK_PUBBLICAZIONE = "tick_pubblicazione"
RIGENERA_POST = "rigenera_post"
INVIA_NOTIFICA = "invia_notifica"

_NOMI_JOB = {
    GENERA_CAMPAGNA,
    TICK_PUBBLICAZIONE,
    RIGENERA_POST,
    INVIA_NOTIFICA,
}


def accoda(nome: str, **kwargs: Any) -> int:
    """Accoda un job per nome senza importare il modulo destinatario.

    Restituisce l'id del job. Il worker lo prende dopo `ATTESA_PARTENZA_SECONDI`,
    quando chi l'ha accodato ha salvato.
    """
    if nome not in _NOMI_JOB:
        raise ValueError(f"Nome job non valido: {nome}")

    attesa = {"seconds": ATTESA_PARTENZA_SECONDI} if ATTESA_PARTENZA_SECONDI else None
    job = app.configure_task(nome, schedule_in=attesa)
    try:
        return job.defer(**kwargs)
    except procrastinate.exceptions.AppNotOpen:
        # Nell'API la coda si apre al primo job; nel worker è già aperta.
        with _apertura:
            app.open()
        return job.defer(**kwargs)
