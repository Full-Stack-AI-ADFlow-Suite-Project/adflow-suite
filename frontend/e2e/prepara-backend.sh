#!/usr/bin/env bash
# Backend del percorso E2E di T4-106: database dedicato adflow_e2e, migrazioni,
# seed con una password di prova fissa, poi Uvicorn con i provider finti.
# Il database della demo e delle prove (adflow, adflow_test) non si tocca.
set -u
export PATH="/home/giova/.local/bin:/home/giova/.local/share/fnm:$PATH"
eval "$(fnm env --shell bash)"
cd "$(dirname "$0")/../../backend" || exit 1

PW="E2eSonda!2026"

uv run python - <<'EOF'
import re
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
env = Path(".env").read_text("utf-8")
base = make_url(re.search(r"^DATABASE_URL=(.+)$", env, flags=re.M).group(1))
motore = create_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")
with motore.connect() as c:
    c.execute(text("DROP DATABASE IF EXISTS adflow_e2e"))
    c.execute(text("CREATE DATABASE adflow_e2e"))
print("adflow_e2e creato")
EOF

export DATABASE_URL="$(python3 - <<'PY'
import re
env = open(".env", encoding="utf-8").read()
url = re.search(r"^DATABASE_URL=(.+)$", env, flags=re.M).group(1)
print(re.sub(r"/[^/@?]+$", "/adflow_e2e", url))
PY
)"
export AI_PROVIDER=finto SOCIAL_PROVIDER=finto

uv run alembic upgrade head
printf '%s\n%s\n' "$PW" "$PW" | uv run python -m app.cli seed
exec uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning
