# Plan · come è fatto

Ogni tabella nasce già nella forma definitiva, nello sprint indicato. Cartelle e regole dei moduli: `constitution.md` §2. Vincoli: regole R-xx di `spec.md` §5.

## 1. Stack e configurazione
Python 3.11+ · FastAPI · Pydantic · SQLAlchemy 2 + Alembic · PostgreSQL 16 · Procrastinate (coda e job in PostgreSQL) · LiteLLM (AI; primo provider OpenAI; provider `finto` per sviluppo e test) · React + Vite + TypeScript + Mantine · pytest. Social simulato; email verso un catcher locale (Mailpit). Sessione con cookie httpOnly.

`backend/.env`:
```
DATABASE_URL · DATABASE_URL_TEST · ARCHIVIO_FOTO_DIR
AI_PROVIDER=finto|litellm · AI_MODELLO_VISIONE · AI_MODELLO_TESTO · OPENAI_API_KEY
ANTICIPO_MINIMO_GIORNI=3 · MARGINE_SLOT_MINUTI=15 · SMTP_HOST · SMTP_PORT
```

## 2. Modello dati
| Tabella | Modulo | Campi | Sprint |
|---|---|---|---|
| utente | accesso | email (unica), password_hash, nome, ruolo (artigiano / operatore / admin), attivo | 1 |
| sessione | accesso | token_hash (sha256), utente_id, scade_il | 1 |
| profilo_bottega | artigiani | utente_id (1:1), nome, referente, citta, anni_attivita, sito, storia, origine, valori[], tipo_prodotto, gamma, fascia_prezzo, stagionalita, clienti_ideali, obiettivo, zona, tono[], cortesia, vincoli, canali[], frequenza, orari, social_esistenti (JSON `{canali[], profili, cosa_funziona}`), foto_policy (JSON `{quantita_mese, chi_scatta, persone}`), eventi_ricorrenti (JSON `[{nome, quando, tipo}]`), chiusure, aggiornato_il · obbligatori: nome, referente, citta, tipo_prodotto, clienti_ideali, obiettivo, canali | 1 (seed; schermate 2a) |
| campagna | campagne | profilo_id, titolo, inizio, fine, descrizione, crea_immagini_ai (bool, default false), stato, canali[], frequenza, obiettivo, profilo_snapshot (JSON), rimandata (bool), inviata_il | 1 |
| foto | campagne | profilo_id, campagna_id, gruppo_id (uuid), origine (default `caricata`), file, mime, larghezza, altezza, descrizione, analisi_ai, n_utilizzi | 1 |
| decisione_campagna | campagne | campagna_id, utente_id, esito, motivo, nota, foto_segnate[], creata_il | 1 (solo `approvata`), 2b |
| post | contenuti | campagna_id, canale, data_ora, stato, da_rivedere (bool), n_rigenerazioni_testo · n_ritocchi_foto (3) | 1 |
| versione_post | contenuti | post_id, numero, testo, hashtag[], foto_id, tipo_intervento, testo_proposto, nota, provider_ai, modello_ai, versione_prompt, errori_validazione, creata_il · versione_foto_id (3) | 1 |
| versione_foto | contenuti | foto_id, numero (0 = originale), file, origine (originale / ritocco_ai), nota, provider_ai, modello_ai, versione_prompt, creata_il | 3 |
| approvazione | revisione | versione_id, utente_id, ruolo, esito, creata_il | 1 |
| pubblicazione | pubblicazione | post_id, versione_id, n_tentativo, stato (in_corso / ok / errore), id_esterno, errore, creata_il · indice unico parziale su `ok` per post | 1 |
| metrica | pubblicazione | pubblicazione_id, data_rilevazione, like, commenti, copertura, salvataggi | 4 |
| notifica | notifiche | utente_id, campagna_id, tipo (`campagna_respinta`, `campagna_scaduta`, …), canale, stato_invio, creata_il, inviata_il | 2b |
| anagrafica_artigiano | artigiani | utente_id (1:1), codice (unico, es. ART-0042), codice_consorzio, nome_bottega, referente, citta, telefono, stato_iscrizione, iscritto_il | 3 |
| account_social | artigiani | profilo_id, piattaforma, id_pagina, permesso (cifrato), scadenza, stato | 3 |

La versione corrente di un post è l'ultima. Versioni e decisioni non si cancellano mai.

Migrazioni dello sprint 1, una per modulo, tutte in T1-03: 001 accesso, 002 artigiani, 003 campagne, 004 contenuti, 005 revisione, 006 pubblicazione. Ogni migrazione successiva è un task della corsia 0.

**Transizioni** (`campagne/domain.py` per la campagna, `contenuti/domain.py` per il post):
- campagna: bozza → inviata → in_generazione → in_revisione → attiva → conclusa · in_generazione → generazione_fallita → inviata · in_revisione → respinta · inviata / in_generazione / generazione_fallita / in_revisione → scaduta · attiva ⇄ sospesa · attiva / sospesa → annullata
- post: da_approvare → approvato → pubblicato / fallito · fallito → approvato · da_approvare → scaduto · da_approvare → scartato
- `da_rivedere` è un indicatore (campo bool del post), non uno stato.

**Valori ammessi** (nel `domain.py` del modulo della tabella):
| Campo | Valori |
|---|---|
| tipo_prodotto | legno_mobili, ceramica_vetro, gioielli_metalli, tessile_pelle, alimentare, altro |
| valori[] | artigianalita, sostenibilita, tradizione, innovazione, territorio, su_misura |
| fascia_prezzo | accessibile, media, alta |
| obiettivo | vendere, negozio, notorieta, fidelizzare |
| tono[] | caldo, elegante, diretto, ironico, professionale |
| cortesia | tu, lei, dipende |
| canali[] | facebook, instagram (almeno uno) |
| frequenza → post/settimana | f1_2 → 2, f3_4 → 3, f5_piu → 5, decidete_voi → 3 |
| social_esistenti.canali[] | facebook, instagram, nessuno |
| foto_policy | quantita_mese: meno_5, da5_a12, da12_a20, oltre_20 · chi_scatta: artigiano, fotografo, consorzio · persone: mai, con_consenso, spesso |
| eventi_ricorrenti[].tipo | fiera_mercatino, festivita, lancio_prodotto, promozione, chiusura, altro |
| foto.origine | caricata, creata_ai |
| decisione_campagna.esito / motivo | approvata, rimandata, respinta / foto, altro |
| versione_post.tipo_intervento | generazione, rigenera_totale, rigenera_da_proposta, ritocco_foto, scelta_foto |

## 3. API (prefisso `/api`)
| Sprint | Modulo | Metodo e percorso | Ruolo | Esito |
|---|---|---|---|---|
| 1 | `main.py` | GET /health | tutti | `{"stato":"ok"}` |
| 1 | accesso | POST /auth/login · POST /auth/logout · GET /auth/me | tutti / autenticato | 200 + cookie `adflow_sessione` · 204 · 200 |
| 1 | campagne | GET /campagne?stato= | autenticato | l'artigiano vede solo le sue |
| 1 | campagne | POST /campagne `{titolo,inizio,fine,descrizione,crea_immagini_ai}` | artigiano | 201 bozza · 409 R-12 · 422 R-08 |
| 1 | campagne | GET /campagne/{id} | proprietario, operatore | campagna, foto e gruppi (senza post); all'operatore anche snapshot e decisioni |
| 1 | campagne | POST /campagne/{id}/foto (multipart: file, gruppo_id) | artigiano | 201 · solo in bozza · 422 R-13 |
| 1 | campagne | PUT /campagne/{id}/gruppi/{gruppo_id} `{descrizione}` | artigiano | copia la descrizione su tutto il gruppo · solo in bozza |
| 1 | campagne | DELETE /foto/{id} · DELETE /campagne/{id}/gruppi/{gruppo_id} | artigiano | 204 · solo in bozza |
| 1 | campagne | GET /foto/{id}/file | proprietario, operatore | immagine |
| 1 | campagne | POST /campagne/{id}/invia | artigiano | → inviata + job `genera_campagna`; 409 senza profilo; 422 R-08, R-13 |
| 1 | campagne | POST /campagne/{id}/riprova | operatore | generazione_fallita → inviata + job |
| 1 | revisione | GET /campagne/{id}/post?stato= | operatore | post con versione corrente e storico |
| 1 | revisione | POST /campagne/{id}/approva | operatore | → attiva, post approvati, righe approvazione + decisione · 409 R-14 |
| 2a | artigiani | GET /profilo · PUT /profilo | artigiano | 404 se assente · upsert, 422 obbligatori |
| 2a | campagne | PATCH /campagne/{id} | artigiano | solo in bozza, stessi controlli della creazione; anche `crea_immagini_ai` |
| 2b | revisione | POST /campagne/{id}/rimanda `{nota}` | operatore | `rimandata = true`, decisione, nessuna email |
| 2b | revisione | POST /campagne/{id}/respingi `{motivo, nota, foto_segnate[]}` | operatore | → respinta, post scartati, decisione, notifica · 422 R-18 o foto di altra campagna |
| 2b | campagne | POST /campagne/{id}/sospendi · /riattiva · /annulla | operatore | 409 fuori dalle transizioni |
| 2b | revisione | POST /post/{id}/rigenera `{modalita, testo_proposto, nota}` | operatore | `totale` o `da_proposta`; solo in_revisione; job · 409 R-03, R-16 · 422 `da_proposta` senza testo |
| 3 | revisione | GET /artigiani · GET /artigiani/{id} | operatore | elenco, dettaglio per sezioni (spec §4) |
| 3 | artigiani | POST /artigiani · PUT /artigiani/{id}/anagrafica | operatore | creazione, anagrafica |
| 3 | artigiani | POST /artigiani/{id}/social/{piattaforma}/collega | operatore | collegamento (simulato) |
| 3 | revisione | POST /post/{id}/ritocca-foto `{nota}` | operatore | solo in_revisione; job · 409 R-03 |
| 3 | revisione | POST /post/{id}/scegli-foto `{versione_foto_id}` | operatore | originale o precedente; non consuma cicli |
| 4 | pubblicazione | GET /metriche?artigiano=&campagna= | operatore; artigiano solo le sue | metriche |

Non esistono: modifica a mano di un post, approvazione o scarto del singolo post.

## 4. Job
| Sprint | Modulo | Job | Quando | Cosa fa |
|---|---|---|---|---|
| 1 | contenuti | `genera_campagna(campagna_id)` | da /invia, /riprova; 3 esecuzioni, 30 s | campagna `in_generazione`; usa lo snapshot; analisi foto; (dal 3) ritocco → `versione_foto` 1; slot R-05, R-08; post + validatore R-09 → `in_revisione`; alla terza esecuzione fallita `generazione_fallita` |
| 1 | `worker.py` | `tick_pubblicazione` | ogni minuto, uno alla volta | (2b) `revisione.scadenze()` R-06; poi `pubblicazione.pubblica_dovuti()`: tentativo registrato → pubblica → esito; campagna conclusa; (3) sospensione R-07 |
| 2b | contenuti | `rigenera_post(post_id)` | da /rigenera; 3 esecuzioni | nuovo testo, stessa foto, versioni rifiutate come contesto, validatore |
| 2b | notifiche | `invia_notifica(notifica_id)` | alla creazione; 3 tentativi | email via adattatore, aggiorna `stato_invio` |
| 3 | contenuti | `ritocca_foto(post_id)` | da /ritocca-foto; 3 esecuzioni | nuova `versione_foto` e nuova versione del post |
| 3 | revisione | `promemoria` | ogni ora | email all'operatore, R-06, una volta per campagna |
| 4 | pubblicazione | `raccogli_metriche` · `report_settimanale` | giorno · settimana | metriche; email di riepilogo |

I nomi dei job stanno in `core/coda.py`; un job di un altro modulo si accoda con `accoda(nome, …)`, senza importarlo.

## 5. Adattatori
Ognuno in `adapters/<nome>/`: interfaccia, implementazione finta, implementazione reale.
- **ai**: `analizza_immagine()`, `ritocca_immagine()` (3), `genera_post()`; `crea_immagine()` non ancora pianificata (spec R-19). Provider da `AI_PROVIDER`; ogni versione salva provider, modello e versione del prompt. Prompt in `adapters/ai/prompts/`.
- **social**: `collega_account()`, `pubblica()`, `leggi_metriche()`; simulato e Meta.
- **email**: `invia()`; catcher locale in sviluppo.
- **archivio**: salva, legge, elimina file sotto `ARCHIVIO_FOTO_DIR`.

## 6. Contratti tra moduli
Le sole funzioni di `moduli/<modulo>/service.py` che un altro modulo può chiamare. Ricevono la sessione `db` come primo argomento. Sprint 1:

| Modulo | Funzione | Usata da | Scritta in |
|---|---|---|---|
| accesso | `utente_corrente` (dipendenza FastAPI → utente) · `richiede_ruolo(*ruoli)` | tutti i router | T1-12 (fino ad allora: utente di prova, T1-06) |
| accesso | `crea_utente(email, password, nome, ruolo)` | `cli.py` | T1-13 |
| artigiani | `profilo_di(utente_id)` → profilo o `None` | campagne, revisione | T1-04 |
| campagne | `campagna(id)` · `foto_della_campagna(id)` · `campagne_in_stato(stati)` | contenuti, revisione, pubblicazione | T1-04 |
| campagne | `cambia_stato(campagna, nuovo)` | contenuti, revisione, pubblicazione | T1-04 |
| campagne | `registra_decisione(campagna, utente_id, esito, motivo, nota, foto_segnate)` | revisione | T1-04 |
| campagne | `aggiorna_foto(foto_id, analisi_ai, n_utilizzi)` | contenuti | T1-04 |
| contenuti | `post_della_campagna(campagna_id)` (versione corrente e storico) · `ha_blocchi(campagna_id)` · `approva_post(campagna_id)` → versioni approvate | revisione | T1-04 |
| contenuti | `post_dovuti(adesso)` (approvati, data raggiunta, campagna attiva) · `segna_esito(post, esito)` · `tutti_chiusi(campagna_id)` | pubblicazione | T1-04 |
| pubblicazione | `pubblica_dovuti(adesso)` | `tick_pubblicazione` | T1-43 |

- Sprint successivi (firme da fissare nel loro sprint, con un task della corsia 0): notifiche `crea()`; accesso `utente()`; artigiani `profilo()`, `account_social()`, `anagrafica_di()`; campagne `campagne_di()`; contenuti `scarta_post()`, `scadi_post()`, `puo_rigenerare()`, `puo_ritoccare()`, `scegli_foto()`; revisione `scadenze()`.
- Job accodati per nome: `genera_campagna` da campagne (/invia, /riprova); `rigenera_post` (2b) e `ritocca_foto` (3) da revisione.
- **Fabbriche di test** in `tests/moduli/<modulo>/fabbrica.py`, della corsia 0: `utente(ruolo)`, `profilo()`, `campagna_in_bozza()`, `campagna_inviata()`, `campagna_in_revisione()`, `campagna_attiva()`, `post_da_approvare()`, `post_approvato()`. Fixture `utente_di_prova(ruolo)` (T1-06) al posto di `utente_corrente` nei test delle API.
- Una firma o una fabbrica si cambia solo con un task della corsia 0.
