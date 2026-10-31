# T4-106 · Frontend

Copre §4.4, §6 (frontend, E2E, accessibilità, contratto) di
`accettazione-post-mvp.md` e converge §4. Strumenti: Playwright 1.64.1
(Apache-2.0) e `@axe-core/playwright` 4.11.0 (MPL-2.0), in `devDependencies`
di `frontend/package.json` con lo script `test:e2e`. `frontend/src/` non è
stato toccato.

## 1. Percorso della demo a due ruoli, da database vuoto

`frontend/e2e/percorso-demo.spec.ts`, con `frontend/playwright.config.ts`:
due server (backend su :8000 con il database dedicato `adflow_e2e` creato,
migrato e riempito dal seed da `e2e/prepara-backend.sh`; frontend Vite su
:5173), Chromium in headless, video e traccia richiesti, locale it-IT e
`Europe/Rome`.

Comando: da `frontend/`, `npx playwright test` (con `PLAYWRIGHT_CHROMIUM`
all'occorrenza, vedi §6). Esito: **1 passed in 19 s**.

Passi provati (i numeri sono quelli di converge §4, limiti dichiarati in §4):

1. **operatore**: accede e arriva su «Campagne da approvare»; l'elenco è
   vuoto («Nessuna campagna da approvare») — è il database appena creato;
2. **operatore**: elenco artigiani con la bottega del seed; storico AI vuoto;
3. **operatore**: esce (il pulsante «Esci» chiude la sessione e riporta ad
   Accesso);
4. **artigiano**: accede e arriva sull'Ingresso («Buongiorno, …», «Qui trovi
   che cosa ti chiede il consorzio…»);
5. **artigiano**: Campagne (vuote), Calendario settimanale, Archivio foto;
6. **artigiano**: una pagina dell'operatore (`/da-approvare`) non gli è
   accessibile e viene riportato indietro;
7. ogni pagina visitata passa da axe (WCAG 2.2 AA, tag `wcag2a/2aa/21a/21aa/22aa`).

Evidenza: `T4-106-traccia.zip` (traccia Playwright con screencast passo per
passo). Il video `.webm` separato non viene prodotto da questa versione di
Playwright su questa macchina (il browser è quello in cache, usato con
`executablePath`): lo screencast nella traccia è l'evidenza visiva equivalente.

## 2. Accessibilità (axe): 4 violazioni gravi (RL-035)

| Pagina | Violazioni | Dettaglio |
|---|---|---|
| Accesso → Campagne da approvare (operatore) | 0 | — |
| Elenco artigiani (operatore) | **1 seria** | `color-contrast` su 2 elementi |
| Storico AI (operatore) | 0 | — |
| Ingresso (artigiano) | **2 serie** | `color-contrast` su 7 elementi; `link-in-text-block` su 1 |
| Campagne (artigiano) | 0 | — |
| Calendario (artigiano) | **1 seria** | `color-contrast` su 7 elementi |
| Archivio foto (artigiano) | 0 | — |

Nessuna violazione critica; quattro **gravi** (contrasto dei colori e link
distinguibile solo dal colore), tutte nelle pagine dell'artigiano e
nell'elenco artigiani. I JSON completi stanno in
`docs/accettazione/report/T4-106-axe-*.json`; sono il rilievo **RL-035**
(media: toccano l'accessibilità AA del percorso della demo).

## 3. Contratto OpenAPI ↔ TypeScript

Generati i tipi con `npx openapi-typescript@7` dallo schema dell'app (il file
generato resta fuori dal repository), confrontati con le interfacce scritte a
mano in `frontend/src/api/*.ts`:

- **percorsi**: tutti i `/api/…` usati dal frontend esistono nello schema;
  nessun endpoint morto nel client;
- **tipi**: 34 interfacce hanno lo stesso nome di uno schema OpenAPI e, per
  tutte, i campi coincidono (**zero differenze**);
- 39 schemi non hanno un tipo omonimo nel frontend: sono corpi di richiesta e
  risposte costruite in linea o con nomi italiani diversi (es.
  `CampagnaSchema` ↔ tipi di `campagne.ts`), non un disallineamento.
- Resta vero quanto dice RL-027: gli errori (401/403/404/409) non sono
  dichiarati nello schema, quindi i tipi generati non li conoscono.

Nessun rilievo nuovo dal contratto: le differenze sono quelle già registrate
in RL-027.

## 4. Che cosa il percorso **non** copre

- I passi della demo che richiedono **file** (caricamento foto, invio,
  generazione, revisione, richiesta all'artigiano, approvazione, pubblicazione,
  interventi dopo l'approvazione): servono le fabbriche del backend per
  preparare una campagna, un upload vero e il worker; sono la parte più lunga
  di converge §4 e vanno aggiunti come test E2E separati nel piano di
  correzione (RL-036).
- **Controllo visivo** (passo 7 di converge §4): confronto a occhio con le
  pagine statiche — resta una prova a mano.
- **Test unitari delle pagine** (vitest + Testing Library): non ci sono (R-08);
  il vuoto è riempito solo dal percorso E2E qui sopra.
- **CI**: il percorso E2E non entra nei workflow (domanda 3: strumenti solo in
  locale).

## 5. Rilievo R-08 (→ RL-036)

R-08 diceva: «il frontend non ha test: gli script sono dev, build, lint,
preview». Dopo questo task c'è **un** percorso E2E verdone con axe, ma:
niente test unitari delle pagine, niente E2E completo della demo, niente E2E
nella CI. Il rischio è **confermato** come lacuna residua: RL-036.

## 6. Nota sull'ambiente

`npx playwright install` non funziona su questa macchina (Playwright 1.64 non
supporta l'Ubuntu 26.04 simulato) e i browser in cache sono di una build
diversa: il percorso usa `PLAYWRIGHT_CHROMIUM=/home/giova/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`
e un collegamento locale `ffmpeg-1013 → ffmpeg-1011` nella cache dei browser.
La configurazione legge la variabile e non contiene percorsi assoluti: su una
macchina con i browser ufficiali basta togliere la variabile.
