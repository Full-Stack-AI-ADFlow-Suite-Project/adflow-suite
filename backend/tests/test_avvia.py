"""Prove di `avvia.py` (avvio unificato, log e registro degli avvii).

Nessun servizio vero: i processi sono piccoli `python -c` e le cartelle di log
stanno in `tmp_path`.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import io
import os
from pathlib import Path
import socket
import sys
import threading
from unittest.mock import MagicMock

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

PID_INESISTENTE = 2**22 + 12345


def test_servizi_con_e_senza_web():
    assert [s.nome for s in avvia._servizi(con_web=True)] == ["api", "worker", "web"]
    assert [s.nome for s in avvia._servizi(con_web=False)] == ["api", "worker"]


def test_leggi_env_ignora_commenti_e_virgolette(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text('# commento\nA=1\nB="due"\n\nSENZA_UGUALE\nC = tre \n')
    assert avvia._leggi_env(env) == {"A": "1", "B": "due", "C": "tre"}
    assert avvia._leggi_env(tmp_path / "manca") == {}


def test_database_raggiungibile_e_non():
    with socket.socket() as ascolto:
        ascolto.bind(("127.0.0.1", 0))
        ascolto.listen(1)
        porta = ascolto.getsockname()[1]
        url = f"postgresql+psycopg://u:p@127.0.0.1:{porta}/adflow"
        assert avvia._database_raggiungibile({"DATABASE_URL": url}) is None
    # chiusa: nessuno ascolta più
    errore = avvia._database_raggiungibile({"DATABASE_URL": url})
    assert errore is not None and "PostgreSQL non risponde" in errore
    # URL assente: non si blocca
    assert avvia._database_raggiungibile({}) is None


def test_blocco_impedisce_secondo_avvio(tmp_path: Path):
    file_pid = tmp_path / "avvia.pid"
    assert avvia.prendi_blocco(file_pid) is None
    assert file_pid.read_text() == str(os.getpid())
    avvia.rilascia_blocco(file_pid)
    assert not file_pid.exists()

    # un PID vivo diverso dal mio (il processo padre) blocca
    file_pid.write_text(str(os.getppid()))
    if avvia._processo_vivo(os.getppid()):
        assert "già in esecuzione" in (avvia.prendi_blocco(file_pid) or "")
    # un PID morto è un blocco vecchio: si prende
    file_pid.write_text(str(PID_INESISTENTE))
    assert avvia.prendi_blocco(file_pid) is None
    assert file_pid.read_text() == str(os.getpid())


def test_rilascia_blocco_non_tocca_il_pid_di_un_altro(tmp_path: Path):
    file_pid = tmp_path / "avvia.pid"
    file_pid.write_text(str(PID_INESISTENTE))
    avvia.rilascia_blocco(file_pid)
    assert file_pid.exists()


def test_registro_avvio_e_arresto_sono_righe_accodate(tmp_path: Path):
    registro = tmp_path / "logs" / "registro.log"
    servizi = avvia._servizi(con_web=True)
    avvia.registra_avvio(registro, servizi, {"api": 11, "worker": 22, "web": 33})
    avvia.registra_arresto(registro, "Ctrl+C")
    righe = registro.read_text(encoding="utf-8").splitlines()
    assert len(righe) == 2
    campi = [c.strip() for c in righe[0].split("|")]
    assert campi[1] == str(os.getpid()) and campi[2] == "AVVIO"
    assert "api:8000" in campi[3] and "web:5173" in campi[3]
    assert "api=11" in campi[3]
    assert righe[1].split("|")[2].strip() == "ARRESTO"
    assert righe[1].endswith("Ctrl+C")


def test_motivo_con_a_capo_e_barre_resta_su_una_riga(tmp_path: Path):
    registro = tmp_path / "registro.log"
    avvia.registra_arresto(registro, "errore | riga1\nriga2")
    righe = registro.read_text(encoding="utf-8").splitlines()
    assert len(righe) == 1 and righe[0].count("|") == 3


def test_avvio_senza_arresto_si_chiude_come_interrotto(tmp_path: Path):
    registro = tmp_path / "registro.log"
    registro.write_text(
        f"2026-11-05 10:00:00 | {PID_INESISTENTE} | AVVIO | servizi=api\n"
        f"2026-11-05 10:05:00 | {PID_INESISTENTE + 1} | AVVIO | servizi=api\n"
        f"2026-11-05 10:06:00 | {PID_INESISTENTE + 1} | ARRESTO | Ctrl+C\n",
        encoding="utf-8",
    )
    assert avvia.chiudi_avvii_interrotti(registro) == [PID_INESISTENTE]
    ultima = registro.read_text(encoding="utf-8").splitlines()[-1]
    assert f"| {PID_INESISTENTE} | ARRESTO | interrotto senza chiusura" in ultima
    # secondo giro: niente da chiudere
    assert avvia.chiudi_avvii_interrotti(registro) == []


def test_avvio_ancora_vivo_non_viene_chiuso(tmp_path: Path):
    registro = tmp_path / "registro.log"
    registro.write_text(
        f"2026-11-05 10:00:00 | {os.getppid()} | AVVIO | servizi=api\n",
        encoding="utf-8",
    )
    if avvia._processo_vivo(os.getppid()):
        assert avvia.chiudi_avvii_interrotti(registro) == []


def test_inoltra_scrive_su_terminale_e_su_file_senza_colori(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    file_log = tmp_path / "logs" / "inoltro.log"
    logger = avvia.crea_logger(file_log)
    servizio = avvia.Servizio("api", ["x"], Path.cwd(), porta=8000)
    processo = MagicMock()
    processo.stdout = ["\x1b[32mINFO\x1b[0m partito\n", "seconda riga\n"]

    avvia._inoltra(servizio, processo, larghezza=6, logger=logger)
    avvia.chiudi_logger(logger)

    uscita = capsys.readouterr().out
    assert "[api   ]" in uscita and "seconda riga" in uscita
    su_file = file_log.read_text(encoding="utf-8")
    assert "[api   ] INFO partito" in su_file
    assert "\x1b" not in su_file


def test_log_ruota_e_scrittura_concorrente_non_perde_righe(tmp_path: Path):
    file_log = tmp_path / "concorrenza.log"
    logger = avvia.crea_logger(file_log)

    def scrivi(tid: int):
        for i in range(50):
            logger.info("t%s m%s", tid, i)

    thread = [threading.Thread(target=scrivi, args=(t,)) for t in range(8)]
    for t in thread:
        t.start()
    for t in thread:
        t.join()
    avvia.chiudi_logger(logger)
    assert len(file_log.read_text(encoding="utf-8").splitlines()) == 400
    assert avvia.crea_logger(None) is None


def test_stampa_sicura_ripiega_su_ascii():
    class Cp1252(io.StringIO):
        def write(self, s: str) -> int:
            if "✓" in s:
                raise UnicodeEncodeError("cp1252", s, 0, 1, "no")
            return super().write(s)

    flusso = Cp1252()
    avvia._stampa_sicura("pronta ✓", file=flusso)
    assert "pronta" in flusso.getvalue() and "✓" not in flusso.getvalue()


def test_banner_avvisa_se_l_orologio_e_spostato(tmp_path: Path):
    servizi = avvia._servizi(con_web=True)
    righe = avvia._righe_banner(servizi, {"OROLOGIO_GIORNI_AVANTI": "12"}, None, None)
    testo = "\n".join(righe)
    assert "http://localhost:8000/docs" in testo
    assert "http://localhost:5173" in testo
    assert "OROLOGIO_GIORNI_AVANTI=12" in testo
    senza = avvia._righe_banner(servizi, {"OROLOGIO_GIORNI_AVANTI": "0"}, None, None)
    assert "OROLOGIO_GIORNI_AVANTI" not in "\n".join(senza)


def _prepara_main(monkeypatch, tmp_path: Path, comandi: dict[str, str]):
    """Rimpiazza i servizi con processi `python -c` e porta i file in tmp_path."""
    servizi = [
        avvia.Servizio(nome, [sys.executable, "-u", "-c", codice], tmp_path)
        for nome, codice in comandi.items()
    ]
    monkeypatch.setattr(avvia, "_servizi", lambda con_web: servizi)
    monkeypatch.setattr(avvia, "_controlli", lambda s: [])
    monkeypatch.setattr(avvia, "FILE_PID", tmp_path / "logs" / "avvia.pid")
    monkeypatch.setattr(avvia, "_leggi_env", lambda *a, **k: {})
    log = tmp_path / "logs" / "app.log"
    registro = tmp_path / "logs" / "registro.log"
    monkeypatch.setattr(
        sys,
        "argv",
        ["avvia.py", "--log-file", str(log), "--registro-file", str(registro)],
    )
    return log, registro


def test_main_servizio_che_cade_ferma_tutto_e_lo_scrive(monkeypatch, tmp_path: Path):
    log, registro = _prepara_main(
        monkeypatch,
        tmp_path,
        {
            "lungo": "import time; print('vivo', flush=True); time.sleep(60)",
            "corto": "print('ciao dal corto'); raise SystemExit(3)",
        },
    )
    assert avvia.main() == 1

    righe = registro.read_text(encoding="utf-8").splitlines()
    assert [r.split("|")[2].strip() for r in righe] == ["AVVIO", "ARRESTO"]
    assert "corto si è fermato (codice 3)" in righe[1]
    testo_log = log.read_text(encoding="utf-8")
    assert "ciao dal corto" in testo_log
    assert "arresto: corto si è fermato" in testo_log
    assert not (tmp_path / "logs" / "avvia.pid").exists()


def test_main_ctrl_c_registra_arresto_regolare(monkeypatch, tmp_path: Path):
    log, registro = _prepara_main(
        monkeypatch, tmp_path, {"lungo": "import time; time.sleep(60)"}
    )

    def interrompi(_secondi):
        raise KeyboardInterrupt

    monkeypatch.setattr(avvia.time, "sleep", interrompi)
    assert avvia.main() == 0
    ultima = registro.read_text(encoding="utf-8").splitlines()[-1]
    assert "| ARRESTO | Ctrl+C" in ultima


def test_main_no_log_non_scrive_nulla(monkeypatch, tmp_path: Path):
    _prepara_main(monkeypatch, tmp_path, {"corto": "raise SystemExit(0)"})
    monkeypatch.setattr(sys, "argv", ["avvia.py", "--no-log"])
    assert avvia.main() == 1
    assert not (tmp_path / "logs").exists()


def test_main_rifiuta_secondo_avvia_vivo(monkeypatch, tmp_path: Path, capsys):
    if not avvia._processo_vivo(os.getppid()):
        pytest.skip("il processo padre non è verificabile")
    _prepara_main(monkeypatch, tmp_path, {"lungo": "import time; time.sleep(60)"})
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "avvia.pid").write_text(str(os.getppid()))
    assert avvia.main() == 1
    assert "già in esecuzione" in capsys.readouterr().err
