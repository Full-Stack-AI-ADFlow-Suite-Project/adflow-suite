"""Avvia API, worker e frontend con un solo comando, e li ferma insieme.

Dalla radice del repository:

    uv run python avvia.py                tutto: API, worker e frontend
    uv run python avvia.py --senza-web    solo API e worker
    uv run python avvia.py --no-log       nessuna scrittura in logs/

Per riavviare si preme Ctrl+C (ferma tutto) e si rilancia il comando: l'API si
ricarica da sola a ogni modifica, il worker no. Se una porta è già occupata o un
altro `avvia.py` è ancora vivo, il comando lo dice e non parte.

Log. Le righe di tutti i servizi vanno a terminale e, con data e ora e senza
colori, in `logs/app_runtime.log` (ruota a 5 MB, ne tiene 3). Ogni avvio e ogni
arresto è una riga di `logs/registro_avvii.log`, legata al PID di `avvia.py`:
un avvio rimasto senza arresto (processo ucciso, spegnimento) viene chiuso come
"interrotto" al giro successivo. La cartella `logs/` è in `.gitignore`.

Pubblicare dalla presentazione. Dopo aver generato e approvato una campagna,
`uv run python pubblica.py` (da un altro terminale) chiede a questo avvia.py di
fermare API, worker e frontend, far uscire subito sulla Pagina i post approvati
di Facebook (`app.cli pubblica-ora --canale facebook`, che vuole il worker
fermo) e rilanciare tutto. La richiesta passa da un file in `logs/`, che non
è in git; una richiesta rimasta lì da prima non viene mai eseguita.

Il worker esegue anche il tick di pubblicazione ogni minuto. Con
`OROLOGIO_GIORNI_AVANTI` in `backend/.env` API e worker leggono la stessa ora
spostata: dopo averlo cambiato basta riavviare con questo comando.

Usa solo la libreria standard.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

RADICE = Path(__file__).resolve().parent
BACKEND = RADICE / "backend"
FRONTEND = RADICE / "frontend"
CARTELLA_LOGS = RADICE / "logs"
FILE_LOG_RUNTIME = CARTELLA_LOGS / "app_runtime.log"
FILE_REGISTRO_AVVII = CARTELLA_LOGS / "registro_avvii.log"
FILE_PID = CARTELLA_LOGS / "avvia.pid"
FILE_RICHIESTA_PUBBLICAZIONE = CARTELLA_LOGS / "pubblica.richiesta"
FILE_ESITO_PUBBLICAZIONE = CARTELLA_LOGS / "pubblica.esito"
CANALE_PUBBLICAZIONE = "facebook"
WINDOWS = os.name == "nt"

SECONDI_ATTESA_API = 45
SECONDI_ATTESA_PORTE = 20
_COLORI_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_BLOCCO_REGISTRO = threading.Lock()


@dataclass
class Servizio:
    nome: str
    comando: list[str]
    cartella: Path
    porta: int | None = None  # da controllare prima di partire


def ora_corrente() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _stampa_sicura(messaggio: str, file=None) -> None:
    """Stampa; se la console non regge un carattere (cp1252) lo sostituisce con `?`."""
    destinazione = file if file is not None else sys.stdout
    try:
        print(messaggio, file=destinazione, flush=True)
    except UnicodeEncodeError:
        print(
            messaggio.encode("ascii", errors="replace").decode("ascii"),
            file=destinazione,
            flush=True,
        )


def _servizi(con_web: bool) -> list[Servizio]:
    servizi = [
        Servizio(
            "api",
            ["uv", "run", "uvicorn", "app.main:app", "--reload"],
            BACKEND,
            porta=8000,
        ),
        Servizio(
            "worker",
            [
                "uv",
                "run",
                "python",
                "-m",
                "procrastinate",
                "-a",
                "app.worker.app",
                "worker",
                "--concurrency",
                "1",
            ],
            BACKEND,
        ),
    ]
    if con_web:
        # Su Windows `npm` è `npm.cmd`: `which` trova quello giusto.
        npm = shutil.which("npm") or "npm"
        servizi.append(Servizio("web", [npm, "run", "dev"], FRONTEND, porta=5173))
    return servizi


def _servizio_pubblicazione() -> Servizio:
    """Il comando che fa uscire subito i post approvati di Facebook (a worker fermo)."""
    return Servizio(
        "pubblica",
        [
            "uv",
            "run",
            "python",
            "-m",
            "app.cli",
            "pubblica-ora",
            "--canale",
            CANALE_PUBBLICAZIONE,
        ],
        BACKEND,
    )


def _porta_occupata(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as presa:
        presa.settimeout(0.5)
        return presa.connect_ex(("127.0.0.1", porta)) == 0


# --- Lettura di backend/.env ------------------------------------------------


def _leggi_env(file_env: Path | None = None) -> dict[str, str]:
    """Le coppie CHIAVE=valore di backend/.env (senza commenti né virgolette)."""
    file_env = file_env or BACKEND / ".env"
    valori: dict[str, str] = {}
    try:
        righe = file_env.read_text(encoding="utf-8").splitlines()
    except OSError:
        return valori
    for riga in righe:
        riga = riga.strip()
        if not riga or riga.startswith("#") or "=" not in riga:
            continue
        chiave, _, valore = riga.partition("=")
        valori[chiave.strip()] = valore.strip().strip("'\"")
    return valori


def _database_raggiungibile(env: dict[str, str]) -> str | None:
    """Un messaggio d'errore se PostgreSQL non risponde; None se risponde o non si sa."""
    url = env.get("DATABASE_URL", "")
    parti = urlparse(url)
    if not parti.hostname:
        return None  # URL assente o in un formato che non so leggere: non blocco
    porta = parti.port or 5432
    try:
        with socket.create_connection((parti.hostname, porta), timeout=1.5):
            return None
    except OSError:
        return (
            f"PostgreSQL non risponde su {parti.hostname}:{porta}: "
            "avvialo prima (il database è quello di DATABASE_URL in backend/.env)."
        )


def _controlli(servizi: list[Servizio]) -> list[str]:
    """I motivi per cui non si può partire; elenco vuoto se è tutto a posto."""
    problemi = []
    if shutil.which("uv") is None:
        problemi.append("`uv` non è installato: serve per API e worker.")
    if not (BACKEND / ".env").exists():
        problemi.append(
            "Manca backend/.env: `uv run python allinea.py` lo crea da .env.example."
        )
    else:
        errore_db = _database_raggiungibile(_leggi_env())
        if errore_db:
            problemi.append(errore_db)
    if (
        any(s.nome == "web" for s in servizi)
        and not (FRONTEND / "node_modules").is_dir()
    ):
        problemi.append(
            "Mancano le dipendenze del frontend: `npm install` in frontend/."
        )
    for servizio in servizi:
        if servizio.porta and _porta_occupata(servizio.porta):
            problemi.append(
                f"La porta {servizio.porta} ({servizio.nome}) è già occupata: "
                "ferma l'avvio precedente (Ctrl+C nel suo terminale) e riprova."
            )
    return problemi


# --- Un solo avvia.py alla volta, e registro degli avvii --------------------


def _processo_vivo(pid: int) -> bool:
    if pid <= 0:
        return False
    if WINDOWS:
        esito = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True,
            text=True,
            check=False,
        )
        return f'"{pid}"' in esito.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _pid_scritto(file_pid: Path) -> int | None:
    try:
        return int(file_pid.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def prendi_blocco(file_pid: Path) -> str | None:
    """Scrive il PID di questo avvia.py. Se ne esiste uno vivo ritorna il motivo."""
    altro = _pid_scritto(file_pid)
    if altro is not None and altro != os.getpid() and _processo_vivo(altro):
        return (
            f"Un altro avvia.py è già in esecuzione (PID {altro}): "
            "fermalo con Ctrl+C nel suo terminale prima di rilanciare."
        )
    try:
        file_pid.parent.mkdir(parents=True, exist_ok=True)
        file_pid.write_text(str(os.getpid()), encoding="utf-8")
    except OSError as errore:
        _stampa_sicura(f"[avviso] Non scrivo {file_pid.name}: {errore}", sys.stderr)
    return None


def rilascia_blocco(file_pid: Path) -> None:
    if _pid_scritto(file_pid) == os.getpid():
        try:
            file_pid.unlink()
        except OSError:
            pass


def _riga_registro(pid: int, evento: str, dettaglio: str) -> str:
    dettaglio = dettaglio.replace("\n", " ").replace("|", "/")
    return f"{ora_corrente()} | {pid} | {evento} | {dettaglio}\n"


def _scrivi_registro(file_registro: Path, riga: str) -> None:
    """Accoda una riga al registro: nessuna riscrittura del file."""
    with _BLOCCO_REGISTRO:
        try:
            file_registro.parent.mkdir(parents=True, exist_ok=True)
            with open(file_registro, "a", encoding="utf-8") as f:
                f.write(riga)
        except OSError as errore:
            _stampa_sicura(
                f"[avviso] Non scrivo {file_registro.name}: {errore}", sys.stderr
            )


def chiudi_avvii_interrotti(file_registro: Path) -> list[int]:
    """Chiude come 'interrotto' gli AVVIO senza ARRESTO il cui processo non c'è più."""
    try:
        righe = file_registro.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    aperti: dict[int, bool] = {}
    for riga in righe:
        campi = [c.strip() for c in riga.split("|")]
        if len(campi) < 3 or not campi[1].isdigit():
            continue
        if campi[2] == "AVVIO":
            aperti[int(campi[1])] = True
        elif campi[2] == "ARRESTO":
            aperti.pop(int(campi[1]), None)
    chiusi = []
    for pid in aperti:
        if pid != os.getpid() and not _processo_vivo(pid):
            _scrivi_registro(
                file_registro,
                _riga_registro(pid, "ARRESTO", "interrotto senza chiusura"),
            )
            chiusi.append(pid)
    return chiusi


def registra_avvio(
    file_registro: Path, servizi: list[Servizio], pids: dict[str, int]
) -> None:
    porte = ", ".join(f"{s.nome}:{s.porta}" for s in servizi if s.porta)
    figli = ", ".join(f"{nome}={pid}" for nome, pid in pids.items())
    dettaglio = (
        f"servizi={','.join(s.nome for s in servizi)} porte={porte} figli={figli}"
    )
    _scrivi_registro(file_registro, _riga_registro(os.getpid(), "AVVIO", dettaglio))


def registra_arresto(file_registro: Path, motivo: str) -> None:
    _scrivi_registro(file_registro, _riga_registro(os.getpid(), "ARRESTO", motivo))


# --- Log dei servizi --------------------------------------------------------


def crea_logger(file_log: Path | None) -> logging.Logger | None:
    """Un logger con file a rotazione (5 MB x 3); None se il log su file è spento."""
    if file_log is None:
        return None
    logger = logging.getLogger(f"avvia.{file_log}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        try:
            file_log.parent.mkdir(parents=True, exist_ok=True)
            gestore = RotatingFileHandler(
                file_log, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
            )
        except OSError as errore:
            _stampa_sicura(f"[avviso] Non scrivo {file_log.name}: {errore}", sys.stderr)
            return None
        gestore.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(gestore)
    return logger


def chiudi_logger(logger: logging.Logger | None) -> None:
    if logger is None:
        return
    for gestore in list(logger.handlers):
        gestore.close()
        logger.removeHandler(gestore)


def _inoltra(
    servizio: Servizio,
    processo: subprocess.Popen,
    larghezza: int,
    logger: logging.Logger | None,
) -> None:
    """Riporta le righe del processo con il suo nome davanti, su terminale e su file."""
    prefisso = f"[{servizio.nome:<{larghezza}}]"
    for riga in processo.stdout:
        testo = riga.rstrip()
        _stampa_sicura(f"{prefisso} {testo}")
        if logger is not None:
            logger.info("%s %s", prefisso, _COLORI_ANSI.sub("", testo))


def _apri(servizio: Servizio) -> subprocess.Popen:
    return subprocess.Popen(
        servizio.comando,
        cwd=servizio.cartella,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"},
        # Un gruppo a parte: così si ferma anche ciò che il processo ha avviato
        # (uvicorn --reload e vite hanno processi figli).
        start_new_session=not WINDOWS,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0,
    )


def _lancia(
    servizio: Servizio, larghezza: int, logger: logging.Logger | None
) -> subprocess.Popen:
    processo = _apri(servizio)
    threading.Thread(
        target=_inoltra,
        args=(servizio, processo, larghezza, logger),
        daemon=True,
    ).start()
    return processo


def _ferma(processo: subprocess.Popen) -> None:
    if processo.poll() is not None:
        return
    if WINDOWS:
        subprocess.run(
            ["taskkill", "/PID", str(processo.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
        return
    try:
        os.killpg(processo.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        processo.wait(timeout=8)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(processo.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


# --- Pubblicazione dalla presentazione -------------------------------------


def _consuma_richiesta(file_richiesta: Path) -> str | None:
    """Il codice della richiesta di pubblicazione, che si cancella; None se non c'è."""
    try:
        codice = file_richiesta.read_text(encoding="utf-8").strip()
        file_richiesta.unlink()
    except OSError:
        return None
    return codice


def _attendi_porte_libere(servizi: list[Servizio], secondi: int) -> bool:
    """Aspetta che le porte dei servizi fermati si liberino, prima di rilanciarli."""
    fine = time.monotonic() + secondi
    while time.monotonic() < fine:
        if not any(s.porta and _porta_occupata(s.porta) for s in servizi):
            return True
        time.sleep(0.5)
    return False


def _esegui_e_inoltra(
    servizio: Servizio, larghezza: int, logger: logging.Logger | None
) -> tuple[int, list[str]]:
    """Esegue un comando fino in fondo, riporta le sue righe e torna codice e righe."""
    prefisso = f"[{servizio.nome:<{larghezza}}]"
    try:
        processo = _apri(servizio)
    except OSError as errore:
        riga = f"non riesco a lanciare il comando: {errore}"
        _stampa_sicura(f"{prefisso} {riga}", file=sys.stderr)
        return 127, [riga]
    righe: list[str] = []
    try:
        for riga in processo.stdout:
            testo = riga.rstrip()
            righe.append(testo)
            _stampa_sicura(f"{prefisso} {testo}")
            if logger is not None:
                logger.info("%s %s", prefisso, _COLORI_ANSI.sub("", testo))
        return processo.wait(), righe
    finally:
        _ferma(processo)


def _scrivi_esito(file_esito: Path, esito: dict) -> None:
    """Scrive l'esito in un colpo solo, perché `pubblica.py` non ne legga metà."""
    provvisorio = file_esito.with_name(file_esito.name + ".tmp")
    try:
        file_esito.parent.mkdir(parents=True, exist_ok=True)
        provvisorio.write_text(json.dumps(esito), encoding="utf-8")
        os.replace(provvisorio, file_esito)
    except OSError as errore:
        _stampa_sicura(f"[avviso] Non scrivo {file_esito.name}: {errore}", sys.stderr)


def pubblica_e_riavvia(
    avviati: list[tuple[Servizio, subprocess.Popen]],
    servizi: list[Servizio],
    larghezza: int,
    logger: logging.Logger | None,
    file_registro: Path | None,
    codice_richiesta: str,
) -> None:
    """Ferma tutto, pubblica su Facebook, rilancia tutto e scrive l'esito.

    Si riavvia sempre, anche se la pubblicazione fallisce: l'esito dice com'è
    andata. ``avviati`` si aggiorna sul posto, così l'arresto finale di
    ``main`` ferma i processi nuovi.
    """

    def dillo(messaggio: str) -> None:
        _stampa_sicura(f"[avvia] {messaggio}")
        if logger is not None:
            logger.info("[avvia] %s", messaggio)

    dillo("Richiesta di pubblicazione: fermo tutto.")
    for _, processo in reversed(avviati):
        _ferma(processo)
    if not _attendi_porte_libere(servizi, SECONDI_ATTESA_PORTE):
        dillo("Le porte non si liberano: provo lo stesso.")

    pubblicazione = _servizio_pubblicazione()
    dillo(f"Pubblico su {CANALE_PUBBLICAZIONE}: {' '.join(pubblicazione.comando)}")
    larghezza_comando = max(larghezza, len(pubblicazione.nome))
    codice, righe = _esegui_e_inoltra(pubblicazione, larghezza_comando, logger)
    esito = {
        "codice_richiesta": codice_richiesta,
        "codice": codice,
        "righe": righe[-20:],
        "riavviato": False,
    }
    try:
        dillo("Riavvio tutto.")
        avviati.clear()
        for servizio in servizi:
            avviati.append((servizio, _lancia(servizio, larghezza, logger)))
        esito["riavviato"] = True
        for servizio, processo in avviati:
            if servizio.nome == "api" and servizio.porta:
                _controlla_api_in_background(servizio, processo)
        if file_registro:
            figli = ", ".join(f"{s.nome}={p.pid}" for s, p in avviati)
            _scrivi_registro(
                file_registro,
                _riga_registro(
                    os.getpid(),
                    "PUBBLICAZIONE",
                    f"canale={CANALE_PUBBLICAZIONE} codice={codice} figli={figli}",
                ),
            )
    finally:
        _scrivi_esito(FILE_ESITO_PUBBLICAZIONE, esito)


# --- Messaggi di avvio ------------------------------------------------------


def _righe_banner(
    servizi: list[Servizio],
    env: dict[str, str],
    file_log: Path | None,
    file_registro: Path | None,
) -> list[str]:
    righe = []
    for servizio in servizi:
        if servizio.porta:
            righe.append(f"{servizio.nome}: http://localhost:{servizio.porta}")
    if any(s.nome == "api" and s.porta for s in servizi):
        porta_api = next(s.porta for s in servizi if s.nome == "api")
        righe.append(f"docs API: http://localhost:{porta_api}/docs")
    giorni = env.get("OROLOGIO_GIORNI_AVANTI", "0")
    if giorni not in ("", "0"):
        righe.append(
            f"ATTENZIONE: OROLOGIO_GIORNI_AVANTI={giorni}, "
            "API e worker leggono l'ora spostata."
        )
    if file_log:
        righe.append(f"log: {file_log}")
    if file_registro:
        righe.append(f"registro: {file_registro}")
    righe.append("Ctrl+C per fermare tutto.")
    return righe


def _attendi_api(porta: int, secondi: int, processo: subprocess.Popen) -> bool:
    """Aspetta che /api/health risponda; False se scade il tempo o l'API muore."""
    fine = time.monotonic() + secondi
    while time.monotonic() < fine:
        if processo.poll() is not None:
            return False
        try:
            with urlopen(f"http://127.0.0.1:{porta}/api/health", timeout=2) as r:
                if r.status == 200:
                    return True
        except (URLError, OSError):
            pass
        time.sleep(1)
    return False


def _controlla_api_in_background(servizio: Servizio, processo: subprocess.Popen):
    def verifica() -> None:
        if _attendi_api(servizio.porta, SECONDI_ATTESA_API, processo):
            _stampa_sicura(f"✓ API pronta su http://localhost:{servizio.porta}")
        elif processo.poll() is None:
            _stampa_sicura(
                f"! L'API non risponde dopo {SECONDI_ATTESA_API} s: "
                "guarda le righe [api] qui sopra.",
                file=sys.stderr,
            )

    threading.Thread(target=verifica, daemon=True).start()


def main() -> int:
    parser = argparse.ArgumentParser(description="Avvia API, worker e frontend.")
    parser.add_argument(
        "--senza-web", action="store_true", help="non avviare il frontend"
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="non scrivere in logs/ (né log né registro)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=FILE_LOG_RUNTIME,
        help=f"file del log (predefinito: {FILE_LOG_RUNTIME})",
    )
    parser.add_argument(
        "--registro-file",
        type=Path,
        default=FILE_REGISTRO_AVVII,
        help=f"file del registro (predefinito: {FILE_REGISTRO_AVVII})",
    )
    argomenti = parser.parse_args()

    servizi = _servizi(con_web=not argomenti.senza_web)
    problemi = _controlli(servizi)
    registrazione = not argomenti.no_log
    if registrazione:
        motivo_blocco = prendi_blocco(FILE_PID)
        if motivo_blocco:
            problemi.append(motivo_blocco)
    if problemi:
        for problema in problemi:
            _stampa_sicura(f"✗ {problema}", file=sys.stderr)
        if registrazione:
            rilascia_blocco(FILE_PID)
        return 1

    file_log = argomenti.log_file if registrazione else None
    file_registro = argomenti.registro_file if registrazione else None
    logger = crea_logger(file_log)
    if file_registro:
        for pid in chiudi_avvii_interrotti(file_registro):
            _stampa_sicura(
                f"[avviso] L'avvio con PID {pid} non era stato chiuso: "
                "lo segno come interrotto."
            )

    # Una richiesta rimasta da un'altra volta non deve pubblicare all'avvio.
    try:
        FILE_RICHIESTA_PUBBLICAZIONE.unlink()
        _stampa_sicura(
            "[avviso] Scarto una richiesta di pubblicazione rimasta da prima."
        )
    except OSError:
        pass

    larghezza = max(len(s.nome) for s in servizi)
    avviati: list[tuple[Servizio, subprocess.Popen]] = []
    motivo = "Ctrl+C"
    registrato = False
    try:
        for servizio in servizi:
            avviati.append((servizio, _lancia(servizio, larghezza, logger)))
        if file_registro:
            registra_avvio(file_registro, servizi, {s.nome: p.pid for s, p in avviati})
            registrato = True
        banner = _righe_banner(servizi, _leggi_env(), file_log, file_registro)
        for riga in banner:
            _stampa_sicura(riga)
            if logger is not None:
                logger.info("[avvia] %s", riga)
        for servizio, processo in avviati:
            if servizio.nome == "api" and servizio.porta:
                _controlla_api_in_background(servizio, processo)
        while True:
            richiesta = _consuma_richiesta(FILE_RICHIESTA_PUBBLICAZIONE)
            if richiesta is not None:
                pubblica_e_riavvia(
                    avviati, servizi, larghezza, logger, file_registro, richiesta
                )
            for servizio, processo in avviati:
                if processo.poll() is not None:
                    motivo = (
                        f"{servizio.nome} si è fermato (codice {processo.returncode})"
                    )
                    _stampa_sicura(
                        f"✗ {motivo}: fermo anche gli altri.", file=sys.stderr
                    )
                    return 1
            time.sleep(1)
    except KeyboardInterrupt:
        _stampa_sicura("\nFermo tutto…")
        return 0
    except Exception as errore:  # un errore dello script non deve lasciare figli vivi
        motivo = f"errore di avvia.py: {errore}"
        _stampa_sicura(f"✗ {motivo}", file=sys.stderr)
        return 1
    finally:
        for _, processo in reversed(avviati):
            _ferma(processo)
        if logger is not None:
            logger.info("[avvia] arresto: %s", motivo)
        if file_registro and registrato:
            registra_arresto(file_registro, motivo)
        chiudi_logger(logger)
        if registrazione:
            rilascia_blocco(FILE_PID)


if __name__ == "__main__":
    sys.exit(main())
