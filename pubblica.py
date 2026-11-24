"""Pubblica subito su Facebook i post approvati: ferma tutto, pubblica, riavvia tutto.

Per la presentazione, dopo aver generato e approvato una campagna. Dalla radice:

    uv run python pubblica.py

Se `avvia.py` è in esecuzione gli chiede di fermare API, worker e frontend, far
uscire i post di Facebook (`app.cli pubblica-ora --canale facebook`) e rilanciare
tutto: il lavoro lo fa lui, nel suo terminale, e qui si legge l'esito. Se non è
in esecuzione pubblica e basta, senza avviare niente. Non sposta l'orologio.

Il codice di uscita è 0 se la pubblicazione è andata bene e tutto è ripartito.
Sul social vero (`SOCIAL_PROVIDER=meta` in backend/.env) i post escono davvero.

Usa solo la libreria standard.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

import avvia

SECONDI_ATTESA_ESITO = 900  # fermare, pubblicare e rilanciare: con Meta serve tempo


def avvia_in_esecuzione() -> bool:
    """True se un altro `avvia.py` è vivo (dal suo file dei PID)."""
    pid = avvia._pid_scritto(avvia.FILE_PID)
    return pid is not None and pid != os.getpid() and avvia._processo_vivo(pid)


def _stampa_esito(esito: dict) -> None:
    for riga in esito.get("righe", []):
        print(f"  {riga}")


def pubblica_da_solo() -> int:
    """`avvia.py` non c'è: nessun servizio da fermare, si pubblica e basta."""
    servizio = avvia._servizio_pubblicazione()
    print("avvia.py non è in esecuzione: pubblico senza fermare né riavviare.")
    try:
        return subprocess.run(servizio.comando, cwd=servizio.cartella).returncode
    except OSError as errore:
        print(f"✗ Non riesco a lanciare il comando: {errore}", file=sys.stderr)
        return 1


def chiedi_ad_avvia(secondi: int = SECONDI_ATTESA_ESITO) -> int:
    """Scrive la richiesta, aspetta l'esito di `avvia.py` e lo riporta."""
    codice_richiesta = uuid.uuid4().hex
    file_richiesta: Path = avvia.FILE_RICHIESTA_PUBBLICAZIONE
    file_esito: Path = avvia.FILE_ESITO_PUBBLICAZIONE
    file_esito.unlink(missing_ok=True)
    # Prima un file provvisorio, poi lo si rinomina: avvia.py non ne legge metà.
    provvisorio = file_richiesta.with_name(file_richiesta.name + ".tmp")
    provvisorio.write_text(codice_richiesta, encoding="utf-8")
    os.replace(provvisorio, file_richiesta)
    print("Richiesta inviata ad avvia.py: ferma tutto, pubblica su Facebook, riavvia.")

    fine = time.monotonic() + secondi
    while time.monotonic() < fine:
        try:
            esito = json.loads(file_esito.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            esito = None
        if esito is not None and esito.get("codice_richiesta") == codice_richiesta:
            _stampa_esito(esito)
            if esito.get("codice") != 0:
                print("✗ La pubblicazione non è andata a buon fine.", file=sys.stderr)
            if not esito.get("riavviato"):
                print(
                    "✗ Il riavvio non è riuscito: rilancia avvia.py.", file=sys.stderr
                )
            if esito.get("codice") == 0 and esito.get("riavviato"):
                print("✓ Pubblicato e tutto riavviato.")
                return 0
            return 1
        if not avvia_in_esecuzione():
            print("✗ avvia.py si è fermato prima di rispondere.", file=sys.stderr)
            file_richiesta.unlink(missing_ok=True)
            return 1
        time.sleep(0.5)
    file_richiesta.unlink(missing_ok=True)
    print(
        f"✗ Nessuna risposta da avvia.py in {secondi} s: guarda il suo terminale.",
        file=sys.stderr,
    )
    return 1


def main() -> int:
    if avvia_in_esecuzione():
        return chiedi_ad_avvia()
    return pubblica_da_solo()


if __name__ == "__main__":
    sys.exit(main())
