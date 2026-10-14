# AdFlow Suite · Frontend

React + TypeScript + Vite, con Mantine. Riferimenti: `docs/agenti/plan.md` §3,
`docs/agenti/constitution.md` §2 e §4, spec R-29; pagine statiche dell'MVP
in `docs/appunti/pagine/` (mappa in `index.html`).

## Installazione e avvio

Serve Node 22+. Da `frontend/`:

```bash
npm install
npm run dev
```

L'app si apre su http://localhost:5173. Le chiamate `/api` vanno in proxy
verso il backend su http://localhost:8000 (`vite.config.ts`).

## API vere e dati di esempio

Di default le pagine chiamano le API vere: serve il backend avviato
(`uv run uvicorn app.main:app --reload` da `backend/`), con il worker per la
generazione e la pubblicazione e gli utenti del seed (README della radice).

Una pagina il cui endpoint non è ancora su `main` usa i dati di esempio
finché il suo task non la passa alle API vere (AGENTS.md).

Per lavorare a una pagina senza il backend ci sono i dati di esempio di
`src/api/esempi/`, con la forma delle API di plan §3. Si accendono con un file
`frontend/.env.local` (non va in git) che contiene:

```
VITE_USA_ESEMPI=1
```

Utenti di esempio, password `prova`:

| Email | Ruolo | Pagina di partenza |
|---|---|---|
| `mario@falegnameriabianchi.it` | artigiano | `/campagna` |
| `laura@consorzio.example` | operatore | `/da-approvare` |
| `admin@consorzio.example` | admin | `/da-approvare` |

## Controlli

```bash
npm run lint
npm run build
```

Gli stessi comandi girano a ogni PR (`.github/workflows/frontend.yml`).

## Struttura

```
src/
  api/<modulo>.ts    tipi che rispecchiano gli schemas.py del modulo
  api/esempi/        dati di esempio con la forma di plan §3
  api/http.ts        fetch verso /api; ogni 401 torna all'accesso
  auth.tsx           sessione, guard per ruolo, pagina iniziale per ruolo
  pages/             Accesso, artigiano/, operatore/
  components/        cornici condivise (Guscio: barra laterale e pagina)
  tema.ts            palette e caratteri delle pagine statiche (assets/adflow.css)
  index.css          token con i nomi di adflow.css; i valori stanno in tema.ts
```
