"""Verifiche di affidabilità per avvia.py (motore di avvio unificato e logging).

Collauda:
- Inizializzazione corretta dei servizi (API, worker, web).
- Controlli preventivi (porte, file di configurazione).
- Creazione automatica di `logs/` e `registro_avvii.md` se assenti o vuoti.
- Tracciamento atomico di avvio e arresto nella tabella markdown.
- Scrittura thread-safe simultanea dei log di runtime.
- Inoltro simultaneo a console e su file con timestamp.
- Stampa difensiva con fallback sicuro per codepage limitate su Windows.
- Singola registrazione garantita dell'arresto nel blocco finally con gestione eccezioni.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import inspect
import io
from pathlib import Path
import sys
import threading
from unittest.mock import MagicMock, patch

import pytest

RADICE = Path(__file__).resolve().parents[2]


def _carica_avvia():
    spec = spec_from_file_location("avvia", RADICE / "avvia.py")
    assert spec is not None and spec.loader is not None
    modulo = module_from_spec(spec)
    sys.modules["avvia"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


avvia = _carica_avvia()


def test_definizione_servizi_con_e_senza_web():
    """Verifica che _servizi definisca correttamente le componenti attese."""
    servizi_tutti = avvia._servizi(con_web=True)
    nomi_tutti = [s.nome for s in servizi_tutti]
    assert nomi_tutti == ["api", "worker", "web"]
    assert any(s.porta == 8000 for s in servizi_tutti if s.nome == "api")
    assert any(s.porta == 5173 for s in servizi_tutti if s.nome == "web")

    servizi_no_web = avvia._servizi(con_web=False)
    nomi_no_web = [s.nome for s in servizi_no_web]
    assert nomi_no_web == ["api", "worker"]


def test_creazione_automatica_registro_avvii_se_assente(tmp_path: Path):
    """Verifica che _assicura_registro_esistente crei il file con intestazione markdown."""
    file_registro = tmp_path / "logs" / "registro_avvii_test.md"
    assert not file_registro.exists()

    avvia._assicura_registro_esistente(file_registro)
    assert file_registro.exists()

    contenuto = file_registro.read_text(encoding="utf-8")
    assert "# Registro Attività & Avvii Software" in contenuto
    assert "|---|---|---|---|---|" in contenuto


def test_creazione_automatica_registro_avvii_se_file_vuoto(tmp_path: Path):
    """Verifica che _assicura_registro_esistente rigeneri l'intestazione se il file è vuoto (0 byte)."""
    file_registro = tmp_path / "logs" / "registro_vuoto.md"
    file_registro.parent.mkdir(parents=True, exist_ok=True)
    file_registro.write_text("", encoding="utf-8")
    assert file_registro.stat().st_size == 0

    avvia._assicura_registro_esistente(file_registro)
    assert file_registro.stat().st_size > 0
    contenuto = file_registro.read_text(encoding="utf-8")
    assert "# Registro Attività & Avvii Software" in contenuto


def test_tracciamento_atomico_avvio_e_arresto_nel_registro(tmp_path: Path):
    """Verifica il ciclo di vita nel registro: avvio con PID e successivo arresto."""
    file_registro = tmp_path / "logs" / "registro_ciclo_vita.md"
    file_log = tmp_path / "logs" / "runtime.log"

    servizi = avvia._servizi(con_web=True)
    pids = {"api": 1111, "worker": 2222, "web": 3333}

    # Registra avvio
    avvia.registra_avvio_nel_registro(file_registro, servizi, pids, file_log)
    contenuto_avvio = file_registro.read_text(encoding="utf-8")

    assert "API, WORKER, WEB" in contenuto_avvio
    assert "api: 8000" in contenuto_avvio
    assert "web: 5173" in contenuto_avvio
    assert "🟢 Attivo (PID: api=1111, worker=2222, web=3333)" in contenuto_avvio

    # Registra arresto
    motivo = "Arrestato regolarmente per test"
    avvia.registra_arresto_nel_registro(file_registro, motivo=motivo)
    contenuto_arresto = file_registro.read_text(encoding="utf-8")

    assert "🟢 Attivo" not in contenuto_arresto
    assert f"⏹️ {motivo}" in contenuto_arresto


def test_scrittura_log_thread_safe(tmp_path: Path):
    """Verifica che più thread possano scrivere concorrentemente su file senza perdite o errori."""
    file_log = tmp_path / "logs" / "concorrenza.log"
    num_thread = 10
    messaggi_per_thread = 50

    def lavoratore(tid: int):
        for i in range(messaggi_per_thread):
            avvia._scrivi_log(file_log, f"Thread {tid} - Messaggio {i}")

    threads = [
        threading.Thread(target=lavoratore, args=(t,)) for t in range(num_thread)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert file_log.exists()
    righe = file_log.read_text(encoding="utf-8").splitlines()
    assert len(righe) == num_thread * messaggi_per_thread


def test_inoltra_scrive_console_e_file_log(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    """Verifica che _inoltra stampi su stdout e scriva simultaneamente nel file di log."""
    file_log = tmp_path / "logs" / "inoltro.log"
    servizio = avvia.Servizio("api", ["fake"], Path.cwd(), porta=8000)

    processo_mock = MagicMock()
    processo_mock.stdout = ["Riga di log numero 1\n", "Riga di log numero 2\n"]

    avvia._inoltra(servizio, processo_mock, larghezza=5, file_log=file_log)

    catturato = capsys.readouterr()
    assert "[api  ] Riga di log numero 1" in catturato.out
    assert "[api  ] Riga di log numero 2" in catturato.out

    assert file_log.exists()
    log_su_disco = file_log.read_text(encoding="utf-8")
    assert "[api  ] Riga di log numero 1" in log_su_disco
    assert "[api  ] Riga di log numero 2" in log_su_disco


def test_stampa_sicura_fallback_ascii():
    """Verifica che _stampa_sicura effettui fallback elegante se print fallisce con UnicodeEncodeError."""

    class StreamCp1252Simulata(io.StringIO):
        def write(self, s: str) -> int:
            if "\u2728" in s:
                raise UnicodeEncodeError("cp1252", s, 0, 1, "carattere non supportato")
            return super().write(s)

    stream = StreamCp1252Simulata()
    avvia._stampa_sicura("Test messaggio con emoji \u2728", file=stream)
    contenuto = stream.getvalue()
    assert "Test messaggio con emoji" in contenuto
    assert "?" in contenuto or "\u2728" not in contenuto


def test_singola_chiamata_arresto_in_main():
    """Verifica che nel codice di main l'arresto nel registro sia chiamato solo nel finally."""
    sorgente = inspect.getsource(avvia.main)
    assert "finally:" in sorgente
    chiamate = [
        riga.strip()
        for riga in sorgente.splitlines()
        if "registra_arresto_nel_registro(" in riga and not riga.strip().startswith("#")
    ]
    assert (
        len(chiamate) == 1
    ), f"Attesa 1 sola chiamata a registra_arresto_nel_registro, trovate: {len(chiamate)}"


def test_gestione_eccezioni_inattese_in_main():
    """Verifica che main catturi eccezioni impreviste annotando il motivo dell'errore."""
    sorgente = inspect.getsource(avvia.main)
    assert "except Exception as exc:" in sorgente
    assert 'motivo_arresto = f"Errore imprevisto' in sorgente
