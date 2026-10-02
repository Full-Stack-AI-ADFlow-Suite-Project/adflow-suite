"""
Coda dei job con Procrastinate.

I nomi dei job sono definiti qui e vengono usati per accodare i job
senza dover importare i moduli che li implementano.
"""

import procrastinate
from app.core.config import settings

# Coda Procrastinate
app = procrastinate.App(
    connector=procrastinate.PsycopgConnector(dsn=settings.DATABASE_URL)
)

# Nomi dei job (plan §4)
JOB_GENERA_CAMPAGNA = "genera_campagna"
JOB_TICK_PUBBLICAZIONE = "tick_pubblicazione"
JOB_RIGENERA_POST = "rigenera_post"
JOB_INVIA_NOTIFICA = "invia_notifica"
JOB_RITOCCA_FOTO = "ritocca_foto"
JOB_PROMEMORIA = "promemoria"
JOB_RACCOGLI_METRICHE = "raccogli_metriche"
JOB_REPORT_SETTIMANALE = "report_settimanale"


def accoda(nome_job: str, **kwargs) -> str:
    """
    Accoda un job per nome.

    Args:
        nome_job: Nome del job (una delle costanti JOB_*)
        **kwargs: Argomenti del job

    Returns:
        ID del job accodato

    Raises:
        ValueError: Se il nome del job non è valido
    """
    job_names = {
        JOB_GENERA_CAMPAGNA,
        JOB_TICK_PUBBLICAZIONE,
        JOB_RIGENERA_POST,
        JOB_INVIA_NOTIFICA,
        JOB_RITOCCA_FOTO,
        JOB_PROMEMORIA,
        JOB_RACCOGLI_METRICHE,
        JOB_REPORT_SETTIMANALE,
    }

    if nome_job not in job_names:
        raise ValueError(f"Nome job non valido: {nome_job}")

    # Usiamo l'API di Procrastinate per accodare il job
    # Il job deve essere registrato con @app.task in worker.py
    job_info = app.configure_job(name=nome_job).defer(**kwargs)
    return job_info.id
