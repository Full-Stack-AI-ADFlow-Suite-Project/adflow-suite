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


## Nuovo artigiano (T3-54)

Operatore e admin aprono `/nuovo-artigiano` dalla barra laterale: solo email e
nome del referente, poi la password provvisoria da annotare una volta. Confermare
«Ho annotato la password», cambiare pagina o ricaricare la elimina dalla vista.
La password non viene salvata nel browser né nei dati di esempio.

Finché T3-11 (#109) non è su main, la sola creazione usa dati di esempio, con
un avviso di anteprima: gli account non sono reali. Le email duplicate vengono
ricordate in memoria fino al ricaricamento, senza password. Per verificare il
contratto su una copia che contiene T3-11, avviare Vite con
`VITE_CREAZIONE_ARTIGIANI_API=1` nell'ambiente del processo: invia
`POST /api/artigiani` con `{email, nome}`. `VITE_USA_ESEMPI=1` mantiene tutti
i servizi simulati e ha precedenza. Dopo l'integrazione dell'endpoint, attivare
la creazione via API nella configurazione del frontend.


### Prova browser ripetibile di T3-54

`tests/nuovo-artigiano.cjs` usa Playwright già disponibile nell'ambiente
(`PLAYWRIGHT_PATH` può indicarne il percorso). Aprire due server Vite su
127.0.0.1:5184 e :5185, entrambi con `VITE_USA_ESEMPI=0`: sul primo
`VITE_CREAZIONE_ARTIGIANI_API=0`, sul secondo `=1`. Eseguire poi
`node tests/nuovo-artigiano.cjs`. Gli indirizzi si possono cambiare con
`ARTIGIANO_ESEMPI_TEST_URL` e `ARTIGIANO_API_TEST_URL` (solo localhost).
Il test intercetta tutte le API e blocca altre origini: non crea utenti reali.
Verifica CA-79 nella pagina, duplicati, dati obbligatori, 401/403/409/422/500,
doppio invio, admin/artigiano/anonimo, copia esplicita, nessuna password nello
storage o nei log, uscita durante l'attesa, navigazione, ricaricamento e mobile.
`SCREENSHOT_DIR` salva le schermate; quelle in `tests/evidenze/` contengono
esclusivamente credenziali finte di test, senza possibilità di accesso.
