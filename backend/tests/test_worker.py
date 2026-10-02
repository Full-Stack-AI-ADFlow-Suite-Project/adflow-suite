"""
Test per il worker (worker.py).
"""

from contextlib import nullcontext
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

import app.worker as worker


def test_tick_pubblicazione_registrato_ogni_minuto_senza_sovrapposizioni():
    periodic_task = worker.app.periodic_registry.periodic_tasks[
        ("tick_pubblicazione", "")
    ]

    assert periodic_task.cron == "* * * * *"
    assert periodic_task.configure_kwargs["lock"] == "tick_pubblicazione"
    assert periodic_task.configure_kwargs["queueing_lock"] == "tick_pubblicazione"


@pytest.mark.asyncio
async def test_tick_pubblicazione_invoca_pubblica_dovuti(monkeypatch):
    db = object()
    istante = datetime(2026, 10, 2, tzinfo=timezone.utc)
    pubblica_dovuti = Mock()

    monkeypatch.setattr(worker, "transazione", lambda: nullcontext(db))
    monkeypatch.setattr(worker, "adesso", lambda: istante)
    monkeypatch.setattr(worker, "pubblica_dovuti", pubblica_dovuti)

    await worker.tick_pubblicazione()

    pubblica_dovuti.assert_called_once_with(db, istante)
