# Plan · come è fatto

Ogni tabella nasce già nella forma definitiva, nello sprint indicato. Vincoli: vedi le regole R-xx di `spec.md` §5.

## 1. Stack e configurazione
Python 3.11+ · FastAPI · Pydantic · SQLAlchemy 2 + Alembic · PostgreSQL 16 · Procrastinate (coda e job in PostgreSQL) · LiteLLM (AI; primo provider OpenAI; provider `finto` per sviluppo e test) · React + Vite + TypeScript + Mantine · pytest. Social simulato; email verso un catcher locale (Mailpit). Sessione con cookie httpOnly.

`backend/.env`:
```
DATABASE_URL · DATABASE_URL_TEST · ARCHIVIO_FOTO_DIR
AI_PROVIDER=finto|litellm · AI_MODELLO_VISIONE · AI_MODELLO_TESTO · OPENAI_API_KEY
ANTICIPO_MINIMO_GIORNI=3 · MARGINE_SLOT_MINUTI=15 · SMTP_HOST · SMTP_PORT
```

## 2. Modello dati
| Tabella | Campi | Sprint |
|---|---|---|
| utente | email (unica), password_hash, nome, ruolo (artigiano / operatore / admin), attivo | 1 |
| sessione | token_hash (sha256), utente_id, scade_il | 1 |
| profilo_bottega | utente_id (1:1), nome, referente, citta, anni_attivita, sito, storia, origine, valori[], tipo_prodotto, gamma, fascia_prezzo, stagionalita, clienti_ideali, obiettivo, zona, tono[], cortesia, vincoli, canali[], frequenza, orari, social_esistenti (JSON `{canali[], profili, cosa_funziona}`), foto_policy (JSON `{quantita_mese, chi_scatta, persone}`), eventi_ricorrenti (JSON `[{nome, quando, tipo}]`), chiusure, aggiornato_il · obbligatori: nome, referente, citta, tipo_prodotto, clienti_ideali, obiettivo, canali | 1 (seed; schermate 2a) |
| campagna | profilo_id, titolo, inizio, fine, descrizione, stato, canali[], frequenza, obiettivo, profilo_snapshot (JSON), rimandata (bool), inviata_il | 1 |
| foto | profilo_id, campagna_id, gruppo_id (uuid), file, mime, larghezza, altezza, descrizione, analisi_ai, n_utilizzi | 1 |
| post | campagna_id, canale, data_ora, stato, da_rivedere (bool), n_rigenerazioni_testo · n_ritocchi_foto (3) | 1 |
| versione_post | post_id, numero, testo, hashtag[], foto_id, tipo_intervento, testo_proposto, nota, provider_ai, modello_ai, versione_prompt, errori_validazione, creata_il · versione_foto_id (3) | 1 |
| decisione_campagna | campagna_id, utente_id, esito, motivo, nota, foto_segnate[], creata_il | 1 (solo `approvata`), 2b |
| approvazione | versione_id, utente_id, ruolo, esito, creata_il | 1 |
| pubblicazione | post_id, versione_id, n_tentativo, stato (in_corso / ok / errore), id_esterno, errore, creata_il · indice unico parziale su `ok` per post | 1 |
| notifica | utente_id, campagna_id, tipo (`campagna_respinta`, `campagna_scaduta`, …), canale, stato_invio, creata_il, inviata_il | 2b |
| versione_foto | foto_id, numero (0 = originale), file, origine (originale / ritocco_ai), nota, provider_ai, modello_ai, versione_prompt, creata_il | 3 |
| anagrafica_artigiano | utente_id (1:1), codice (unico, es. ART-0042), codice_consorzio, nome_bottega, referente, citta, telefono, stato_iscrizione, iscritto_il | 3 |
| account_social | profilo_id, piattaforma, id_pagina, permesso (cifrato), scadenza, stato | 3 |
| metrica | pubblicazione_id, data_rilevazione, like, commenti, copertura, salvataggi | 4 |

La versione corrente di un post è l'ultima. Versioni e decisioni non si cancellano mai.

**Transizioni** (`domain.py`):
- campagna: bozza → inviata → in_generazione → in_revisione → attiva → conclusa · in_generazione → generazione_fallita → inviata · in_revisione → respinta · inviata / in_generazione / generazione_fallita / in_revisione → scaduta · attiva ⇄ sospesa · attiva / sospesa → annullata
- post: da_approvare → approvato → pubblicato / fallito · fallito → approvato · da_approvare → scaduto · da_approvare → scartato
- `da_rivedere` è un indicatore (campo bool del post), non uno stato.

**Valori ammessi** (`domain.py`):
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
| decisione_campagna.esito / motivo | approvata, rimandata, respinta / foto, altro |
| versione_post.tipo_intervento | generazione, rigenera_totale, rigenera_da_proposta, ritocco_foto, scelta_foto |

## 3. API (prefisso `/api`)
| Sprint | Metodo e percorso | Ruolo | Esito |
|---|---|---|---|
| 1 | GET /health | tutti | `{"stato":"ok"}` |
| 1 | POST /auth/login · POST /auth/logout · GET /auth/me | tutti / autenticato | 200 + cookie `adflow_sessione` · 204 · 200 |
| 1 | GET /campagne?stato= | autenticato | l'artigiano vede solo le sue |
| 1 | POST /campagne `{titolo,inizio,fine,descrizione}` | artigiano | 201 bozza · 409 R-12 · 422 R-08 |
| 1 | GET /campagne/{id} | proprietario, operatore | dettaglio; visibilità secondo spec §4; all'operatore anche snapshot e decisioni |
| 1 | POST /campagne/{id}/foto (multipart: file, gruppo_id) | artigiano | 201 · solo in bozza · 422 R-13 |
| 1 | PUT /campagne/{id}/gruppi/{gruppo_id} `{descrizione}` | artigiano | copia la descrizione su tutto il gruppo · solo in bozza |
| 1 | DELETE /foto/{id} · DELETE /campagne/{id}/gruppi/{gruppo_id} | artigiano | 204 · solo in bozza |
| 1 | GET /foto/{id}/file | proprietario, operatore | immagine |
| 1 | POST /campagne/{id}/invia | artigiano | → inviata + job `genera_campagna`; 409 senza profilo; 422 R-08, R-13 |
| 1 | POST /campagne/{id}/riprova | operatore | generazione_fallita → inviata + job |
| 1 | GET /campagne/{id}/post?stato= | operatore | post con versione corrente e storico |
| 1 | POST /campagne/{id}/approva | operatore | → attiva, post approvati, righe approvazione + decisione · 409 R-14 |
| 2a | GET /profilo · PUT /profilo | artigiano | 404 se assente · upsert, 422 obbligatori |
| 2a | PATCH /campagne/{id} | artigiano | solo in bozza, stessi controlli della creazione |
| 2b | POST /campagne/{id}/rimanda `{nota}` | operatore | `rimandata = true`, decisione, nessuna email |
| 2b | POST /campagne/{id}/respingi `{motivo, nota, foto_segnate[]}` | operatore | → respinta, post scartati, decisione, notifica · 422 R-18 o foto di altra campagna |
| 2b | POST /campagne/{id}/sospendi · /riattiva · /annulla | operatore | 409 fuori dalle transizioni |
| 2b | POST /post/{id}/rigenera `{modalita, testo_proposto, nota}` | operatore | `totale` o `da_proposta`; solo in_revisione; job · 409 R-03, R-16 · 422 `da_proposta` senza testo |
| 3 | GET /artigiani · GET /artigiani/{id} · POST /artigiani · PUT /artigiani/{id}/anagrafica | operatore | elenco, dettaglio per sezioni, creazione, anagrafica |
| 3 | POST /artigiani/{id}/social/{piattaforma}/collega | operatore | collegamento (simulato) |
| 3 | POST /post/{id}/ritocca-foto `{nota}` | operatore | solo in_revisione; job · 409 R-03 |
| 3 | POST /post/{id}/scegli-foto `{versione_foto_id}` | operatore | originale o precedente; non consuma cicli |
| 4 | GET /metriche?artigiano=&campagna= | operatore; artigiano solo le sue | metriche |

Non esistono: modifica a mano di un post, approvazione o scarto del singolo post.

## 4. Job
| Sprint | Job | Quando | Cosa fa |
|---|---|---|---|
| 1 | `genera_campagna(campagna_id)` | da /invia, /riprova; 3 esecuzioni, 30 s | usa lo snapshot; analisi foto; (dal 3) ritocco → `versione_foto` 1; slot R-05, R-08; post + validatore R-09 → in_revisione |
| 1 | `tick_pubblicazione` | ogni minuto, uno alla volta | tentativo registrato → pubblica → esito; conclusa · (2b) scadenze R-06 · (3) sospensione R-07 |
| 2b | `rigenera_post(post_id)` | da /rigenera; 3 esecuzioni | nuovo testo, stessa foto, versioni rifiutate come contesto, validatore |
| 2b | `invia_notifica(notifica_id)` | alla creazione; 3 tentativi | email via adattatore, aggiorna `stato_invio` |
| 3 | `ritocca_foto(post_id)` | da /ritocca-foto; 3 esecuzioni | nuova `versione_foto` e nuova versione del post |
| 3 | `promemoria` | ogni ora | email all'operatore, R-06, una volta per campagna |
| 4 | `raccogli_metriche` · `report_settimanale` | giorno · settimana | metriche; email di riepilogo |

## 5. Adattatori
- **AI**: `analizza_immagine()`, `ritocca_immagine()`, `genera_post()`; provider da `AI_PROVIDER`; ogni versione salva provider, modello e versione del prompt. Prompt in `adapters/prompts/`.
- **Social**: `collega_account()`, `pubblica()`, `leggi_metriche()`; simulato e Meta.
- **Email**: `invia()`; catcher locale in sviluppo.
- **Archivio foto**: salva, legge, elimina file sotto `ARCHIVIO_FOTO_DIR`.
