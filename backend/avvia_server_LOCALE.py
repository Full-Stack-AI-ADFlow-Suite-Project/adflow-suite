# pylint: disable=invalid-name  # il suffisso _LOCALE e' intenzionale (file locale non tracciato)
"""Launcher locale per AdFlow Suite con registrazione automatica degli avvii e degli errori.

Questo script avvia il server Uvicorn (FastAPI) registrando data e ora esatta
di ogni avvio sia in CHANGELOG_LOCALE.md sia nel file di log di runtime
backend/app_runtime_LOCALE.log, consentendo l'analisi dinamica in tempo reale.

Uso da terminale (dalla cartella backend/):
    uv run python avvia_server_LOCALE.py
    uv run python avvia_server_LOCALE.py --port 8000
    uv run python avvia_server_LOCALE.py --host 127.0.0.1 --port 8000
    uv run python avvia_server_LOCALE.py --no-reload

Caratteristiche di affidabilità:
    - B3: deepcopy per evitare la contaminazione del dict globale uvicorn
    - B4: gestione sicura dei logger senza handlers (uvicorn.error propaga
          a uvicorn senza duplicare i messaggi nel log file)
    - B5: singola registrazione dell'arresto garantita nel blocco finally
    - Inizializzazione automatica di CHANGELOG_LOCALE.md se assente
"""

from __future__ import annotations

import argparse
import copy
import os
import sys
from datetime import datetime
from pathlib import Path

import uvicorn

CARTELLA_BACKEND = Path(__file__).resolve().parent
RADICE_PROGETTO = CARTELLA_BACKEND.parent
FILE_CHANGELOG = RADICE_PROGETTO / "CHANGELOG_LOCALE.md"
FILE_LOG_RUNTIME = CARTELLA_BACKEND / "app_runtime_LOCALE.log"

INTESTAZIONE_CHANGELOG = (
    "# Change Log & Registro Attività Software (Silvia · Corsia 2)\n\n"
    "> **USO LOCALE**: Questo file è privato e protetto da `.gitignore` (`*_LOCALE.md`).\n"
    "> Traccia in tempo reale gli avvii e gli arresti del server Uvicorn/FastAPI.\n\n"
    "---\n\n"
    "## 🚀 1. Registro degli Avvii del Software (Analisi Dinamica)\n\n"
    "| Data e Ora | Componente / Processo | Comando / Modalità | "
    "Esito Iniziale | Errori / Note di Runtime |\n"
    "|---|---|---|---|---|\n"
)


def ora_corrente() -> str:
    """Restituisce la data e ora locale formattata come stringa."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def assicura_changelog_esistente() -> None:
    """Crea CHANGELOG_LOCALE.md con intestazione e tabella se non esiste."""
    if not FILE_CHANGELOG.exists():
        try:
            FILE_CHANGELOG.write_text(INTESTAZIONE_CHANGELOG, encoding="utf-8")
        except Exception as errore:  # pylint: disable=broad-except
            print(f"[AVVISO] Impossibile creare CHANGELOG_LOCALE.md: {errore}")


def registra_avvio_nel_changelog(porta: int, reload: bool, pid: int) -> None:
    """Accoda l'evento di avvio nella tabella del file CHANGELOG_LOCALE.md."""
    assicura_changelog_esistente()

    timestamp = ora_corrente()
    modalita = f"Porta {porta}, reload={'Sì' if reload else 'No'}"
    riga = (
        f"| **{timestamp}** | API Server (Uvicorn/FastAPI) | `{modalita}` | "
        f"🟢 Attivo (PID {pid}) | Streaming attivo in `app_runtime_LOCALE.log` |\n"
    )

    try:
        contenuto = FILE_CHANGELOG.read_text(encoding="utf-8")
        marcatore = "|---|---|---|---|---|\n"
        if marcatore in contenuto:
            parti = contenuto.split(marcatore, 1)
            nuovo_contenuto = parti[0] + marcatore + riga + parti[1]
        else:
            nuovo_contenuto = (
                contenuto + ("\n" if not contenuto.endswith("\n") else "") + riga
            )
        FILE_CHANGELOG.write_text(nuovo_contenuto, encoding="utf-8")
    except Exception as errore:  # pylint: disable=broad-except
        print(f"[AVVISO] Impossibile aggiornare CHANGELOG_LOCALE.md: {errore}")


def registra_arresto_nel_changelog(
    motivo: str = "Arrestato regolarmente",
) -> None:
    """Aggiorna l'ultimo record di avvio attivo annotando la data e ora di arresto."""
    if not FILE_CHANGELOG.exists():
        return

    try:
        timestamp = ora_corrente()
        contenuto = FILE_CHANGELOG.read_text(encoding="utf-8")
        if "🟢 Attivo" in contenuto:
            contenuto = contenuto.replace("🟢 Attivo", f"⏹️ {motivo} [{timestamp}]", 1)
            FILE_CHANGELOG.write_text(contenuto, encoding="utf-8")
    except Exception as errore:  # pylint: disable=broad-except
        print(
            f"[AVVISO] Impossibile aggiornare arresto in CHANGELOG_LOCALE.md: {errore}"
        )


def configura_logging(file_log: Path) -> dict:
    """Configura Uvicorn per duplicare i log su console e su file.

    NOTA: usa copy.deepcopy() invece di .copy() (shallow) per evitare
    la contaminazione del dizionario globale uvicorn.config.LOGGING_CONFIG,
    che è un oggetto condiviso a livello di modulo (B3).
    """
    # FIX B3: deepcopy invece di shallow copy per non contaminare il dict globale
    log_config = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)

    # Aggiunge FileHandler per registrare tutto lo stream su file
    log_config["handlers"]["file"] = {
        "class": "logging.FileHandler",
        "filename": str(file_log),
        "mode": "a",
        "encoding": "utf-8",
        "formatter": "default",
    }

    # FIX B4: i logger con 'handlers' espliciti ricevono l'handler 'file'.
    # I logger privi di 'handlers' (come uvicorn.error) hanno propagate=True
    # di default verso il logger padre 'uvicorn' (che possiede già 'file' e console).
    # Se assegnassimo un handler 'file' dedicato a uvicorn.error, i messaggi
    # verrebbero scritti due volte nel file di log.
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        if logger_name not in log_config["loggers"]:
            continue
        logger_cfg = log_config["loggers"][logger_name]
        if "handlers" not in logger_cfg:
            continue
        handlers = list(logger_cfg["handlers"])
        if "file" not in handlers:
            handlers.append("file")
        logger_cfg["handlers"] = handlers

    return log_config


def scrivi_banner_avvio(porta: int, reload: bool, pid: int) -> None:
    """Scrive un'intestazione evidente nel file di log di runtime e su console."""
    timestamp = ora_corrente()
    separatore = "=" * 80
    messaggio = (
        f"\n{separatore}\n"
        f"[{timestamp}] 🚀 AVVIO SOFTWARE ADFLOW SUITE (PID: {pid})\n"
        f"Ambiente: Locale | Indirizzo: http://127.0.0.1:{porta} | Reload: {reload}\n"
        f"Documentazione Swagger: http://localhost:{porta}/docs\n"
        f"Health Check: http://localhost:{porta}/api/health\n"
        f"{separatore}\n"
    )
    # Crea il file di log se non esiste (open in modalita 'a' lo crea automaticamente)
    with open(FILE_LOG_RUNTIME, "a", encoding="utf-8") as f:
        f.write(messaggio)
    print(messaggio)


def main() -> int:
    """Punto d'ingresso: analizza gli argomenti, registra l'avvio e lancia il server."""
    parser = argparse.ArgumentParser(
        description=(
            "Avvia il server AdFlow Suite con registrazione automatica di avvii ed errori."
        )
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta TCP su cui esporre l'API (predefinita: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host di ascolto (predefinito: 127.0.0.1)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disabilita il ricaricamento automatico al salvataggio del codice",
    )

    args = parser.parse_args()
    pid = os.getpid()
    reload = not args.no_reload

    scrivi_banner_avvio(porta=args.port, reload=reload, pid=pid)
    registra_avvio_nel_changelog(porta=args.port, reload=reload, pid=pid)

    log_config = configura_logging(FILE_LOG_RUNTIME)

    # FIX B5: rimossa la chiamata a registra_arresto_nel_changelog() dal blocco
    # 'except Exception': era una doppia scrittura perché il 'finally' la chiama
    # sempre comunque. Ora l'arresto viene registrato UNA SOLA VOLTA nel 'finally'.
    errore_critico: Exception | None = None
    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=reload,
            log_config=log_config,
        )
    except KeyboardInterrupt:
        print("\n[INFO] Arresto del server in corso...")
    except Exception as exc:  # pylint: disable=broad-except
        errore_critico = exc
        timestamp = ora_corrente()
        errore_msg = f"[{timestamp}] 💥 ERRORE CRITICO ALL'AVVIO: {exc}\n"
        print(f"\n{errore_msg}")
        with open(FILE_LOG_RUNTIME, "a", encoding="utf-8") as f:
            f.write(errore_msg)
    finally:
        # Unico punto di registrazione dell'arresto: evita la doppia scrittura (B5)
        motivo = f"Errore critico: {errore_critico}" if errore_critico else "Arrestato"
        registra_arresto_nel_changelog(motivo=motivo)
        with open(FILE_LOG_RUNTIME, "a", encoding="utf-8") as f:
            f.write(f"[{ora_corrente()}] ⏹️ SERVER ARRESTATO\n")

    return 1 if errore_critico else 0


if __name__ == "__main__":
    sys.exit(main())
