# AdFlow Suite · Frontend

React + TypeScript + Vite, con Mantine. Riferimenti: `docs/agenti/plan.md` §3,
`docs/agenti/constitution.md` §2 e §4, spec R-29; le pagine statiche da cui
è nata l'interfaccia sono in `docs/archivio/pagine/` (mappa in `index.html`).

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
generazione e la pubblicazione e gli utenti del seed (`backend/README.md`).

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
npm test
```

Gli stessi comandi girano a ogni PR (`.github/workflows/frontend.yml`).

`npm test` lancia i test dei componenti (Vitest, Testing Library, MSW): `src/**/*.test.tsx`, accanto al componente. `src/test/` ha il finto server (`server.ts`, ogni test dichiara le sue risposte con `server.use(...)`; una richiesta non prevista è un errore), l'avvio (`setup.ts`) e `disegna()` (tema, router in memoria e sessione finta).
Test end-to-end (Playwright, Chromium): `npm run test:e2e`, da `frontend/`. Playwright avvia da sé il backend (`e2e/prepara-backend.sh`: database dedicato `adflow_e2e`, migrazioni, seed, provider AI e social finti) e il frontend. Due progetti, in ordine: `percorso-demo` (database vuoto) e `ritocco`, che prima prepara una campagna con quattro foto sintetiche (`e2e/prepara-dati-ritocco.sh`, `backend/scripts/prepara_dati_ritocco_e2e.py`). Se il Chromium di Playwright non si installa sulla tua macchina, `PLAYWRIGHT_CHROMIUM=/percorso/di/chrome npm run test:e2e`. In CI gira nel workflow `.github/workflows/e2e.yml`.

## Struttura

```
src/
  api/<modulo>.ts    tipi che rispecchiano gli schemas.py del modulo
  api/esempi/        dati di esempio con la forma di plan §3
  api/http.ts        fetch verso /api; ogni 401 torna all'accesso
  auth.tsx           sessione, guard per ruolo, pagina iniziale per ruolo
  pages/             Accesso, artigiano/, operatore/
  components/        cornici condivise (Guscio: barra laterale e pagina)
  tema.ts            palette e caratteri (da docs/archivio/pagine/assets/adflow.css)
  index.css          token con i nomi di adflow.css; i valori stanno in tema.ts
```
