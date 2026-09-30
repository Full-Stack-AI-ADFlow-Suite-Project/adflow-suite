# SPEC-CODICE · AdFlow Suite

Regole tecniche vincolanti per chi scrive codice, persona o assistente AI. Le decisioni stanno in `docs/ADR.md`; flusso e architettura in `docs/architettura/`.

## 1. Regole di lavoro
1. **Leggere prima** questo file e `docs/ADR.md`. Non cambiare una decisione ADR senza aggiungere una nuova riga ADR.
2. **Uno sprint alla volta**: si implementa solo ciò che è nel backlog dello sprint corrente (§8).
3. **Ogni modifica passa i test**: `pytest` nel backend e `npm run build` nel frontend. Una nuova regola di business porta con sé il suo test.
4. **Database solo tramite migrazioni Alembic**: mai modifiche manuali allo schema.
5. **Segreti solo in `backend/.env`**, che non va mai in git. Il file `.env.example` va aggiornato a ogni nuova variabile.
6. **Commit piccoli**, messaggio in italiano all'imperativo, con prefisso: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`.

## 2. Struttura
```
adflow-suite/
├─ docs/            ADR.md · SPEC-CODICE.md · architettura/ (flusso v4.6, diagrammi, scheda bottega, pagina operatore artigiano, strumenti)
├─ backend/
│  ├─ app/
│  │  ├─ api/        router FastAPI: solo HTTP, permessi e conversione dati
│  │  ├─ services/   logica di business (generazione, revisione, pubblicazione, validatore)
│  │  ├─ adapters/   servizi esterni dietro interfacce: ai, social, archivio, prompts
│  │  ├─ worker/     Procrastinate: app, task (involucri sottili sui services), avvio
│  │  ├─ domain.py   valori ammessi e macchine a stati (unica fonte)
│  │  ├─ models.py   tabelle SQLAlchemy · schemas.py contratto API · config.py · db.py
│  │  ├─ coda.py     accodamento job dall'API · security.py · cli.py · main.py
│  ├─ alembic/      migrazioni
│  └─ tests/        pytest su PostgreSQL reale (database adflow_test)
└─ frontend/src/    api.ts (client + tipi) · auth.tsx · pages/ · components/
```
**Dipendenze ammesse:** `api → services → adapters`, e tutti possono usare `domain`/`models`. Nessuna logica di business nei router o nei task. Gli stati si cambiano solo con `verifica_transizione()`.

## 3. Convenzioni
- Nomi di dominio in **italiano** (tabelle, campi, funzioni); termini tecnici standard in inglese (`router`, `task`, `schema`).
- Python 3.11+, type hints ovunque, SQLAlchemy 2 (`Mapped`). Date salvate in UTC (`timestamptz`); il fuso Europe/Rome si usa solo per calcolare gli slot.
- Un solo formato di errore API: `{"detail": "messaggio in italiano"}`. Codici: 401 senza sessione, 403 ruolo, 404 non trovato o non tuo, 409 stato non valido, 422 dati non validi.
- Frontend: TypeScript strict, Mantine, niente librerie di stato globali; i tipi in `api.ts` rispecchiano `schemas.py`.

## 4. Modello dati (sprint 1, con le estensioni degli sprint 2a e 2b)
| Tabella | Campi principali | Note |
|---|---|---|
| utente | email (unica), password_hash (scrypt), nome, ruolo, attivo | ruoli: artigiano, operatore, admin |
| anagrafica_artigiano *(nuova, ADR-38)* | utente_id (1:1), codice (unico, es. ART-0042), codice_consorzio, nome_bottega, referente, citta, telefono, stato_iscrizione (attiva/sospesa), iscritto_il | scritta solo dall'operatore; dato ufficiale. Nome, referente e città restano anche in `profilo_bottega` (passo 1) |
| sessione | token_hash (sha256), utente_id, scade_il | ADR-05: il cookie contiene il token, il DB solo l'hash |
| profilo_bottega | utente_id (1:1), nome, tipo_prodotto, storia, tono, vincoli · **da sprint 2a:** referente, citta, anni_attivita, sito, origine, valori[], gamma, fascia_prezzo, stagionalita, clienti_ideali, obiettivo, zona, cortesia, canali[], frequenza, orari, social_esistenti (JSON `{canali[], profili, cosa_funziona}`), foto_policy (JSON `{quantita_mese, chi_scatta, persone}`), eventi_ricorrenti (JSON `[{nome, quando, tipo}]`), chiusure, aggiornato_il | ADR-21: esattamente i campi dei passi 1–9 della scheda bottega (`docs/architettura/AdFlow-scheda-bottega.html`). `storia` = "cosa fai"; `tono` diventa lista; `vincoli` = "cose da non dire mai" |
| campagna | profilo_id, titolo, inizio, fine, canale, stato · **da sprint 2a:** descrizione, canali[] (sostituisce canale), frequenza, obiettivo, profilo_snapshot (JSON), inviata_il · **da sprint 2b:** rimandata (bool), nuovi stati `respinta` e `scaduta` | ADR-19, ADR-23, ADR-24, ADR-25. canali/frequenza/obiettivo/snapshot si scrivono solo all'invio. `rimandata` si azzera all'approvazione (ADR-32) |
| decisione_campagna *(nuova, sprint 2b, ADR-37)* | campagna_id, utente_id, esito (approvata / rimandata / respinta), nota, creata_il | storico delle decisioni dell'operatore; la nota della respinta è la richiesta di modifica inviata all'artigiano (ADR-33) |
| notifica *(anticipata allo sprint 2b, ADR-37)* | utente_id, campagna_id, tipo, canale (email), stato_invio, creata_il, inviata_il | tipi dello sprint 2b: `campagna_respinta`, `campagna_scaduta`; gli altri dallo sprint 3 |
| foto | profilo_id, campagna_id, file, mime, descrizione, richieste, analisi_ai, n_utilizzi · **da sprint 2a:** gruppo_id (uuid), larghezza, altezza | ADR-22, ADR-28: descrizione uguale per tutte le foto del gruppo; `richieste` facoltativo |
| post | campagna_id, canale, data_ora, stato, n_rigenerazioni | versione corrente = ultima versione |
| versione_post | post_id, numero, testo, hashtag[], foto_id, autore, provider_ai, modello_ai, versione_prompt, errori_validazione | ADR-12: mai cancellata |
| approvazione | versione_id, utente_id, ruolo, esito | ADR-30: l'approvazione in blocco scrive una riga per la versione corrente di ogni post; ADR-36: una riga anche per ogni modifica in campagna attiva |
| pubblicazione | post_id, versione_id, n_tentativo, stato, id_esterno, errore | indice unico: un solo `ok` per post (ADR-13) |

Da aggiungere negli sprint successivi: account_social e anagrafica_artigiano (sprint 3), metrica (sprint 4).

**Vincoli di dominio (sprint 2a, in `domain.py` e nei servizi):** una sola campagna `bozza` per profilo; campagne non `annullata`/`conclusa`/`respinta`/`scaduta` dello stesso profilo con periodi non sovrapposti; `inizio ≥ oggi + ANTICIPO_MINIMO_GIORNI` (3, configurabile; ADR-35) alla creazione, alla modifica e all'invio; `fine > inizio`, durata ≤ 92 giorni. Migrazione: `canali = [canale]`, `tono = [tono]` se valorizzato, `profilo_snapshot` nullo per le campagne dello sprint 1.

**Stati (sprint 2b, in `domain.py`):**
| Entità | Stati e transizioni |
|---|---|
| campagna | bozza → inviata → in_generazione → in_revisione → **attiva** (approva, ADR-30) → conclusa (tutti i post pubblicati o falliti) · in_generazione → generazione_fallita → inviata (Riprova) · in_revisione → **respinta** (respingi, ADR-33) · inviata / in_generazione / generazione_fallita / in_revisione → **scaduta** (inizio raggiunto senza approvazione, ADR-34) · attiva ⇄ sospesa · attiva / sospesa → annullata |
| post | da_approvare (+ indicatore "da rivedere") → approvato (in blocco) → pubblicato / fallito · fallito → approvato (riprogrammato) · da_approvare → scaduto (solo con la campagna, ADR-34) · da_approvare → scartato (solo con la campagna respinta, ADR-33) |

**Valori ammessi (`domain.py`, dalle scelte della scheda):**
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

## 5. Contratto API (prefisso `/api`)
| Metodo e percorso | Ruolo | Esito |
|---|---|---|
| POST /auth/login `{email,password}` | tutti | 200 utente + cookie `adflow_sessione` httpOnly |
| POST /auth/logout · GET /auth/me | autenticato | 204 · 200 utente |
| GET /profilo | artigiano | 200 profilo bottega · 404 se non ancora compilato (ADR-15, ADR-16) |
| PUT /profilo `{...campi profilo_bottega...}` | artigiano | 200; crea o aggiorna (upsert), sempre lo stesso profilo per utente; 422 se manca un obbligatorio (ADR-21) |
| GET /campagne?stato= | autenticato | elenco (l'artigiano vede solo le sue); `?stato=bozza` per riprendere la bozza al rientro |
| POST /campagne `{titolo,inizio,fine,descrizione}` | artigiano | 201 campagna in bozza; 409 se c'è già una bozza o il periodo si sovrappone; 422 date non valide, inizio prima di oggi + 3 giorni (ADR-35) o durata oltre 3 mesi (ADR-25) |
| PATCH /campagne/{id} `{titolo,inizio,fine,descrizione}` | artigiano | 200; solo in bozza, stessi controlli |
| GET /campagne/{id} | proprietario o operatore | dettaglio con foto per gruppo e post (all'artigiano solo approvati/pubblicati/falliti); all'operatore anche `profilo_snapshot` (ADR-29) e storico delle decisioni; all'artigiano, se `respinta`, la nota della richiesta di modifica (ADR-33) |
| POST /campagne/{id}/foto (multipart: file, gruppo_id) | artigiano | 201; solo in bozza; JPG/PNG/WEBP ≤ 10 MB, lato corto ≥ 1080 px, altrimenti 422 (ADR-28) |
| PUT /campagne/{id}/gruppi/{gruppo_id} `{descrizione}` | artigiano | 200; copia la descrizione su tutte le foto del gruppo; solo in bozza (ADR-22) |
| DELETE /foto/{id} · DELETE /campagne/{id}/gruppi/{gruppo_id} | artigiano | 204; solo in bozza |
| GET /foto/{id}/file | proprietario o operatore | immagine |
| POST /campagne/{id}/invia | artigiano | bozza → inviata + job `genera_campagna`; copia canali, frequenza, obiettivo dal profilo e salva `profilo_snapshot` (ADR-23, ADR-24); 409 senza profilo; 422 senza foto, con un gruppo senza descrizione o con inizio prima di oggi + 3 giorni (ADR-35). Consentito anche senza account social (ADR-26) |
| POST /campagne/{id}/riprova | operatore | generazione_fallita → inviata + job `genera_campagna` (ADR-14) |
| GET /post?stato=&campagna_id= | operatore | elenco post con versione corrente (sprint 1); nello sprint 2b lo sostituisce `GET /campagne/{id}/post` |
| **Sprint 2b · revisione in blocco** | | |
| GET /campagne/{id}/post?stato= | operatore | pagina Vedi campagna (ADR-39): tutti i post in ogni stato, con data, canale e versione corrente; stessi dati per elenco e calendario |
| POST /campagne/{id}/approva | operatore | in_revisione → attiva; tutti i post → approvato, una riga `approvazione` per versione corrente, riga in `decisione_campagna` (ADR-30); 409 se un post è "da rivedere" o in rigenerazione (ADR-31) |
| POST /campagne/{id}/rimanda `{nota}` | operatore | resta in_revisione, `rimandata = true`, riga in `decisione_campagna`; nessuna email (ADR-32) |
| POST /campagne/{id}/respingi `{nota}` | operatore | in_revisione → respinta; post → scartato; riga in `decisione_campagna`; notifica `campagna_respinta` all'artigiano; 422 senza nota (ADR-33) |
| POST /campagne/{id}/sospendi · /riattiva · /annulla | operatore | attiva ⇄ sospesa; attiva o sospesa → annullata; 409 negli altri stati |
| POST /post/{id}/rigenera `{nota}` | operatore | solo con campagna in_revisione; nuova versione con job asincrono; max 3 (R-03) |
| PUT /post/{id} `{testo,hashtag,foto_id}` | operatore | nuova versione (ripassa la validazione); in_revisione resta da_approvare; in campagna attiva, post non ancora pubblicato, la versione è subito approvata (ADR-36) |
| ~~POST /post/{id}/approva · /scarta~~ | — | **eliminate nello sprint 2b** (ADR-30): erano dello sprint 1 |
| **Sprint 3 · pagine operatore** | | |
| GET /artigiani · GET /artigiani/{id} | operatore | elenco; dettaglio con anagrafica, profilo corrente (sola lettura), account social, bozza aperta e campagne raggruppate per sezione (ADR-39) |
| POST /artigiani · PUT /artigiani/{id}/anagrafica | operatore | crea utente artigiano + anagrafica; modifica l'anagrafica (ADR-38) |
| GET /health | tutti | `{"stato":"ok"}` |

Documentazione interattiva generata da FastAPI: `http://localhost:8000/docs`.

## 6. Job del worker
| Job | Quando | Cosa fa |
|---|---|---|
| `genera_campagna(campagna_id)` | accodato da /invia o /riprova; 3 esecuzioni in tutto, attesa 30 s | legge `profilo_snapshot` (mai il profilo corrente, ADR-24); analisi foto con la descrizione del gruppo; slot = min(frequenza × settimane, foto × usi massimi), canali alternati; eventi, chiusure e commenti della campagna nel prompt (ADR-27); 1 post per slot + validazione (max 3 tentativi) → in_revisione. Errore tecnico anche alla 3ª esecuzione → generazione_fallita (ADR-14) |
| `tick_pubblicazione` | ogni minuto, un solo tick alla volta | **da sprint 2b:** campagne non approvate con inizio raggiunto (00:00 Europe/Rome) → scaduta, post → scaduto, notifica all'artigiano (ADR-34); post approvati alla data → pubblicazione; campagna attiva con tutti i post pubblicati o falliti → conclusa; senza account social collegato → campagna sospesa (ADR-26). Non porta più la campagna in attiva (lo fa l'approvazione, ADR-30) né fa scadere i singoli post |
| `invia_notifica(notifica_id)` | accodato quando si crea una notifica (sprint 2b); 3 tentativi | invia l'email tramite l'adattatore (catcher locale in sviluppo) e aggiorna `stato_invio` (ADR-37) |
| `promemoria` | ogni ora (sprint 3) | email all'operatore per le campagne in_revisione che iniziano entro 48 h (ADR-34) |

## 7. Test (ADR-11)
- **Unitari:** validatore (incluse le "cose da non dire" del profilo), transizioni, calcolo degli slot (frequenza, canali alternati, limite delle foto), parsing della risposta AI.
- **Servizi:** generazione, pubblicazione (ok, errore temporaneo ×3, errore definitivo, tentativo in corso), scadenze, chiusura campagna.
- **API:** autenticazione, permessi, validazione input, flusso completo.
- **Scheda bottega (sprint 2a):** profilo 404 → PUT → GET; 422 per ogni obbligatorio mancante; seconda bozza e periodo sovrapposto → 409; foto con formato, peso o risoluzione non validi → 422; invio con gruppo senza descrizione → 422; lo snapshot resta uguale dopo una modifica del profilo; Riprova usa lo snapshot.
- **Anticipo minimo (sprint 2a, ADR-35):** inizio prima di oggi + 3 giorni → 422 su creazione, modifica e invio (anche per una bozza rimasta ferma).
- **Revisione in blocco (sprint 2b):** approva → tutti i post approvati e una riga `approvazione` per versione; approva con un post "da rivedere" → 409; rimanda non cambia stato; respingi senza nota → 422, con nota → post scartati e notifica creata; campagna non approvata all'inizio → scaduta con post scaduti (anche da generazione_fallita); una campagna respinta o scaduta non blocca il periodo; modifica in campagna attiva → versione approvata; rigenera in campagna attiva → 409; approva e scarta sul singolo post non esistono più.
- **Adattatore LiteLLM:** con risposta simulata, senza rete.
- **End-to-end:** uno solo, a fine progetto (browser → pubblicazione simulata).

## 8. Sprint
### Sprint 1 · Scheletro che cammina ✔
Obiettivo: un percorso completo e sottile, dal login alla pubblicazione simulata.

| Criterio di completamento | Stato |
|---|---|
| Login/logout con sessione e cookie; ruoli protetti | ✔ |
| Artigiano: crea campagna, carica foto con descrizione e richieste, invia | ✔ |
| Worker: genera 1 post per foto (AI finta o LiteLLM), validazione a regole | ✔ |
| Operatore: vede i post da approvare, accetta o scarta | ✔ |
| Scheduler: scadenze + pubblicazione simulata idempotente, campagna attiva/conclusa | ✔ |
| Test backend verdi; frontend compilato | ✔ |

Fuori dallo sprint 1: rigenera, modifica, storico versioni in interfaccia, profilo modificabile, calendario, notifiche email, metriche.

### Backlog
- **Sprint 2a · Scheda bottega:** pagina unica profilo + nuova campagna a partire da `docs/architettura/AdFlow-scheda-bottega.html` (ADR-15): `GET`/`PUT /profilo` e schermata Bentornato (ADR-16), campi del profilo e valori ammessi (ADR-21), eventi ricorrenti (ADR-18), bozza e suoi vincoli con anticipo minimo di 3 giorni (ADR-25, ADR-35), foto a gruppi (ADR-22, ADR-28), invio con copia dei dati e snapshot (ADR-23, ADR-24), migrazione dello schema.
- **Sprint 2b · Revisione in blocco:** pagina Vedi campagna in forma di elenco (ADR-39); approva / rimanda / respingi (ADR-30, 32, 33) con `decisione_campagna`; scadenza della campagna all'inizio (ADR-34); rigenera con nota (max 3, versioni rifiutate come contesto) e modifica manuale (ADR-31, ADR-36); storico e ripristino versioni; badge "da rivedere"; sospendi / riattiva / annulla; `notifica` + adattatore email con catcher locale per respinta e scadenza (ADR-37); messaggio della richiesta di modifica nel Bentornato. Sostituisce approva/scarta per post dello sprint 1.
- **Sprint 3 · Pagine operatore e affidabilità:** anagrafica artigiano (ADR-38), elenco artigiani e pagina artigiano (`docs/architettura/AdFlow-operatore-artigiano.html`), vista calendario dentro Vedi campagna, account social (simulato) con permesso scaduto, promemoria 48 h prima dell'inizio, email di riepilogo all'artigiano, più post per foto (max 2).
- **Sprint 4 · Monitoraggio e demo:** metriche simulate, pagina metriche operatore e dashboard artigiano, report settimanale, test end-to-end, dati demo, prova con OpenAI reale.
