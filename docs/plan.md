# Plan · AdFlow Suite

**Come** costruiamo ciò che descrive [`spec.md`](spec.md). Le regole che non si discutono stanno in [`constitution.md`](constitution.md); le decisioni con data e stato in [`ADR.md`](ADR.md). Versione 4.7 del 30/09/2026.

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

## 3. Modello dati

![Schema dati](architettura/diagrammi/06-schema-dati.png)

| Tabella | Campi | Sprint | Note |
|---|---|---|---|
| utente | email (unica), password_hash (scrypt), nome, ruolo, attivo | 1 | ruoli: artigiano, operatore, admin |
| sessione | token_hash (sha256), utente_id, scade_il | 1 | il cookie contiene il token, il DB solo l'hash (ADR-05) |
| profilo_bottega | utente_id (1:1), nome, referente, citta, anni_attivita, sito, storia, origine, valori[], tipo_prodotto, gamma, fascia_prezzo, stagionalita, clienti_ideali, obiettivo, zona, tono[], cortesia, vincoli, canali[], frequenza, orari, social_esistenti (JSON `{canali[], profili, cosa_funziona}`), foto_policy (JSON `{quantita_mese, chi_scatta, persone}`), eventi_ricorrenti (JSON `[{nome, quando, tipo}]`), chiusure, aggiornato_il | 1 (schermate nel 2a) | esattamente i campi dei passi 1–9 (ADR-21). `storia` = "cosa fai"; `vincoli` = "cose da non dire mai". Nello sprint 1 lo riempie il seed |
| campagna | profilo_id, titolo, inizio, fine, descrizione, stato, canali[], frequenza, obiettivo, profilo_snapshot (JSON), rimandata (bool), inviata_il | 1 | canali/frequenza/obiettivo/snapshot si scrivono solo all'invio (ADR-23, ADR-24). `rimandata` si azzera all'approvazione |
| foto | profilo_id, campagna_id, gruppo_id (uuid), file, mime, larghezza, altezza, descrizione, analisi_ai, n_utilizzi | 1 | descrizione uguale per tutto il gruppo (ADR-22); controllo tecnico ADR-28 |
| post | campagna_id, canale, data_ora, stato, da_rivedere (bool), n_rigenerazioni_testo · **sprint 3:** n_ritocchi_foto | 1 | versione corrente = ultima versione; max 3 per contatore (ADR-43) |
| versione_post | post_id, numero, testo, hashtag[], foto_id, tipo_intervento (generazione / rigenera_totale / rigenera_da_proposta), testo_proposto, nota, provider_ai, modello_ai, versione_prompt, errori_validazione, creata_il · **sprint 3:** versione_foto_id; tipo_intervento anche ritocco_foto / scelta_foto | 1 | mai cancellata (ADR-12); ogni intervento crea una nuova versione (ADR-42) |
| decisione_campagna | campagna_id, utente_id, esito (approvata / rimandata / respinta), motivo (foto / altro), nota, foto_segnate[], creata_il | 1 (solo `approvata`); 2b il resto | storico delle decisioni; motivo, nota e foto segnate vanno all'artigiano (ADR-37, ADR-40) |
| approvazione | versione_id, utente_id, ruolo, esito, creata_il | 1 | l'approvazione in blocco scrive una riga per la versione corrente di ogni post (ADR-30) |
| pubblicazione | post_id, versione_id, n_tentativo, stato (in_corso / ok / errore), id_esterno, errore, creata_il | 1 | indice unico parziale: un solo `ok` per post (ADR-13) |
| notifica | utente_id, campagna_id, tipo, canale (email), stato_invio, creata_il, inviata_il | 2b | tipi 2b: `campagna_respinta`, `campagna_scaduta`; altri dal 3 |
| versione_foto | foto_id, numero, file, origine (originale / ritocco_ai), nota, provider_ai, modello_ai, versione_prompt, creata_il | 3 | numero 0 = originale, sempre conservato (ADR-41) |
| anagrafica_artigiano | utente_id (1:1), codice (unico, es. ART-0042), codice_consorzio, nome_bottega, referente, citta, telefono, stato_iscrizione (attiva / sospesa), iscritto_il | 3 | scritta solo dall'operatore (ADR-38) |
| account_social | profilo_id, piattaforma, id_pagina, permesso (cifrato), scadenza, stato | 3 | simulato in fase 1 |
| metrica | pubblicazione_id, data_rilevazione, like, commenti, copertura, salvataggi | 4 | una riga per giorno |

**Tabelle tecniche:** `procrastinate_*` (coda dei job, gestite dalla libreria).

**Vincoli di dominio** (in `domain.py` e nei servizi): una sola campagna `bozza` per profilo; campagne non `annullata` / `conclusa` / `respinta` / `scaduta` dello stesso profilo con periodi non sovrapposti; `inizio ≥ oggi + ANTICIPO_MINIMO_GIORNI` alla creazione, alla modifica e all'invio; `fine > inizio`; durata ≤ 92 giorni; `n_rigenerazioni_testo ≤ 3`, `n_ritocchi_foto ≤ 3`; una foto in al massimo 2 post.

**Stati e transizioni** (in `domain.py`, cambiati solo da `verifica_transizione()`):
| Entità | Transizioni |
|---|---|
| campagna | bozza → inviata → in_generazione → in_revisione → attiva → conclusa · in_generazione → generazione_fallita → inviata · in_revisione → respinta · inviata / in_generazione / generazione_fallita / in_revisione → scaduta · attiva ⇄ sospesa · attiva / sospesa → annullata |
| post | da_approvare → approvato → pubblicato / fallito · fallito → approvato · da_approvare → scaduto · da_approvare → scartato |

**Valori ammessi** (`domain.py`, dalle scelte della scheda):
| Campo | Valori |
|---|---|
| tipo_prodotto | legno_mobili, ceramica_vetro, gioielli_metalli, tessile_pelle, alimentare, altro |
| valori[] | artigianalita, sostenibilita, tradizione, innovazione, territorio, su_misura |
| fascia_prezzo | accessibile, media, alta |
| obiettivo | vendere, negozio, notorieta, fidelizzare |
| tono[] | caldo, elegante, diretto, ironico, professionale |
| cortesia | tu, lei, dipende |
| canali[] (pubblicazione) | facebook, instagram (almeno uno) |
| frequenza → post/settimana | f1_2 → 2, f3_4 → 3, f5_piu → 5, decidete_voi → 3 (configurabile) |
| social_esistenti.canali[] | facebook, instagram, nessuno |
| foto_policy | quantita_mese: meno_5, da5_a12, da12_a20, oltre_20 · chi_scatta: artigiano, fotografo, consorzio · persone: mai, con_consenso, spesso |
| eventi_ricorrenti[].tipo | fiera_mercatino, festivita, lancio_prodotto, promozione, chiusura, altro |
| decisione_campagna.motivo | foto, altro |
| versione_post.tipo_intervento | generazione, rigenera_totale, rigenera_da_proposta, ritocco_foto, scelta_foto |

## 4. Contratto API (prefisso `/api`)

Errori sempre `{"detail": "..."}`: 401 senza sessione, 403 ruolo, 404 non trovato o non tuo, 409 stato non valido, 422 dati non validi.

| Metodo e percorso | Ruolo | Esito | Sprint |
|---|---|---|---|
| GET /health | tutti | `{"stato":"ok"}` | 1 |
| POST /auth/login `{email,password}` | tutti | 200 utente + cookie `adflow_sessione` httpOnly; 401 credenziali errate | 1 |
| POST /auth/logout · GET /auth/me | autenticato | 204 · 200 utente | 1 |
| GET /campagne?stato= | autenticato | elenco (l'artigiano vede solo le sue); `?stato=bozza` per riprendere la bozza | 1 |
| POST /campagne `{titolo,inizio,fine,descrizione}` | artigiano | 201 bozza; 409 bozza già presente o periodo sovrapposto; 422 date, anticipo o durata non validi | 1 |
| GET /campagne/{id} | proprietario o operatore | dettaglio con foto per gruppo; all'artigiano solo post approvati/pubblicati/falliti; all'operatore anche `profilo_snapshot` e decisioni; all'artigiano, se respinta, motivo, nota e foto segnate | 1 (decisioni e respinta dal 2b) |
| POST /campagne/{id}/foto (multipart: file, gruppo_id) | artigiano | 201; solo in bozza; JPG/PNG/WEBP ≤ 10 MB, lato corto ≥ 1080 px, altrimenti 422 | 1 |
| PUT /campagne/{id}/gruppi/{gruppo_id} `{descrizione}` | artigiano | 200; copia la descrizione su tutte le foto del gruppo; solo in bozza | 1 |
| DELETE /foto/{id} · DELETE /campagne/{id}/gruppi/{gruppo_id} | artigiano | 204; solo in bozza | 1 |
| GET /foto/{id}/file | proprietario o operatore | immagine | 1 |
| POST /campagne/{id}/invia | artigiano | bozza → inviata + job `genera_campagna`; copia canali, frequenza, obiettivo e salva `profilo_snapshot`; 409 senza profilo; 422 senza foto, gruppo senza descrizione o anticipo non rispettato | 1 |
| POST /campagne/{id}/riprova | operatore | generazione_fallita → inviata + job `genera_campagna` | 1 |
| GET /campagne/{id}/post?stato= | operatore | Vedi campagna: tutti i post con data, canale, versione corrente e storico | 1 |
| POST /campagne/{id}/approva | operatore | in_revisione → attiva; post → approvato; riga `approvazione` per versione corrente; riga `decisione_campagna`; 409 con post "da rivedere" o intervento in corso | 1 |
| GET /profilo | artigiano | 200 profilo · 404 se non compilato | 2a |
| PUT /profilo `{...}` | artigiano | 200 upsert; 422 se manca un obbligatorio | 2a |
| PATCH /campagne/{id} `{titolo,inizio,fine,descrizione}` | artigiano | 200; solo in bozza, stessi controlli della creazione | 2a |
| POST /campagne/{id}/rimanda `{nota}` | operatore | resta in_revisione, `rimandata = true`, riga in `decisione_campagna`; nessuna email | 2b |
| POST /campagne/{id}/respingi `{motivo, nota, foto_segnate[]}` | operatore | in_revisione → respinta; post → scartato; decisione; notifica `campagna_respinta`; 422 senza motivo o nota, o con foto di un'altra campagna | 2b |
| POST /campagne/{id}/sospendi · /riattiva · /annulla | operatore | attiva ⇄ sospesa; attiva o sospesa → annullata; 409 negli altri stati | 2b |
| POST /post/{id}/rigenera `{modalita, testo_proposto, nota}` | operatore | solo in_revisione; `totale` o `da_proposta` (con `testo_proposto`), stessa foto; job asincrono; 409 oltre 3 o in altri stati; 422 `da_proposta` senza testo | 2b |
| GET /artigiani · GET /artigiani/{id} | operatore | elenco; dettaglio con anagrafica, profilo (sola lettura), account social, bozza, campagne per sezione | 3 |
| POST /artigiani · PUT /artigiani/{id}/anagrafica | operatore | crea utente artigiano + anagrafica; modifica anagrafica | 3 |
| POST /artigiani/{id}/social/{piattaforma}/collega | operatore | collega (simulato in fase 1) o ricollega l'account | 3 |
| POST /post/{id}/ritocca-foto `{nota}` | operatore | solo in_revisione; job asincrono: nuova `versione_foto` e nuova versione del post, solo per quel post; 409 oltre 3 | 3 |
| POST /post/{id}/scegli-foto `{versione_foto_id}` | operatore | solo in_revisione; originale o versione precedente; nuova versione del post; non consuma cicli | 3 |
| GET /metriche?artigiano=&campagna= | operatore; artigiano (solo le sue) | metriche per post e per periodo | 4 |

Non esistono (per scelta): modifica a mano di un post, approvazione o scarto del singolo post (ADR-30, ADR-42).

## 5. Job del worker

| Job | Quando | Cosa fa | Sprint |
|---|---|---|---|
| `genera_campagna(campagna_id)` | accodato da /invia o /riprova; 3 esecuzioni, attesa 30 s | legge `profilo_snapshot`; analizza le foto; **dallo sprint 3** le ritocca (`versione_foto` 1); slot = min(frequenza × settimane, foto × 2), canali alternati, niente slot nel passato; eventi, chiusure e commenti nel prompt; 1 post per slot + validazione (max 3 riscritture, poi `da_rivedere`) → in_revisione. Errore tecnico anche alla 3ª → generazione_fallita | 1 |
| `tick_pubblicazione` | ogni minuto, un tick alla volta | post approvati alla data → registra il tentativo, pubblica, esito; campagna attiva con tutti i post pubblicati o falliti → conclusa. **Dal 2b:** campagne non approvate all'inizio (00:00 Europe/Rome) → scaduta. **Dal 3:** senza account collegato o con permesso scaduto → sospesa | 1 |
| `rigenera_post(post_id)` | accodato da /rigenera; 3 esecuzioni | nuovo testo con la stessa foto, da zero o dal testo proposto con la nota; versioni rifiutate come contesto; validazione | 2b |
| `invia_notifica(notifica_id)` | alla creazione di una notifica; 3 tentativi | email tramite adattatore; aggiorna `stato_invio` | 2b |
| `ritocca_foto(post_id)` | accodato da /ritocca-foto; 3 esecuzioni | nuovo ritocco con la nota; nuova `versione_foto` e nuova versione del post | 3 |
| `promemoria` | ogni ora | email all'operatore per le campagne in revisione che iniziano entro 48 h (una volta sola) | 3 |
| `raccogli_metriche` | ogni giorno | legge le metriche dei post pubblicati | 4 |
| `report_settimanale` | ogni settimana | email di riepilogo | 4 |

## 6. Aderenza flusso → architettura

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

## 7. Rischi tecnici

1. **Testi AI ripetitivi** → prompt per tipo di prodotto, versioni rifiutate come contesto, validatore.
2. **Collo di bottiglia dell'operatore** (20 artigiani × 12 post = 240 post al mese) → approvazione in blocco, anticipo di 3 giorni; misurare nella demo il tempo di revisione per campagna.
3. **Costo delle chiamate AI** (analisi e ritocco foto, rigenerazioni) → cicli 3 + 3, stima dei costi, confronto tra provider.
4. **Troppo lavoro per 6 settimane** → la demo copre le fasi 1→3 e simula la pubblicazione; se il tempo stringe si tagliano i campi facoltativi della scheda, mai gli obbligatori.
5. **Multi-provider che si allarga** → nell'MVP due implementazioni: un provider reale e uno finto.
6. **"Funziona sul mio PC"** → versioni fissate (Python, Node, PostgreSQL), `.env.example`, istruzioni di avvio nel README; una sola persona non deve essere l'unica a saper avviare il progetto.
7. **Lavoro in parallelo di più persone** → task piccoli con dipendenze esplicite, un branch per task, `domain.py` e `models.py` toccati da un task alla volta (vedi tasks.md).

## 8. Punti tecnici da verificare

- LiteLLM: supporto delle immagini per i modelli OpenAI scelti; formato dei nomi dei modelli.
- Modelli OpenAI per visione, testo e **ritocco immagini**, con costi (tasks.md A-01).
- Modello locale: solo se serve davvero; l'hardware deve reggere la visione.
- Catcher email per lo sviluppo (proposta: Mailpit).
- Libreria per la vista calendario (sprint 3, tasks.md A-03).
- Server proprio: dominio e certificato HTTPS per l'OAuth dei social.
