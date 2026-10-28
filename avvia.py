"""Avvia API, worker e frontend con un solo comando, e li ferma insieme.

Dalla radice del repository:

    uv run python avvia.py                tutto: API, worker e frontend
    uv run python avvia.py --senza-web    solo API e worker

Per riavviare si preme Ctrl+C (ferma tutto) e si rilancia il comando: l'API si
ricarica da sola a ogni modifica, il worker no. Se una porta è già occupata (un
avvio precedente ancora vivo) il comando lo dice e non parte.

Il worker esegue anche il tick di pubblicazione ogni minuto. Con
`OROLOGIO_GIORNI_AVANTI` in `backend/.env` API e worker leggono la stessa ora
spostata: dopo averlo cambiato basta riavviare con questo comando.

Usa solo la libreria standard.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

RADICE = Path(__file__).resolve().parent
BACKEND = RADICE / "backend"
FRONTEND = RADICE / "frontend"
WINDOWS = os.name == "nt"


@dataclass
class Servizio:
    nome: str
    comando: list[str]
    cartella: Path
    porta: int | None = None  # da controllare prima di partire


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


def _inoltra(servizio: Servizio, processo: subprocess.Popen, larghezza: int) -> None:
    """Riporta le righe del processo con il suo nome davanti."""
    for riga in processo.stdout:
        print(f"[{servizio.nome:<{larghezza}}] {riga.rstrip()}", flush=True)


def _lancia(servizio: Servizio, larghezza: int) -> subprocess.Popen:
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
        target=_inoltra, args=(servizio, processo, larghezza), daemon=True
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
        os.killpg(processo.pid, signal.SIGKILL)


def main() -> int:
    parser = argparse.ArgumentParser(description="Avvia API, worker e frontend.")
    parser.add_argument(
        "--senza-web", action="store_true", help="non avviare il frontend"
    )
    argomenti = parser.parse_args()

    servizi = _servizi(con_web=not argomenti.senza_web)
    problemi = _controlli(servizi)
    if problemi:
        for problema in problemi:
            print(f"✗ {problema}", file=sys.stderr)
        return 1

    larghezza = max(len(s.nome) for s in servizi)
    avviati: list[tuple[Servizio, subprocess.Popen]] = []
    try:
        for servizio in servizi:
            avviati.append((servizio, _lancia(servizio, larghezza)))
        print(
            "API http://localhost:8000 · frontend http://localhost:5173 · Ctrl+C per fermare"
        )
        while True:
            for servizio, processo in avviati:
                if processo.poll() is not None:
                    print(
                        f"✗ {servizio.nome} si è fermato (codice {processo.returncode}): "
                        "fermo anche gli altri.",
                        file=sys.stderr,
                    )
                    return 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nFermo tutto…")
        return 0
    finally:
        for _, processo in reversed(avviati):
            _ferma(processo)


if __name__ == "__main__":
    sys.exit(main())
