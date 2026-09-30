# Tecnica · AdFlow Suite

Documento del **canale umano**: le scelte tecniche con le loro motivazioni, gli ambienti, i rischi. Il dettaglio normativo per gli agenti (modello dati, API, job) sta in `docs/agenti/plan.md`. Decisioni ufficiali in [`ADR.md`](ADR.md). Versione 4.7 del 30/09/2026.

Si parte **da zero** nel repository del team (ADR-45): ogni tabella nasce già nella sua forma definitiva, nello sprint indicato, senza migrazioni "di passaggio".

---

## 1. Stack e ambienti

![Stack e ambienti](architettura/diagrammi/08-stack-ambienti.png)

| Livello | Scelta | Note |
|---|---|---|
| Frontend | React + Vite, TypeScript, **Mantine** | SPA; in sviluppo Vite inoltra `/api` al backend |
| Backend API | Python 3.11+ · FastAPI · Pydantic | Documentazione interattiva su `http://localhost:8000/docs` |
| Worker e scheduler | Python + **Procrastinate**, stesso codice dell'API | Coda e job pianificati dentro PostgreSQL |
| Database | PostgreSQL 16 · SQLAlchemy 2 + Alembic | Migrazioni versionate |
| Archivio foto | Cartella locale → volume Docker | Dietro adattatore; storage a oggetti in roadmap |
| AI | LiteLLM, multi-provider | Primo provider reale: OpenAI; provider **finto** per sviluppo e test |
| Autenticazione | Sessione con cookie httpOnly | Ruoli: artigiano, operatore, admin; un solo consorzio |
| Social | Simulato + Meta | Simulato in fase 1 e in demo |
| Email | Catcher locale (es. Mailpit) → SMTP reale | Nessuna email vera durante lo sviluppo |
| Test | pytest su database `adflow_test`; 1 test end-to-end finale | ADR-11 |

| Fase | Come gira | Quando |
|---|---|---|
| **1 · Locale** | PostgreSQL installato; tre processi: API (`uvicorn`), worker, frontend (`vite dev`); foto in una cartella; chiavi in `.env`; social simulato | Sviluppo e demo |
| **2 · Docker su server proprio** | `docker compose` con frontend, api, worker, postgres; volumi per database e foto; backup giornaliero; reverse proxy con HTTPS | Quando il flusso funziona in locale |
| Roadmap | Cloud o PostgreSQL gestito, storage a oggetti, CI/CD | Dopo il progetto |

**Configurazione** (`backend/.env`, esempio in `.env.example`):
```
DATABASE_URL=postgresql+psycopg2://adflow:***@localhost:5432/adflow
DATABASE_URL_TEST=postgresql+psycopg2://adflow:***@localhost:5432/adflow_test
ARCHIVIO_FOTO_DIR=./archivio
AI_PROVIDER=finto                 # oppure litellm
AI_MODELLO_VISIONE=openai/<modello-con-visione>
AI_MODELLO_TESTO=openai/<modello-testo>
OPENAI_API_KEY=
ANTICIPO_MINIMO_GIORNI=3
MARGINE_SLOT_MINUTI=15
SMTP_HOST=localhost
SMTP_PORT=1025
```

### Scelte tecniche (motivazioni)

| ID | Decisione | Motivazione | Alternative scartate |
|---|---|---|---|
| D-A | **Monolite modulare + worker** | Semplice da spiegare e costruire, un solo deploy | Microservizi, serverless |
| D-B | **Coda dei job in PostgreSQL** | Nessun servizio in più, retry inclusi | Redis, cron + script |
| D-C1 | Backend e worker in **Python + FastAPI** | Ecosistema AI più ricco; un solo linguaggio lato server | Node/TypeScript, Next.js |
| D-C2 | Frontend **React + Vite** (TypeScript) | Il più diffuso, molte librerie per calendario e form | Angular, Vue |
| D-C3 | Fase 1 locale, fase 2 Docker su server proprio | Si parte senza infrastruttura | Cloud gestito (roadmap) |
| D-C4 | **AI multi-provider** da configurazione | Nessun vincolo a un fornitore; confronto qualità/costo | Provider fisso |
| D-C5 | Login con **sessione e cookie** httpOnly | Più semplice e sicuro per una SPA sullo stesso dominio; logout immediato | JWT, provider esterno |
| D-C6 | Multi-provider tramite **LiteLLM** dentro l'adattatore AI | Molti provider con la stessa sintassi | Interfaccia propria + SDK ufficiali |
| D-C7 | Primo provider reale: **OpenAI** | Testo + visione, documentazione ampia | Claude, Gemini, modello locale |
| D-C8 | **Un solo consorzio** | Schema e permessi più semplici | Multi-tenant |
| D-C9 | Coda e job pianificati con **Procrastinate** | Pronta su PostgreSQL: tentativi, job ogni minuto, lock | Tabella scritta da noi |
| D-C10 | Interfaccia con **Mantine** | Componenti pronti per form, card, notifiche | MUI, Tailwind + shadcn/ui |
| D-C11 | **Monorepo** `backend/`, `frontend/`, `docs/` | Una modifica, un commit; più semplice per 5 persone | Due repository |
| D-C12 | Test **unitari + API** su PostgreSQL reale; **un solo end-to-end** | Sicurezza veloce; l'E2E dimostra l'insieme | E2E per ogni funzione |

## 2. Architettura

![Architettura](architettura/diagrammi/05-architettura.png)

| Componente | Cosa fa | Con chi parla | Se si rompe |
|---|---|---|---|
| **Web App** | Viste per ruolo. Artigiano: scheda bottega + nuova campagna, calendario in lettura, metriche. Operatore: elenco artigiani, pagina artigiano, Vedi campagna (decisioni in blocco, motivi del No, interventi AI), metriche | Backend API | Nessuna azione possibile, ma le pubblicazioni continuano |
| **Backend API** | Moduli: autenticazione, utenti e ruoli, anagrafica, profili, campagne e bozze, foto a gruppi, post e versioni, decisioni sulla campagna, approvazioni, pubblicazioni, metriche, notifiche. All'invio copia canali/frequenza/obiettivo e salva `profilo_snapshot`. Mette i job in coda | DB, archivio, validatore, adattatori | L'app si ferma; il worker continua |
| **Worker** | Esegue i job (§5); quelli della campagna leggono `profilo_snapshot` | DB, archivio, validatore, adattatori | I job restano in coda: solo ritardo |
| **PostgreSQL** | Tutti i dati + coda dei job | API, worker | Tutto fermo: backup giornalieri |
| **Archivio foto** | Originali, ritocchi AI, ritagli | API, worker | Generazione e pubblicazione ferme |
| **Validatore** | Regole verificabili sui testi (lunghezza, hashtag, parole vietate, "cose da non dire", niente prezzi o premi inventati) | API, worker | Post "da rivedere", mai pubblicato senza controllo |
| **Adattatore AI** | `analizza_immagine()`, `ritocca_immagine()`, `genera_post()`; provider e modello da configurazione; prompt per tipo di prodotto, con versione | Provider AI | Nuovo tentativo, poi "da rivedere" o "generazione fallita" |
| **Adattatore social** | `collega_account()`, `pubblica()`, `leggi_metriche()`; implementazioni Meta e **simulata** | Social | Nuovo tentativo, "fallito" o "account da ricollegare" |
| **Adattatore email** | `invia()`; notifiche e report | Catcher locale / SMTP | Notifica salvata e reinviata |

## 3. Modello dati, API e job

Il dettaglio (tabelle, stati, valori ammessi, endpoint, job, con lo sprint in cui nasce ogni pezzo) sta in `docs/agenti/plan.md`. Qui resta la vista d'insieme:

![Schema dati](architettura/diagrammi/06-schema-dati.png)

## 4. Aderenza flusso → architettura

Metodo (diagramma 02): si disegna il flusso, se ne ricava l'architettura, si verifica che **ogni passo abbia un componente** e che **ogni componente serva a un passo**. Ogni buco corregge l'uno o l'altra; le sette iterazioni fatte finora sono nel diagramma.

![Ciclo iterativo](architettura/diagrammi/02-ciclo-flusso-architettura.png)

| Passo (spec) | Componenti | Entità |
|---|---|---|
| 1.0 Accesso | Web App, API | utente, sessione, profilo_bottega |
| 1.1–1.1b Profilo e Bentornato | Web App, API | profilo_bottega, decisione_campagna (ultima respinta) |
| 1.2 Account social | API, adattatore social | account_social |
| 1.3–1.5 Bozza e foto | Web App, API, archivio | campagna, foto |
| 1.6 Invio | API, worker (coda) | campagna (`profilo_snapshot`) |
| 2.1–2.1b Analisi e ritocco | worker, adattatore AI, archivio | foto, versione_foto |
| 2.2–2.4 Calendario, post, controllo | worker, adattatore AI, validatore | post, versione_post |
| 2.5 Campagna pronta | worker, adattatore email | notifica |
| 3.1 Dashboard operatore | Web App, API | anagrafica_artigiano, campagna |
| 3.2–3.3 Vedi campagna e interventi | Web App, API, worker, validatore, adattatore AI | post, versione_post, versione_foto |
| 3.4 Decisione | Web App, API, adattatore email | decisione_campagna, approvazione, notifica |
| 3.5 Promemoria e scadenza | worker, adattatore email | campagna, post, notifica |
| 3.6 Sospendi / annulla | Web App, API | campagna |
| 4.1–4.4 Pubblicazione | worker, adattatore social, adattatore email | pubblicazione, account_social |
| 4.5 Metriche e report | worker, adattatore social, Web App | metrica |

## 5. Rischi tecnici

1. **Testi AI ripetitivi** → prompt per tipo di prodotto, versioni rifiutate come contesto, validatore.
2. **Collo di bottiglia dell'operatore** (20 artigiani × 12 post = 240 post al mese) → approvazione in blocco, anticipo di 3 giorni; misurare nella demo il tempo di revisione per campagna.
3. **Costo delle chiamate AI** (analisi e ritocco foto, rigenerazioni) → cicli 3 + 3, stima dei costi, confronto tra provider.
4. **Troppo lavoro per 6 settimane** → la demo copre le fasi 1→3 e simula la pubblicazione; se il tempo stringe si tagliano i campi facoltativi della scheda, mai gli obbligatori.
5. **Multi-provider che si allarga** → nell'MVP due implementazioni: un provider reale e uno finto.
6. **"Funziona sul mio PC"** → versioni fissate (Python, Node, PostgreSQL), `.env.example`, istruzioni di avvio nel README; una sola persona non deve essere l'unica a saper avviare il progetto.
7. **Lavoro in parallelo di più persone** → task piccoli con dipendenze esplicite, un branch per task, `domain.py` e `models.py` toccati da un task alla volta (vedi `docs/agenti/tasks.md`).

## 6. Punti tecnici da verificare

- LiteLLM: supporto delle immagini per i modelli OpenAI scelti; formato dei nomi dei modelli.
- Modelli OpenAI per visione, testo e **ritocco immagini**, con costi (lavori.md A-01).
- Modello locale: solo se serve davvero; l'hardware deve reggere la visione.
- Catcher email per lo sviluppo (proposta: Mailpit).
- Libreria per la vista calendario (sprint 3, lavori.md A-03).
- Server proprio: dominio e certificato HTTPS per l'OAuth dei social.
