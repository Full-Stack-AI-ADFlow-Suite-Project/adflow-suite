"""Nomi dei job e funzione di accodamento (plan §4)."""

from typing import Any

import procrastinate

from app.core.config import leggi_impostazioni

app = procrastinate.App(
    connector=procrastinate.PsycopgConnector(dsn=leggi_impostazioni().database_url)
)

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
    """Accoda un job per nome senza importare il modulo destinatario."""
    if nome not in _NOMI_JOB:
        raise ValueError(f"Nome job non valido: {nome}")

    return app.configure_task(nome).defer(**kwargs).id
