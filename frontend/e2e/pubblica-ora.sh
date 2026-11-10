#!/usr/bin/env bash
# Fa uscire i post approvati con il social finto (RT-33): il comando delle prove a mano,
# sul database adflow_e2e. Lo lancia il test del ritocco dopo Approva.
set -eu
source "$(dirname "$0")/ambiente.sh"
exec uv run python -m app.cli pubblica-ora
