# AdFlow Suite · istruzioni per gli agenti

Monorepo: `backend/` (FastAPI + worker Procrastinate, PostgreSQL), `frontend/` (React + Vite + Mantine), `docs/`.

Siamo nello **sprint 3 · MVP** (ADR-114): consegna il 6 novembre 2026, codice bloccato il 30 ottobre. Che cosa entra nell'MVP lo dice `docs/agenti/perimetro-mvp.md`.

## Si parte da qui

A inizio sessione, dalla radice, prima di ogni altra cosa:

```bash
uv run python allinea.py
```

Aggiorna `main`, le dipendenze e il database senza toccare il lavoro in corso, poi stampa i task pronti dell'area, cosa leggere per ognuno e il branch da aprire. L'area si indica una volta sola (`uv run python allinea.py 3`) e resta ricordata. Il task si sceglie da ciò che stampa, non a memoria e non dalle note di una sessione precedente: la fonte è `docs/agenti/tasks.md` su `main`. Se la persona non ha indicato un task, proponi il primo segnato PRONTO e aspetta la conferma. Queste istruzioni valgono per ogni agente, qualunque sia lo strumento con cui lavori.

## Cosa leggere

1. `docs/agenti/constitution.md` e `docs/agenti/perimetro-mvp.md`: sempre, prima di tutto.
2. La riga del tuo task in `docs/agenti/tasks.md` e il brief che cita, se c'è (`brief-interventi.md`, `brief-pagine.md`, `brief-interfaccia.md`, `brief-richieste.md`).
3. **Solo** le sezioni di `docs/agenti/spec.md` e `docs/agenti/plan.md` citate dal task.
4. Se scrivi codice del backend: `docs/agenti/plan.md` §7 (cosa offre già `core/` e come si usano le fixture dei test).
5. Prima della PR: `docs/agenti/converge.md`.

Le pagine statiche di `docs/pagine/` sono il riferimento per l'interfaccia dell'MVP (mappa in `index.html`): un task del frontend le usa. `docs/ADR.md` è il registro delle decisioni. `docs/archivio/` è un archivio (ADR-115): non fa testo e non si legge, se il prompt non lo chiede con un percorso preciso. Dove qualcosa non torna, vale `docs/agenti/`, e dentro `docs/agenti/` vale `perimetro-mvp.md`.

## Comandi

Serve `uv`: `uv run` usa `.venv` senza attivarlo, così i comandi sono gli stessi su Windows, macOS e Linux. Si lanciano uno alla volta (`&&` non funziona in ogni shell).
Dalla radice: `uv run python allinea.py` prepara tutto, anche la prima volta (crea `.venv`, installa le dipendenze, copia `backend/.env.example` in `backend/.env` e chiede di metterci le credenziali di PostgreSQL).
Da `backend/`: `uv run uvicorn app.main:app --reload` avvia l'API; `uv run alembic upgrade head`, poi `uv run pytest`, poi `uv run black --check .` sono il controllo prima della PR. GitHub li rilancia a ogni PR (`.github/workflows/backend.yml`).

## Come lavori

- Un task alla volta, su un branch `feature/<id>-<breve>`, mai su `main`.
- Fai solo il task: il resto diventa un nuovo task o una domanda.
- Non costruire e non estendere ciò che `perimetro-mvp.md` segna *Togli*, *Congela* o *Roadmap*. Il codice congelato porta il commento "Congelato per l'MVP, ADR-114": non si modifica.
- Tocchi i file che servono al task, con i loro test: le aree di `tasks.md` dicono chi lavora dove, non quali file sono proibiti. Se cambi composizione, `core/`, `alembic/`, `backend/requirements.txt` o un `domain.py`, scrivilo nella PR: la rivede il referente dei file comuni.
- I dati di un altro modulo si leggono solo con le funzioni di plan §6: niente SQL scritto a mano sulle sue tabelle e niente copie delle sue costanti. Se la funzione che serve non c'è, la aggiungi nel tuo task, nel `service.py` di quel modulo, e la scrivi in plan §6.
- Una libreria nuova entra in `backend/requirements.txt` nella PR del task che la usa, con nome, motivo e licenza.
- Nel frontend una pagina usa i dati di esempio (`src/api/esempi/`) finché il suo endpoint non è su `main`; poi passa alle API vere.
- Nei test nessuna chiamata reale ad AI, Meta o email.
- Se manca un'informazione o due documenti non tornano, fermati e chiedi. Non inventare requisiti.
- Commit in italiano all'imperativo: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`.
- Non modificare `docs/archivio/`. `docs/pagine/`, `docs/ADR.md` e `docs/agenti/` si modificano solo se il task o il prompt lo chiede (una riga nuova in `ADR.md` solo se cambia il perimetro); la casella del tuo task in `tasks.md` la spunti nella tua PR.
