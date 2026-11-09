#!/usr/bin/env bash
# Backend del percorso E2E di T4-106: database dedicato adflow_e2e, migrazioni,
# seed con una password di prova fissa, poi Uvicorn con i provider finti.
# Il database della demo e delle prove (adflow, adflow_test) non si tocca.
# In CI (RT-10) lo lancia Playwright come in locale: l'ambiente è in ambiente.sh.
set -u
source "$(dirname "$0")/ambiente.sh"

PW="E2eSonda!2026"

uv run python - <<'PY'
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
base = make_url(os.environ["DATABASE_URL"])
motore = create_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")
with motore.connect() as c:
    c.execute(text("DROP DATABASE IF EXISTS adflow_e2e"))
    c.execute(text("CREATE DATABASE adflow_e2e"))
print("adflow_e2e creato")
PY

uv run alembic upgrade head
printf '%s\n%s\n' "$PW" "$PW" | uv run python -m app.cli seed
exec uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning
