"""
Test per la coda dei job (core/coda.py).
"""

import asyncio
from collections.abc import Iterator
from contextlib import suppress

import procrastinate
import pytest
from sqlalchemy import Engine, text

from app.core import coda as modulo_coda
from app.core.coda import GENERA_CAMPAGNA, accoda, app, indirizzo_psycopg

JOB_DI_PROVA = "job_di_prova"
CODA_DI_PROVA = "prova"


@pytest.fixture
def coda_su_database(motore_test: Engine) -> Iterator[None]:
    """La coda vera su adflow_test: prova connessione e schema della migrazione 007."""
    url = motore_test.url.render_as_string(hide_password=False)
    connettore = procrastinate.PsycopgConnector(conninfo=indirizzo_psycopg(url))
    with app.replace_connector(connettore):
        yield
        # PsycopgConnector non ha un lato sincrono: il pool async si chiude
        # da solo all'uscita di open_async().
        with suppress(NotImplementedError):
            app.close()
    with motore_test.begin() as connessione:
        connessione.execute(text("TRUNCATE procrastinate_jobs CASCADE"))


@pytest.fixture
def job_di_prova(monkeypatch) -> Iterator[list[int]]:
    """Un job in più, su una coda sua e solo per il test: restituisce ciò che ha eseguito."""
    eseguiti: list[int] = []
    monkeypatch.setattr(
        modulo_coda, "_NOMI_JOB", modulo_coda._NOMI_JOB | {JOB_DI_PROVA}
    )
    # Senza job periodici: il worker di prova non accoda il tick.
    monkeypatch.setattr(app.periodic_registry, "periodic_tasks", {})

    @app.task(name=JOB_DI_PROVA, queue=CODA_DI_PROVA)
    def esegui(valore: int) -> None:
        eseguiti.append(valore)

    yield eseguiti
    del app.tasks[JOB_DI_PROVA]


async def _esegui_i_job_di_prova() -> None:
    """Worker sulla sola coda di prova: i job veri non girano mai dentro un test."""
    async with app.open_async():
        await app.run_worker_async(
            queues=[CODA_DI_PROVA],
            wait=False,
            install_signal_handlers=False,
            listen_notify=False,
        )


def test_accoda_scrive_nome_e_argomenti(coda):
    job_id = accoda(GENERA_CAMPAGNA, campagna_id=123)

    job = coda.jobs[job_id]
    assert job["task_name"] == "genera_campagna"
    assert job["args"] == {"campagna_id": 123}
    assert job["status"] == "todo"


def test_accoda_nome_non_valido(coda):
    """Test accoda con nome non valido genera ValueError."""
    with pytest.raises(ValueError, match="Nome job non valido"):
        accoda("job_inesistente", campagna_id=123)
    assert coda.jobs == {}


def test_job_di_prova_accodato_per_nome_ed_eseguito(
    coda_su_database, job_di_prova, motore_test
):
    job_id = accoda(JOB_DI_PROVA, valore=7)

    with motore_test.connect() as connessione:
        riga = connessione.execute(
            text("select task_name, status from procrastinate_jobs where id = :id"),
            {"id": job_id},
        ).one()
    assert tuple(riga) == (JOB_DI_PROVA, "todo")

    asyncio.run(_esegui_i_job_di_prova())

    assert job_di_prova == [7]
    with motore_test.connect() as connessione:
        stato = connessione.scalar(
            text("select status from procrastinate_jobs where id = :id"),
            {"id": job_id},
        )
    assert stato == "succeeded"


def test_indirizzo_psycopg_toglie_il_driver():
    assert (
        indirizzo_psycopg("postgresql+psycopg://utente:segreta@localhost:5432/adflow")
        == "postgresql://utente:segreta@localhost:5432/adflow"
    )


def test_nomi_job_costanti_definite():
    """Test che tutte le costanti JOB_* siano definite."""
    nomi_attesi = {
        "genera_campagna",
        "tick_pubblicazione",
        "rigenera_post",
        "invia_notifica",
        "ritocca_foto",
        "promemoria",
        "raccogli_metriche",
        "report_settimanale",
    }

    from app.core.coda import (
        JOB_GENERA_CAMPAGNA,
        JOB_TICK_PUBBLICAZIONE,
        JOB_RIGENERA_POST,
        JOB_INVIA_NOTIFICA,
        JOB_RITOCCA_FOTO,
        JOB_PROMEMORIA,
        JOB_RACCOGLI_METRICHE,
        JOB_REPORT_SETTIMANALE,
    )

    costanti = {
        JOB_GENERA_CAMPAGNA,
        JOB_TICK_PUBBLICAZIONE,
        JOB_RIGENERA_POST,
        JOB_INVIA_NOTIFICA,
        JOB_RITOCCA_FOTO,
        JOB_PROMEMORIA,
        JOB_RACCOGLI_METRICHE,
        JOB_REPORT_SETTIMANALE,
    }

    assert costanti == nomi_attesi
