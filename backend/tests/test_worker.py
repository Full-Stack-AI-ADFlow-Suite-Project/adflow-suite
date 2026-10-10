"""
Test per il worker (worker.py).
"""

import subprocess
import sys
from contextlib import nullcontext
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

import app.worker as worker


@pytest.fixture
def pubblica_dovuti_finta(monkeypatch) -> Mock:
    """`pubblica_dovuti` finta, con sessione e ora fisse al posto di quelle vere."""
    finta = Mock()
    monkeypatch.setattr(worker, "transazione", lambda: nullcontext("db"))
    monkeypatch.setattr(
        worker, "adesso", lambda: datetime(2026, 10, 2, tzinfo=timezone.utc)
    )
    monkeypatch.setattr(worker, "pubblica_dovuti", finta)
    return finta


def test_il_worker_carica_il_modello_intero():
    """In un processo nuovo, come il worker vero: nei test le tabelle ci sono già tutte.

    Senza una tabella a cui punta una chiave, il primo salvataggio di un job fallisce.
    """
    codice = (
        "import app.worker; from app.core.db import Base; "
        "caricate = set(Base.metadata.tables); import app.tabelle; "
        "mancanti = set(Base.metadata.tables) - caricate; "
        "assert not mancanti, sorted(mancanti)"
    )
    esito = subprocess.run([sys.executable, "-c", codice], capture_output=True)
    assert esito.returncode == 0, esito.stderr.decode(errors="replace")[-500:]


def test_tick_pubblicazione_registrato_ogni_minuto_senza_sovrapposizioni():
    periodic_task = worker.app.periodic_registry.periodic_tasks[
        ("tick_pubblicazione", "")
    ]

    assert periodic_task.cron == "* * * * *"
    assert periodic_task.configure_kwargs["lock"] == "tick_pubblicazione"
    assert periodic_task.configure_kwargs["queueing_lock"] == "tick_pubblicazione"


def test_tick_pubblicazione_invoca_pubblica_dovuti(pubblica_dovuti_finta):
    worker.tick_pubblicazione(timestamp=0)

    pubblica_dovuti_finta.assert_called_once_with(
        "db", datetime(2026, 10, 2, tzinfo=timezone.utc)
    )


def test_tick_accodato_ed_eseguito_dal_worker(coda, pubblica_dovuti_finta):
    """Il tick passa dalla coda come nel worker vero: accodato con `timestamp`, poi eseguito."""
    job_id = worker.tick_pubblicazione.defer(timestamp=1_790_000_000)

    worker.app.run_worker(
        wait=False, install_signal_handlers=False, listen_notify=False
    )

    assert coda.jobs[job_id]["status"] == "succeeded"
    pubblica_dovuti_finta.assert_called_with(
        "db", datetime(2026, 10, 2, tzinfo=timezone.utc)
    )
