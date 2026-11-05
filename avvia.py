"""Avvia API, worker e frontend con un solo comando, con logging unificato e tracciamento.

Dalla radice del repository:

    uv run python avvia.py                tutto: API, worker e frontend (con log e registro)
    uv run python avvia.py --senza-web    solo API e worker
    uv run python avvia.py --no-log       avvio senza scrittura su file di log o registro

Per riavviare si preme Ctrl+C (ferma tutto) e si rilancia il comando: l'API si
ricarica da sola a ogni modifica, il worker no. Se una porta è già occupata (un
avvio precedente ancora vivo) il comando lo segnala e non parte.

I log continui di tutti i servizi attivi vengono inoltrati a terminale e salvati
simultaneamente in `logs/app_runtime.log`. Gli eventi di avvio e arresto vengono
registrati nella tabella di `logs/registro_avvii.md`. Entrambi i file sono protetti
da `.gitignore`.

Il worker esegue anche il tick di pubblicazione ogni minuto. Con
`OROLOGIO_GIORNI_AVANTI` in `backend/.env` API e worker leggono la stessa ora
spostata: dopo averlo cambiato basta riavviare con questo comando.

Usa solo la libreria standard di Python.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time

RADICE = Path(__file__).resolve().parent
BACKEND = RADICE / "backend"
FRONTEND = RADICE / "frontend"
CARTELLA_LOGS = RADICE / "logs"
FILE_LOG_RUNTIME = CARTELLA_LOGS / "app_runtime.log"
FILE_REGISTRO_AVVII = CARTELLA_LOGS / "registro_avvii.md"

WINDOWS = os.name == "nt"
_BLOCCO_SCRITTURA = threading.Lock()

INTESTAZIONE_REGISTRO = (
    "# Registro Attività & Avvii Software (AdFlow Suite)\n\n"
    "> **USO PRIVATO**: Questo file si trova nella cartella `logs/` protetta da `.gitignore`.\n"
    "> Traccia in tempo reale gli avvii e gli arresti dell'intero stack applicativo (API, Worker, Frontend).\n\n"
    "---\n\n"
    "## 🚀 1. Registro degli Avvii del Software (Analisi Dinamica)\n\n"
    "| Data e Ora | Servizi / Componenti | Modalità / Porte | "
    "Esito Iniziale | Errori / Note di Runtime |\n"
    "|---|---|---|---|---|\n"
)


@dataclass
class Servizio:
    nome: str
    comando: list[str]
    cartella: Path
    porta: int | None = None  # da controllare prima di partire


def ora_corrente() -> str:
    """Restituisce la data e ora locale formattata come stringa."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _stampa_sicura(messaggio: str, file=None) -> None:
    """Stampa con fallback ASCII difensivo per console Windows con codepage limitate."""
    dest = file if file is not None else sys.stdout
    try:
        print(messaggio, file=dest, flush=True)
    except UnicodeEncodeError:
        print(
            messaggio.encode("ascii", errors="replace").decode("ascii"),
            file=dest,
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


def _porta_occupata(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as presa:
        presa.settimeout(0.5)
        return presa.connect_ex(("127.0.0.1", porta)) == 0


def _controlli(servizi: list[Servizio]) -> list[str]:
    """I motivi per cui non si può partire; elenco vuoto se è tutto a posto."""
    problemi = []
    if shutil.which("uv") is None:
        problemi.append("`uv` non è installato: serve per API e worker.")
    if not (BACKEND / ".env").exists():
        problemi.append(
            "Manca backend/.env: `uv run python allinea.py` lo crea da .env.example."
        )
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


def _assicura_registro_esistente(file_registro: Path) -> None:
    """Crea registro_avvii.md con intestazione e tabella se non esiste o è vuoto."""
    if not file_registro.exists() or file_registro.stat().st_size == 0:
        try:
            file_registro.parent.mkdir(parents=True, exist_ok=True)
            file_registro.write_text(INTESTAZIONE_REGISTRO, encoding="utf-8")
        except OSError as errore:
            _stampa_sicura(
                f"[AVVISO] Impossibile creare il registro degli avvii: {errore}",
                file=sys.stderr,
            )


def _scrivi_log(file_log: Path | None, messaggio: str) -> None:
    """Scrive in modo thread-safe una riga nel file di log runtime se abilitato."""
    if not file_log:
        return
    with _BLOCCO_SCRITTURA:
        try:
            file_log.parent.mkdir(parents=True, exist_ok=True)
            with open(file_log, "a", encoding="utf-8") as f:
                f.write(messaggio + "\n")
        except OSError as errore:
            _stampa_sicura(
                f"[AVVISO] Errore di scrittura su {file_log.name}: {errore}",
                file=sys.stderr,
            )


def registra_avvio_nel_registro(
    file_registro: Path,
    servizi: list[Servizio],
    pids: dict[str, int],
    file_log: Path | None,
) -> None:
    """Accoda l'evento di avvio dei servizi nella tabella del registro."""
    _assicura_registro_esistente(file_registro)

    timestamp = ora_corrente()
    nomi_servizi = ", ".join(s.nome.upper() for s in servizi)
    dettagli_porte = (
        ", ".join(f"{s.nome}: {s.porta}" for s in servizi if s.porta)
        or "Nessuna porta diretta"
    )
    dettagli_pid = ", ".join(f"{nome}={pid}" for nome, pid in pids.items())
    nota_log = (
        f"Streaming in `{file_log.name}`" if file_log else "Log su file disabilitato"
    )

    riga = (
        f"| **{timestamp}** | {nomi_servizi} | `{dettagli_porte}` | "
        f"🟢 Attivo (PID: {dettagli_pid}) | {nota_log} |\n"
    )

    with _BLOCCO_SCRITTURA:
        try:
            contenuto = file_registro.read_text(encoding="utf-8")
            marcatore = "|---|---|---|---|---|\n"
            if marcatore in contenuto:
                parti = contenuto.split(marcatore, 1)
                nuovo_contenuto = parti[0] + marcatore + riga + parti[1]
            else:
                nuovo_contenuto = (
                    contenuto + ("\n" if not contenuto.endswith("\n") else "") + riga
                )
            file_registro.write_text(nuovo_contenuto, encoding="utf-8")
        except OSError as errore:
            _stampa_sicura(
                f"[AVVISO] Impossibile aggiornare {file_registro.name}: {errore}",
                file=sys.stderr,
            )


def registra_arresto_nel_registro(
    file_registro: Path,
    motivo: str = "Arrestato regolarmente (Ctrl+C)",
) -> None:
    """Aggiorna l'ultimo record attivo annotando data, ora e motivo dell'arresto."""
    if not file_registro.exists():
        return

    timestamp = ora_corrente()
    with _BLOCCO_SCRITTURA:
        try:
            contenuto = file_registro.read_text(encoding="utf-8")
            if "🟢 Attivo" in contenuto:
                nuovo_contenuto = contenuto.replace(
                    "🟢 Attivo", f"⏹️ {motivo} [{timestamp}]", 1
                )
                file_registro.write_text(nuovo_contenuto, encoding="utf-8")
        except OSError as errore:
            _stampa_sicura(
                f"[AVVISO] Impossibile registrare arresto in {file_registro.name}: {errore}",
                file=sys.stderr,
            )


def _scrivi_banner_avvio(
    servizi: list[Servizio],
    pids: dict[str, int],
    file_log: Path | None,
    file_registro: Path | None,
) -> None:
    """Stampa a video e scrive nel log il banner di avvio di AdFlow Suite."""
    timestamp = ora_corrente()
    separatore = "=" * 80
    nomi = ", ".join(s.nome.upper() for s in servizi)
    pid_str = ", ".join(f"{nome}={pid}" for nome, pid in pids.items())

    banner = (
        f"\n{separatore}\n"
        f"[{timestamp}] 🚀 AVVIO SOFTWARE ADFLOW SUITE (PID: {pid_str})\n"
        f"Servizi attivi: {nomi}\n"
        f"API: http://localhost:8000 (Swagger: http://localhost:8000/docs | Health: http://localhost:8000/api/health)\n"
    )
    if any(s.nome == "web" for s in servizi):
        banner += "Frontend: http://localhost:5173\n"
    if file_log:
        banner += f"File di log: {file_log}\n"
    if file_registro:
        banner += f"Registro avvii: {file_registro}\n"
    banner += (
        "Premere Ctrl+C per fermare tutti i servizi contemporaneamente.\n"
        f"{separatore}\n"
    )

    _stampa_sicura(banner)
    if file_log:
        _scrivi_log(file_log, banner)


def _inoltra(
    servizio: Servizio,
    processo: subprocess.Popen,
    larghezza: int,
    file_log: Path | None,
) -> None:
    """Riporta le righe del processo su console e contemporaneamente su file di log."""
    assert processo.stdout is not None
    for riga in processo.stdout:
        testo = riga.rstrip()
        prefisso_console = f"[{servizio.nome:<{larghezza}}]"
        _stampa_sicura(f"{prefisso_console} {testo}")
        if file_log:
            timestamp = ora_corrente()
            _scrivi_log(file_log, f"[{timestamp}] {prefisso_console} {testo}")


def _lancia(
    servizio: Servizio,
    larghezza: int,
    file_log: Path | None,
) -> subprocess.Popen:
    """Avvia il singolo servizio in un processo figlio e ne cattura lo stream."""
    processo = subprocess.Popen(
        servizio.comando,
        cwd=servizio.cartella,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        # Un gruppo a parte: così si ferma anche ciò che il processo ha avviato
        # (uvicorn --reload e vite hanno processi figli).
        start_new_session=not WINDOWS,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0,
    )
    threading.Thread(
        target=_inoltra,
        args=(servizio, processo, larghezza, file_log),
        daemon=True,
    ).start()
    return processo


def _ferma(processo: subprocess.Popen) -> None:
    """Arresta in modo pulito e immediato il processo e l'intero albero dei suoi figli."""
    if processo.poll() is not None:
        return
    if WINDOWS:
        try:
            subprocess.run(
                ["taskkill", "/PID", str(processo.pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
        except OSError:
            pass
        return
    try:
        os.killpg(processo.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        return
    try:
        processo.wait(timeout=8)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(processo.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Avvia API, worker e frontend con logging unificato e tracciamento."
    )
    parser.add_argument(
        "--senza-web", action="store_true", help="non avviare il frontend"
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="disabilita la registrazione su file di log e registro in logs/",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=FILE_LOG_RUNTIME,
        help=f"percorso personalizzato del file di log (predefinito: {FILE_LOG_RUNTIME})",
    )
    parser.add_argument(
        "--registro-file",
        type=Path,
        default=FILE_REGISTRO_AVVII,
        help=f"percorso personalizzato del file di registro (predefinito: {FILE_REGISTRO_AVVII})",
    )
    argomenti = parser.parse_args()

    servizi = _servizi(con_web=not argomenti.senza_web)
    problemi = _controlli(servizi)
    if problemi:
        for problema in problemi:
            _stampa_sicura(f"✗ {problema}", file=sys.stderr)
        return 1

    file_log = None if argomenti.no_log else argomenti.log_file
    file_registro = None if argomenti.no_log else argomenti.registro_file

    larghezza = max(len(s.nome) for s in servizi)
    avviati: list[tuple[Servizio, subprocess.Popen]] = []
    pids: dict[str, int] = {}
    motivo_arresto = "Arrestato regolarmente (Ctrl+C)"

    try:
        for servizio in servizi:
            proc = _lancia(servizio, larghezza, file_log)
            avviati.append((servizio, proc))
            pids[servizio.nome] = proc.pid

        # Registrazione e notifica dell'avvio
        if file_registro:
            registra_avvio_nel_registro(file_registro, servizi, pids, file_log)

        _scrivi_banner_avvio(servizi, pids, file_log, file_registro)

        while True:
            for servizio, processo in avviati:
                if processo.poll() is not None:
                    motivo_arresto = f"Servizio {servizio.nome} interrotto inaspettatamente (codice {processo.returncode})"
                    _stampa_sicura(
                        f"\n✗ {servizio.nome} si è fermato (codice {processo.returncode}): "
                        "fermo anche gli altri servizi.",
                        file=sys.stderr,
                    )
                    return 1
            time.sleep(1)

    except KeyboardInterrupt:
        motivo_arresto = "Arrestato regolarmente (Ctrl+C)"
        _stampa_sicura("\n[INFO] Arresto di tutti i servizi in corso...")
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        motivo_arresto = f"Errore imprevisto all'avvio: {exc}"
        _stampa_sicura(f"\n✗ {motivo_arresto}", file=sys.stderr)
        return 1

    finally:
        # Singola registrazione garantita dell'arresto (evita doppie scritture B5)
        if file_registro:
            registra_arresto_nel_registro(file_registro, motivo=motivo_arresto)

        if file_log:
            timestamp = ora_corrente()
            _scrivi_log(
                file_log,
                f"[{timestamp}] ⏹️ TUTTI I SERVIZI ARRESTATI ({motivo_arresto})\n",
            )

        for _, processo in reversed(avviati):
            _ferma(processo)


if __name__ == "__main__":
    sys.exit(main())
