# Ambiente comune dei due script del percorso E2E (si legge con `source`):
# cartella del backend, database dedicato adflow_e2e e provider finti.
# Il database lo ricava l'app dalla sua configurazione (DATABASE_URL del
# processo o backend/.env): qui nessun file di segreti si legge a mano.
for percorso in /home/giova/.local/bin /home/giova/.local/share/fnm; do
  [ -d "$percorso" ] && PATH="$percorso:$PATH"
done
export PATH
command -v fnm >/dev/null 2>&1 && eval "$(fnm env --shell bash)"
cd "$(dirname "${BASH_SOURCE[0]}")/../../backend" || exit 1

DATABASE_URL_E2E="$(uv run python -c "
from sqlalchemy.engine import make_url
from app.core.config import leggi_impostazioni
url = make_url(leggi_impostazioni().database_url).set(database='adflow_e2e')
print(url.render_as_string(hide_password=False))
")" || exit 1
export DATABASE_URL="$DATABASE_URL_E2E"
export AI_PROVIDER=finto SOCIAL_PROVIDER=finto
