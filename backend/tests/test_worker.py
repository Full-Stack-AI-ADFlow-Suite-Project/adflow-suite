"""
Test per il worker (worker.py).
"""

import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import Mock, call

import pytest

import app.worker as worker


ORA = datetime(2026, 10, 2, tzinfo=timezone.utc)


@pytest.fixture
def servizio_finto(monkeypatch) -> Mock:
    """Il service di pubblicazione finto, con sessioni e ora fisse al posto di quelle vere.

    Ogni transazione apre una sessione `"db"` e registra `apre`/`chiude` in
    `servizio.mock_calls`, così i test vedono dove stanno i commit.
    """
    servizio = Mock()
    servizio.prepara_tentativi.return_value = [7]

    @contextmanager
    def transazione():
        servizio.apre()
        yield "db"
        servizio.chiude()

    monkeypatch.setattr(worker, "scadenze", servizio.scadenze)
    monkeypatch.setattr(worker, "transazione", transazione)
    monkeypatch.setattr(worker, "adesso", lambda: ORA)
    monkeypatch.setattr(worker, "servizio_pubblicazione", servizio)
    return servizio


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


def test_tick_pubblica_in_fasi_con_un_commit_prima_del_social(servizio_finto):
    """RL-025: `chiamata_il` è confermato (chiude) prima di chiamare il social."""
    worker.tick_pubblicazione(timestamp=0)

    assert servizio_finto.mock_calls == [
        call.apre(),
        call.scadenze("db", ORA),
        call.prepara_tentativi("db", ORA),
        call.chiude(),
        call.apre(),
        call.avvia_chiamata("db", 7, ORA),
        call.chiude(),
        call.chiama_social(servizio_finto.avvia_chiamata.return_value),
        call.apre(),
        call.registra_esito("db", 7, servizio_finto.chiama_social.return_value, ORA),
        call.chiude(),
        call.apre(),
        call.chiudi_campagne("db", ORA),
        call.chiude(),
    ]


def test_tick_senza_richiesta_non_chiama_il_social(servizio_finto):
    servizio_finto.avvia_chiamata.return_value = None

    worker.tick_pubblicazione(timestamp=0)

    servizio_finto.chiama_social.assert_not_called()
    servizio_finto.registra_esito.assert_not_called()
    servizio_finto.chiudi_campagne.assert_called_once()


def test_un_tentativo_rotto_non_ferma_gli_altri(servizio_finto):
    servizio_finto.prepara_tentativi.return_value = [7, 8]
    servizio_finto.avvia_chiamata.side_effect = [RuntimeError("rotto"), "richiesta"]

    worker.tick_pubblicazione(timestamp=0)

    servizio_finto.chiama_social.assert_called_once_with("richiesta")
    servizio_finto.registra_esito.assert_called_once()


def test_tick_accodato_ed_eseguito_dal_worker(coda, servizio_finto):
    """Il tick passa dalla coda come nel worker vero: accodato con `timestamp`, poi eseguito."""
    job_id = worker.tick_pubblicazione.defer(timestamp=1_790_000_000)

    worker.app.run_worker(
        wait=False, install_signal_handlers=False, listen_notify=False
    )

    assert coda.jobs[job_id]["status"] == "succeeded"
    servizio_finto.chiudi_campagne.assert_called_with("db", ORA)
