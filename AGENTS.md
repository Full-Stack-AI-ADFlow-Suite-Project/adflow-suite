# AdFlow Suite · istruzioni per gli agenti

Monorepo: `backend/` (FastAPI + worker Procrastinate, PostgreSQL), `frontend/` (React + Vite + Mantine), `docs/`.

## Cosa leggere
1. `docs/agenti/constitution.md`: sempre, prima di tutto.
2. La riga del tuo task in `docs/agenti/tasks.md`.
3. **Solo** le sezioni di `docs/agenti/spec.md` e `docs/agenti/plan.md` citate dal task.
4. Prima della PR: `docs/agenti/converge.md`.

**Non leggere `docs/umano/`** (diagrammi, pagine HTML, documenti per le persone) se il prompt non te lo chiede con un percorso preciso. Per i task ampi la persona che ti assegna il lavoro ti dà un **brief**: le parti del canale umano che servono, nel prompt o come file da leggere.

## Come lavori
- Un task alla volta, su un branch `feature/<id>-<breve>`, mai su `main`.
- Fai solo il task: il resto diventa un nuovo task o una domanda.
- Se manca un'informazione o due documenti non tornano, fermati e chiedi. Non inventare requisiti.
- Commit in italiano all'imperativo: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`.
- Non modificare `docs/umano/`. Puoi modificare `docs/agenti/` solo se il task o il prompt lo chiede.
