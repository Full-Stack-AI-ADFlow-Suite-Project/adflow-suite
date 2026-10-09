# AdFlow Suite · istruzioni per gli agenti

Monorepo: `backend/` (FastAPI + worker Procrastinate, PostgreSQL), `frontend/` (React + Vite + Mantine), `docs/`.

## Si parte da qui

A inizio sessione, dalla radice, prima di ogni altra cosa:

```bash
uv run python allinea.py
```

Aggiorna `main`, le dipendenze e il database senza toccare il lavoro in corso, poi stampa i task pronti della corsia, cosa leggere per ognuno e il branch da aprire. La corsia si indica una volta sola (`uv run python allinea.py 3`) e resta ricordata. Il task si sceglie da ciò che stampa, non a memoria e non dalle note di una sessione precedente: la fonte è `docs/agenti/tasks.md` su `main`. Se la persona non ha indicato un task, proponi il primo segnato PRONTO e aspetta la conferma.

## Cosa leggere

1. `docs/agenti/constitution.md`: sempre, prima di tutto.
2. La riga del tuo task in `docs/agenti/tasks.md`, con la sua corsia.
3. **Solo** le sezioni di `docs/agenti/spec.md` e `docs/agenti/plan.md` citate dal task.
4. Se scrivi codice del backend: `docs/agenti/plan.md` §7 (cosa offre già `core/` e come si usano le fixture dei test).
5. Prima della PR: `docs/agenti/converge.md`.

`docs/novita/` raccoglie le note datate di alcune PR: raccontano cosa è entrato quel giorno e non fanno testo. Dove non tornano con `docs/agenti/`, vale `docs/agenti/`.

## Comandi

Serve `uv`: `uv run` usa `.venv` senza attivarlo, così i comandi sono gli stessi su Windows, macOS e Linux. Si lanciano uno alla volta (`&&` non funziona in ogni shell).
Dalla radice: `uv run python allinea.py` prepara tutto, anche la prima volta (crea `.venv`, installa le dipendenze, copia `backend/.env.example` in `backend/.env` e chiede di metterci le credenziali di PostgreSQL).
Da `backend/`: `uv run uvicorn app.main:app --reload` avvia l'API; `uv run alembic upgrade head`, poi `uv run pytest`, poi `uv run black --check .` sono il controllo prima della PR. GitHub li rilancia a ogni PR (`.github/workflows/backend.yml`).

**Non leggere `docs/appunti/`** (diagrammi, pagine HTML, note delle persone) se il prompt non te lo chiede con un percorso preciso. Per i task ampi la persona che ti assegna il lavoro ti dà un **brief**: le parti degli appunti che servono, nel prompt o come file da leggere.

## Come lavori

- Un task alla volta, su un branch `feature/<id>-<breve>`, mai su `main`.
- Fai solo il task: il resto diventa un nuovo task o una domanda.
- Tocchi solo ciò che appartiene alla corsia del task (`tasks.md`). Ciò che è della corsia 0 (tabelle, stati, funzioni di plan §6, `core/`, composizione, `requirements.txt`) non si cambia in un task delle corsie 1–5: fermati e chiedi.
- Una libreria nuova entra in `backend/requirements.txt` con una PR della corsia 0 **prima** della PR del task: senza, l'API e i test degli altri non partono.
- I dati di un altro modulo si leggono solo con le funzioni di plan §6: niente SQL scritto a mano sulle sue tabelle e niente copie delle sue costanti. Se la funzione che serve non c'è, è una domanda per la corsia 0.
- Quando porti `main` nel tuo branch e c'è un conflitto in un file che contiene funzioni della corsia 0, di quelle funzioni tieni la versione di `main`.
- Se manca un'informazione o due documenti non tornano, fermati e chiedi. Non inventare requisiti.
- Commit in italiano all'imperativo: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`.
- Non modificare `docs/appunti/`. Puoi modificare `docs/agenti/` solo se il task o il prompt lo chiede; la casella del tuo task in `tasks.md` la spunti nella tua PR.
