#!/usr/bin/env bash
# Dati del percorso del ritocco (RT-10): una campagna con quattro foto sintetiche,
# generata con l'AI finta, nel database adflow_e2e già creato da prepara-backend.sh.
# Lo lancia il test del ritocco prima di partire (non il test della demo, che
# vuole il database vuoto).
set -eu
source "$(dirname "$0")/ambiente.sh"
exec uv run python scripts/prepara_dati_ritocco_e2e.py
