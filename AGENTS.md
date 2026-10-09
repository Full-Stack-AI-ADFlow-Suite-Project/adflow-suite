# AdFlow Suite · istruzioni per gli agenti

Monorepo: `backend/` (FastAPI + worker Procrastinate, PostgreSQL), `frontend/` (React + Vite + Mantine), `docs/`.

## Cosa leggere

1. `docs/agenti/constitution.md`: sempre, prima di tutto.
2. La riga del tuo task in `docs/agenti/tasks.md`, con la sua corsia.
3. **Solo** le sezioni di `docs/agenti/spec.md` e `docs/agenti/plan.md` citate dal task.
4. Se scrivi codice del backend: `docs/agenti/plan.md` §7 (cosa offre già `core/` e come si usano le fixture dei test).
5. Prima della PR: `docs/agenti/converge.md`.

## Comandi

Serve `uv`: `uv run` usa `.venv` senza attivarlo, così i comandi sono gli stessi su Windows, macOS e Linux. Si lanciano uno alla volta (`&&` non funziona in ogni shell).
Dalla radice, una volta: `uv venv --python 3.11 --seed .venv`, `uv pip install -r backend/requirements.txt`, poi copia `backend/.env.example` in `backend/.env`.
Da `backend/`: `uv run uvicorn app.main:app --reload` avvia l'API; `uv run alembic upgrade head`, poi `uv run pytest`, poi `uv run black --check .` sono il controllo prima della PR. GitHub li rilancia a ogni PR (`.github/workflows/backend.yml`).

**Non leggere `docs/appunti/`** (diagrammi, pagine HTML, note delle persone) se il prompt non te lo chiede con un percorso preciso. Per i task ampi la persona che ti assegna il lavoro ti dà un **brief**: le parti degli appunti che servono, nel prompt o come file da leggere.

## Come lavori

- Un task alla volta, su un branch `feature/<id>-<breve>`, mai su `main`.
- Fai solo il task: il resto diventa un nuovo task o una domanda.
- Tocchi solo ciò che appartiene alla corsia del task (`tasks.md`). Ciò che è della corsia 0 (tabelle, stati, funzioni di plan §6, `core/`, composizione) non si cambia in un task delle corsie 1–5: fermati e chiedi.
- Se manca un'informazione o due documenti non tornano, fermati e chiedi. Non inventare requisiti.
- Commit in italiano all'imperativo: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`.
- Non modificare `docs/appunti/`. Puoi modificare `docs/agenti/` solo se il task o il prompt lo chiede.
