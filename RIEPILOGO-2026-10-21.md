# Riepilogo modifiche — 21 ottobre 2026

Branch: `feature/artigiani-elenco-operatore` (unico branch usato oggi; basato su
`origin/main` al merge PR #133). I tre commit di oggi — restyling, feature
artigiani e rifinitura — sono tutti qui dentro. Il branch locale
`feature/prototipo-stile`, dove il restyling era iniziato non committato, è
rimasto indietro e **non contiene** il lavoro: tutto è sul branch corrente.

Due aree di lavoro: il **restyling dell'interfaccia** e la **feature "elenco +
scheda artigiani per l'operatore"** (richiesta dal docente, era marcata Roadmap
in `perimetro-mvp.md`).

---

## 1. Commit `c50b558` — Restyling interfaccia (pushato)

`feat: restyling interfaccia con verde scuro, login split-screen e testi professionali`
— 33 file, +3190 / −1490 righe.

### Aggiunto

- `frontend/src/pages/Accesso.module.css` — stili della login split-screen.
- `frontend/src/pages/artigiano/profilo/Profilo.module.css` — stili del wizard profilo.
- `frontend/src/pages/artigiano/campagna/Passo10.module.css` — stili del riepilogo campagna.
- `frontend/src/components/IconaCanale.tsx` — badge/icone dei canali social (Facebook, Instagram).
- `frontend/src/components/LogoAdFlow.tsx` — logo riusabile.
- Token di design in `frontend/src/index.css`: `--primary #007974`, `--focus-ring #258b86`,
  `--bg-app #f2f8f8`, superfici chiare `#d9f5f3` / `#e3f4f3`, hairline, ombre, larghezza sidebar.
- Tipografia: **Inter** per il corpo, **Space Grotesk** per i titoli, **JetBrains Mono** per codici e orari.
- Favicon verde (`frontend/public/favicon.svg`) e titolo pagina in `frontend/index.html`.

### Modificato

- **Login** (`Accesso.tsx`): split-screen con foto di ceramiche artigianali calde,
  titolo "La comunicazione social della tua bottega, curata insieme al consorzio.",
  badge in vetro scuro, checkbox "Ricordami su questo dispositivo". Gradiente ribaltato:
  trasparente sopra (foto libera), scuro in basso (testo leggibile).
- **Palette**: ritorno al verde scuro `#007974` su pulsanti, logo, indicatori di passo e
  sidebar (dopo l'esperimento con il verde brillante `#00b496`).
- `Guscio.module.css` — sidebar scura con accenti verdi.
- `tema.ts` — tema Mantine allineato ai nuovi token.
- Wizard profilo (`Profilo.tsx`), campagna (`Passo10/11/12`, `Bentornato`, `Bozza`, `Riga`),
  pagine operatore (`DaApprovare`, `VediCampagna`, `Materiali`, `PianoCard`, `PostCard`,
  `RigaCampagna`) — stesso linguaggio visivo: card bianche, hairline, badge, tipografia.
- `CalendarioCampagnaView.tsx` — coerenza visiva + fix del bug di stato residuo (§4).
- `docs/pagine/` (mockup statici e `assets/adflow.css`) allineate al nuovo stile.

---

## 2. Commit `87aca71` — Elenco e scheda artigiani per l'operatore (pushato)

`feat: elenco e scheda artigiani per l'operatore` — 13 file, +1642 / −70 righe.

### Backend (modulo `revisione`, confini fra moduli rispettati)

- `GET /api/artigiani` — tutte le botteghe: account, profilo, canali collegati,
  conteggi campagne (da approvare / in corso / chiuse), prossima scadenza e id campagna.
  Ordinato per urgenza; include anche account inattivi e senza profilo.
- `GET /api/artigiani/{utente_id}` — scheda a sezioni: account, profilo read-only,
  canali, bozza, da approvare, in corso, ultime 3 chiuse + `totale_chiuse`.
  404 se l'id non esiste o non è un artigiano.
- Entrambi protetti da `richiede_ruolo("operatore")` (admin incluso, R-29).
- `accesso.service.artigiani(db)` — nuova funzione di lettura nel modulo proprietario
  della tabella `utente`, documentata in `docs/agenti/plan.md` §6.
- Schemi di risposta in `revisione/schemas.py`.
- File: `letture.py` (funzioni di lettura), `router.py` (rotte), `schemas.py`,
  `accesso/service.py`, `plan.md`.

### Frontend

- `frontend/src/pages/operatore/Artigiani.tsx` — **nuova landing dell'operatore** `/artigiani`:
  4 KPI, ricerca, tabella scrollabile con nomi cliccabili.
- `frontend/src/pages/operatore/Artigiano.tsx` — scheda `/artigiani/:id`: anagrafica,
  canali, campagne (da approvare e in corso in cima, ultime chiuse sotto), profilo read-only.
- `frontend/src/api/artigiani.ts` — tipi + `elencoArtigiani()` + `schedaArtigiano()`.
- `frontend/src/api/esempi/artigiani.ts` — dati finti per la modalità anteprima.
- `App.tsx` — rotte `/artigiani` e `/artigiani/:id`.
- `contesto-auth.ts` — redirect post-login dell'operatore → `/artigiani`.
- `Guscio.tsx` — voce "Artigiani" nella sidebar operatore.

### Test

- `backend/tests/moduli/revisione/test_artigiani.py` — 5 test: ordinamento elenco,
  situazione campagne, sezioni scheda, profilo mancante, 404 e permessi per ruolo.

---

## 3. Modifiche non committate (restyling pagine operatore, post-push)

- `frontend/src/pages/operatore/Artigiani.module.css` (**nuovo**, 291 righe) —
  tutto lo stile della lista.
- `Artigiani.tsx` e `Artigiano.tsx` riscritti con il nuovo sistema visivo:

### Cosa è cambiato nella lista `/artigiani`

- KPI veri: chip icona 42px in verde chiaro, numero grande 30px in Space Grotesk.
- Le card "Con campagne da approvare" e "Profilo da compilare" diventano **ambra**
  quando il valore è > 0 (ambra = serve azione, verde = ok).
- Tabella dentro un pannello-card: header sticky maiuscolo, righe hairline,
  hover `#f2f8f8` (niente più azzurrino fisso sulle righe).
- **Riga intera cliccabile** (anche `Enter` da tastiera) → scheda artigiano.
- Badge "Profilo compilato" grigio neutro; contatori numerici a pill.
- **Barra di ricerca spostata dentro il pannello-tabella**: ricerca + conteggio
  "N di M botteghe" a sinistra, pulsante "Nuovo artigiano" a destra.
- Nome bottega in Space Grotesk, verde in hover.

### Scheda `/artigiani/:id`

- Stesso sistema visivo (badge di stato colorati per semantica, tabelle card-style).
- Larghezza riportata da 1100 allo standard **1040** delle pagine artigiano.

---

## 4. Bug riscontrati e risolti

| Bug | Causa | Risoluzione |
|---|---|---|
| `GET /api/artigiani` rispondeva **405** | Vecchio processo uvicorn `--reload` rimasto orfano serviva codice senza la nuova rotta | Terminato l'albero del processo (`taskkill /T`) e riavviato server pulito su :8000 → 401 corretto senza sessione |
| Screenshot "identico a prima" dopo il restyling | Modifiche in sospeso + `</>` orfano nel JSX che rompeva la compilazione | Rimosso il fragment residuo; verificato con `curl` sul dev server che il markup servito contiene le classi nuove |
| `oxlint` segnalava 1 errore JSX | `</>` orfano dopo lo spostamento della toolbar dentro la card | Rimosso → 0 errori |
| `black --check` falliva con `module 'ast' has no attribute 'Str'` | Black 23.3.0 incompatibile con Python 3.14 | Usato l'ambiente Black pinnato del progetto → 214 file puliti, formattati `letture.py` e `test_artigiani.py` |
| `test_elenco_artigiani_con_situazione_campagne` falliva | Il DB di test persistente conteneva un artigiano residuo di run precedenti (id extra `[…, 333]`) | Il test ora filtra le righe per i soli id creati nel test → 5/5 verdi |
| Test proxy TLS fallito `[WinError 10053]` | Flaky ambientale sotto carico della suite | Rerun isolato → verde |
| `test_elenco_eventi_calendario` → 429 | Contatore `limite_login` saturo dai login reali dei test precedenti | Pulite le righe residue → 32/32 verdi |
| Import di `models` di un altro modulo in `letture.py` | Vietato dalla costituzione (`test_confini`) | Rimosso: solo `service`/`schemas` altrui |
| Campi scheda non corrispondenti allo schema | Frontend usava nomi inventati | Allineati a `ProfiloArtigiano` reale (`nome`, `obiettivo`, `orari`, `eventi_ricorrenti`…) |
| `React.ReactNode` senza import | Uso del namespace senza `import React` | Sostituito con `import { type ReactNode }` |
| Errore nel test: doppia `profilo()` per lo stesso utente | Violava l'unique su `utente_id` | Creata una sola volta |
| Bug calendario: dati della campagna precedente visibili dopo il cambio | Stato non resettato al cambio `campagna_id` | Reset dei dati/errori quando cambia la campagna (`CalendarioCampagnaView.tsx`) |
| Scheda artigiano troppo larga | `largo={1100}` | Rimosso il prop → default 1040 come le pagine artigiano |
| `.nota` in `Artigiani.module.css` mai usata | Residuo di una versione precedente | Rimossa |

---

## 5. Stato delle verifiche

- `uv run pytest` — **1833 passati** (gli unici fallimenti erano i flaky ambientali sopra, tutti verdi in isolato).
- `uv run black --check .` — pulito.
- `npm run build` (`tsc -b && vite build`) — ok (solo il warning chunk > 500 kB, preesistente).
- `npm run lint` (`oxlint`) — 0 warning, 0 errori.

## 6. Da fare / note aperte

- Le modifiche del §3 non sono ancora committate.
- `backend/security-assessment-logs/` è untracked e non è stato toccato.
- Dalla nota del docente resta fuori l'**Archivio foto** come pagina condivisa
  (oggi l'endpoint `GET /archivio` esiste ma è congelato per l'MVP, ADR-114).
