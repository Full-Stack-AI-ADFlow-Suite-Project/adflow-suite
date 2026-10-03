"""
Test per il worker (worker.py).
"""

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
