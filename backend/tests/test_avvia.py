"""Prove di `avvia.py` (avvio unificato, log e registro degli avvii).

Nessun servizio vero: i processi sono piccoli `python -c` e le cartelle di log
stanno in `tmp_path`.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import io
import json
import os
from pathlib import Path
import re
import socket
import sys
import threading
import time
import types
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


def _carica_pubblica():
    spec = spec_from_file_location("pubblica", RADICE / "pubblica.py")
    assert spec is not None and spec.loader is not None
    modulo = module_from_spec(spec)
    sys.modules["pubblica"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


pubblica = _carica_pubblica()

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
        # Solo nel thread principale (il ciclo di main): i thread di appoggio e
        # `subprocess` usano il vero `time.sleep`, che qui non va toccato.
        if threading.current_thread() is threading.main_thread():
            raise KeyboardInterrupt

    # Un modulo `time` finto solo per `avvia`: patchare `time.sleep` per tutti
    # farebbe scattare Ctrl+C anche dentro `Popen.wait` (visto in CI su Linux).
    finto_time = types.SimpleNamespace(monotonic=time.monotonic, sleep=interrompi)
    monkeypatch.setattr(avvia, "time", finto_time)
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


def _prepara_pubblicazione(monkeypatch, tmp_path: Path, codice_uscita: int):
    """File di richiesta ed esito in tmp_path e un comando di pubblicazione finto.

    Il comando scrive in `ordine.txt` quanti avvii dell'API ha già visto: se
    vale 1, ha girato a servizi fermati e prima del riavvio.
    """
    avvii = tmp_path / "avvii.txt"
    ordine = tmp_path / "ordine.txt"
    log, registro = _prepara_main(
        monkeypatch,
        tmp_path,
        {
            "api": f"import time; open({str(avvii)!r}, 'a').write('x'); time.sleep(60)",
            "worker": "import time; time.sleep(60)",
        },
    )
    richiesta = tmp_path / "logs" / "pubblica.richiesta"
    esito = tmp_path / "logs" / "pubblica.esito"
    monkeypatch.setattr(avvia, "FILE_RICHIESTA_PUBBLICAZIONE", richiesta)
    monkeypatch.setattr(avvia, "FILE_ESITO_PUBBLICAZIONE", esito)
    comando = (
        "import pathlib; print('Pubblicati 2 post su 2.'); "
        f"pathlib.Path({str(ordine)!r}).write_text("
        f"str(len(pathlib.Path({str(avvii)!r}).read_text()))); "
        f"raise SystemExit({codice_uscita})"
    )
    monkeypatch.setattr(
        avvia,
        "_servizio_pubblicazione",
        lambda: avvia.Servizio("pubblica", [sys.executable, "-c", comando], tmp_path),
    )
    return registro, richiesta, esito, avvii, ordine


@pytest.mark.parametrize("codice_uscita", [0, 3])
def test_richiesta_di_pubblicazione_ferma_pubblica_e_riavvia(
    monkeypatch, tmp_path: Path, codice_uscita: int
):
    registro, richiesta, esito, avvii, ordine = _prepara_pubblicazione(
        monkeypatch, tmp_path, codice_uscita
    )
    fermati = threading.Event()

    def interrompi(_secondi):
        if threading.current_thread() is threading.main_thread():
            if fermati.is_set():
                raise KeyboardInterrupt
            time.sleep(0.05)

    monkeypatch.setattr(
        avvia, "time", types.SimpleNamespace(monotonic=time.monotonic, sleep=interrompi)
    )

    def attendi(condizione) -> bool:
        fine = time.monotonic() + 30
        while time.monotonic() < fine:
            if condizione():
                return True
            time.sleep(0.05)
        return False

    def pilota() -> None:
        # La richiesta arriva quando tutto è partito, come a mano.
        if attendi(lambda: registro.exists() and avvii.exists()):
            richiesta.parent.mkdir(exist_ok=True)
            richiesta.write_text("codice-di-prova")
            # Fine quando l'esito c'è e l'API è ripartita (secondo avvio).
            attendi(
                lambda: esito.exists()
                and avvii.exists()
                and len(avvii.read_text()) >= 2
            )
        fermati.set()

    threading.Thread(target=pilota, daemon=True).start()
    assert avvia.main() == 0

    risposta = json.loads(esito.read_text(encoding="utf-8"))
    assert risposta["codice_richiesta"] == "codice-di-prova"
    assert risposta["codice"] == codice_uscita
    assert risposta["riavviato"] is True
    assert "Pubblicati 2 post su 2." in risposta["righe"]
    assert not richiesta.exists()
    # La pubblicazione ha girato dopo il primo avvio e prima del secondo.
    assert ordine.read_text() == "1"
    assert avvii.read_text() == "xx"
    righe = registro.read_text(encoding="utf-8").splitlines()
    assert [r.split("|")[2].strip() for r in righe] == [
        "AVVIO",
        "PUBBLICAZIONE",
        "ARRESTO",
    ]
    # I processi del primo giro sono stati fermati davvero.
    primi = [int(n) for n in re.findall(r"=(\d+)", righe[0].split("figli=")[1])]
    assert primi and not any(avvia._processo_vivo(pid) for pid in primi)


def test_richiesta_rimasta_da_prima_non_pubblica_all_avvio(
    monkeypatch, tmp_path: Path, capsys
):
    _prepara_main(monkeypatch, tmp_path, {"corto": "raise SystemExit(0)"})
    richiesta = tmp_path / "logs" / "pubblica.richiesta"
    richiesta.parent.mkdir()
    richiesta.write_text("vecchia")
    marcatore = tmp_path / "pubblicato.txt"
    monkeypatch.setattr(avvia, "FILE_RICHIESTA_PUBBLICAZIONE", richiesta)
    monkeypatch.setattr(
        avvia,
        "_servizio_pubblicazione",
        lambda: avvia.Servizio(
            "pubblica",
            [sys.executable, "-c", f"open({str(marcatore)!r}, 'w')"],
            tmp_path,
        ),
    )

    assert avvia.main() == 1

    assert not richiesta.exists()
    assert not marcatore.exists()
    assert "Scarto una richiesta di pubblicazione" in capsys.readouterr().out


def test_comando_di_pubblicazione_e_solo_facebook():
    assert avvia._servizio_pubblicazione().comando[-3:] == [
        "pubblica-ora",
        "--canale",
        "facebook",
    ]


def test_pubblica_senza_avvia_pubblica_da_solo(monkeypatch):
    chiamate = []
    monkeypatch.setattr(pubblica, "avvia_in_esecuzione", lambda: False)
    monkeypatch.setattr(
        pubblica.subprocess,
        "run",
        lambda comando, cwd: chiamate.append((comando, cwd))
        or types.SimpleNamespace(returncode=0),
    )

    assert pubblica.main() == 0

    [(comando, cartella)] = chiamate
    assert comando[-3:] == ["pubblica-ora", "--canale", "facebook"]
    assert cartella == avvia.BACKEND


@pytest.mark.parametrize(
    ("codice", "riavviato", "atteso"), [(0, True, 0), (1, True, 1), (0, False, 1)]
)
def test_pubblica_con_avvia_scrive_la_richiesta_e_riporta_l_esito(
    monkeypatch, tmp_path: Path, capsys, codice: int, riavviato: bool, atteso: int
):
    richiesta = tmp_path / "pubblica.richiesta"
    esito = tmp_path / "pubblica.esito"
    monkeypatch.setattr(avvia, "FILE_RICHIESTA_PUBBLICAZIONE", richiesta)
    monkeypatch.setattr(avvia, "FILE_ESITO_PUBBLICAZIONE", esito)
    monkeypatch.setattr(pubblica, "avvia_in_esecuzione", lambda: True)

    def avvia_finto() -> None:
        for _ in range(200):
            if richiesta.exists():
                esito.write_text(
                    json.dumps(
                        {
                            "codice_richiesta": richiesta.read_text(),
                            "codice": codice,
                            "righe": ["Pubblicati 2 post su 2."],
                            "riavviato": riavviato,
                        }
                    ),
                    encoding="utf-8",
                )
                return
            time.sleep(0.05)

    threading.Thread(target=avvia_finto, daemon=True).start()

    assert pubblica.main() == atteso
    assert "Pubblicati 2 post su 2." in capsys.readouterr().out


def test_pubblica_rinuncia_se_avvia_si_ferma(monkeypatch, tmp_path: Path, capsys):
    richiesta = tmp_path / "pubblica.richiesta"
    monkeypatch.setattr(avvia, "FILE_RICHIESTA_PUBBLICAZIONE", richiesta)
    monkeypatch.setattr(avvia, "FILE_ESITO_PUBBLICAZIONE", tmp_path / "pubblica.esito")
    risposte = iter([True, False])
    monkeypatch.setattr(pubblica, "avvia_in_esecuzione", lambda: next(risposte))

    assert pubblica.main() == 1

    assert not richiesta.exists()
    assert "si è fermato prima di rispondere" in capsys.readouterr().err
