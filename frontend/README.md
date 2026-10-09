# AdFlow Suite · Frontend

React + TypeScript + Vite, con Mantine. Riferimenti: `docs/agenti/plan.md` §3,
`docs/agenti/constitution.md` §2 e §4, spec R-29; pagine statiche approvate
in `docs/appunti/pagine/`.

## Installazione e avvio

Serve Node 22+. Da `frontend/`:

```bash
npm install
npm run dev
```

L'app si apre su http://localhost:5173. Le chiamate `/api` vanno in proxy
verso il backend su http://localhost:8000 (`vite.config.ts`).

## Dati di esempio

Di default le pagine usano i dati di esempio di `src/api/esempi/`, con la
forma delle API di plan §3: servono finché non si passa alle API vere
(T1-07). Utenti di esempio, password `prova`:

| Email | Ruolo | Pagina di partenza |
|---|---|---|
| `mario@falegnameriabianchi.it` | artigiano | `/campagna` |
| `laura@consorzio.example` | operatore | `/da-approvare` |
| `admin@consorzio.example` | admin | `/da-approvare` |

Per usare le API vere (backend avviato con
`uv run uvicorn app.main:app --reload` da `backend/`):

```bash
VITE_USA_ESEMPI=0 npm run dev
```

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
  components/        cornici condivise (Guscio)
  tema.ts            palette e caratteri delle pagine statiche
```
