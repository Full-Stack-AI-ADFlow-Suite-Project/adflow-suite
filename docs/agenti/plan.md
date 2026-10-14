# Plan · come è fatto

Come è costruito il prodotto: stack, tabelle, API, job, adattatori, contratti tra i moduli, base comune. Cartelle e regole dei moduli: `constitution.md` §2. Vincoli: regole R-xx di `spec.md` §5.

**Stato** (ADR-114, `perimetro-mvp.md`): nelle tabelle `MVP` = nel prodotto; `congelato` = il codice e i test restano, l'interfaccia lo nasconde, non si estende; `fuori MVP` = non c'è, o il codice l'ha tolto T3-01: è in `docs/ROADMAP.md`. Le righe `fuori MVP` stanno in fondo a ogni tabella.

## 1. Stack e configurazione
Python 3.11+ · FastAPI · Pydantic · SQLAlchemy 2 + Alembic · PostgreSQL 16 · Procrastinate (coda e job in PostgreSQL) · LiteLLM (AI; primo provider OpenAI; provider `finto` per sviluppo e test) · React + Vite + TypeScript + Mantine · pytest. Social simulato e Meta, su una pagina di prova (`SOCIAL_PROVIDER`); email verso un catcher locale (Mailpit). Sessione con cookie httpOnly. Driver psycopg 3: gli indirizzi iniziano con `postgresql+psycopg://`. Le versioni stanno in `backend/requirements.txt`; l'ambiente virtuale è `.venv` nella radice. Cosa offre già il codice comune: §7.

`backend/.env` (ogni variabile è un campo di `core/config.py`, in minuscolo, ed è in `.env.example` con un valore finto):
```
DATABASE_URL · DATABASE_URL_TEST · ARCHIVIO_FOTO_DIR · RICHIESTA_MAX_BYTE=12582912
AI_PROVIDER=finto|litellm · AI_MODELLO_VISIONE · AI_MODELLO_TESTO · AI_MODELLO_IMMAGINI · OPENAI_API_KEY
SOCIAL_PROVIDER=finto|meta · META_PAGINA_ID · META_INSTAGRAM_ID · META_TOKEN_PAGINA · META_GRAPH_VERSIONE · FOTO_URL_PUBBLICO
ANTICIPO_MINIMO_GIORNI=3 · MARGINE_SLOT_MINUTI=15 · OROLOGIO_GIORNI_AVANTI=0 · SMTP_HOST · SMTP_PORT
SESSIONE_ARTIGIANO_GIORNI=7 · SESSIONE_OPERATORE_ORE=12 · CONSORZIO_NOME · CONSORZIO_TELEFONO · CONSORZIO_EMAIL
AMBIENTE=sviluppo|test|produzione · LOGIN_LIMITE_TENTATIVI=5 · LOGIN_FINESTRA_SECONDI=900 · LOGIN_LIMITE_SEGRETO · EMAIL_TEST_ENVIRONMENT · COOKIE_SECURE
```
`AI_MODELLO_IMMAGINI` entra in `core/config.py` con T3-31; `SOCIAL_PROVIDER`, le variabili `META_*` e `FOTO_URL_PUBBLICO` con T3-23 e T3-42 (in `.env.example` ci sono già, da T3-41). `COOKIE_SECURE` è facoltativa: in produzione è sempre vera (`docs/sicurezza-accesso.md`).

## 2. Modello dati
| Tabella | Modulo | Campi | Stato |
|---|---|---|---|
| utente | accesso | email (unica), password_hash, nome, ruolo (artigiano / operatore / admin), attivo, deve_cambiare_password (bool; nell'MVP resta falso: il cambio obbligato è fuori MVP) | MVP |
| sessione | accesso | token_hash (sha256), utente_id, scade_il (spostata in avanti a ogni richiesta, spec R-29) | MVP |
| profilo_bottega | artigiani | utente_id (1:1), nome, referente, citta, anni_attivita, sito, storia, origine, valori[], tipo_prodotto, gamma, fascia_prezzo, stagionalita, clienti_ideali, obiettivo, zona, tono[], cortesia, vincoli, canali[] (proposta iniziale per le campagne), frequenza (per canale), orari (JSON), social_esistenti (JSON `{canali[], profili, cosa_funziona}`), foto_policy (JSON `{quantita_mese, chi_scatta, persone}`), eventi_ricorrenti (JSON `[{nome, quando, tipo}]`), chiusure, logo (file, facoltativo; non si legge più, ADR-114), aggiornato_il · obbligatori: nome, referente, citta, tipo_prodotto, clienti_ideali, obiettivo, canali | MVP |
| account_social | artigiani | profilo_id, piattaforma, id_pagina, permesso (cifrato), scadenza, stato · unico su (profilo_id, piattaforma). Nell'MVP nasce come nel seed e dice solo se un canale è collegato: si pubblica sulla pagina di prova di `.env` | MVP |
| campagna | campagne | profilo_id, titolo, inizio, fine, descrizione, stato, canali[] (dichiarati in bozza), canali_tolti[], frequenza, obiettivo, profilo_snapshot (JSON, con la dichiarazione dell'artigiano, spec R-41), inviata_il, chiusa_il | MVP |
| gruppo_foto | campagne | profilo_id, campagna_id (facoltativa: vuota = gruppo dell'archivio, caricato dal profilo), origine, descrizione, da_usare_il (data, facoltativa), n_immagini (solo `create_ai`) | MVP |
| foto | campagne | profilo_id, campagna_id (facoltativa, come il suo gruppo), gruppo_id (→ gruppo_foto; facoltativo: vuoto per le immagini AI e le vecchie cartoline), origine (default `caricata`), file, mime, larghezza, altezza, da_usare (bool, la stella; non si legge più, ADR-114), analisi_ai (JSON `{idonea, simile_a, tipo, punteggio, motivo, soggetto}`), n_utilizzi, pubblicata_su (JSON `{canale: istante dell'ultima pubblicazione}`, in UTC e in formato ISO 8601, es. `{"instagram": "2030-01-05T12:00:00+00:00"}`; `{}` se non è mai uscita; la scrive la pubblicazione con `segna_pubblicata()`) | MVP |
| decisione_campagna | campagne | campagna_id, utente_id, esito, motivo, nota, foto_segnate[], canale (solo `canale_tolto`), post_id (solo `riprogrammato`), creata_il | MVP |
| piano | contenuti | campagna_id, numero, strategia (testo), contenuto (JSON, come lo ha scritto l'AI), esito_controllo (JSON), debole (bool; sempre falso, ADR-114), provider_ai, modello_ai, versione_prompt, creata_il · unico su (campagna_id, numero) | MVP |
| uscita | contenuti | campagna_id, gruppo_id (facoltativo: vuoto per le uscite con un'immagine AI), numero, tema · unico su (campagna_id, numero) | MVP |
| post | contenuti | campagna_id, uscita_id, canale, formato, riempitivo (facoltativo), data_ora, stato, da_rivedere (bool), n_rigenerazioni_testo, controllato_da (utente, facoltativo) · controllato_il (la spunta, congelata), intervento_in_corso (tipo, facoltativo) · intervento_dal · unico su (uscita_id, canale) | MVP |
| versione_post | contenuti | post_id, numero, testo, hashtag[], tipo_intervento, autore_id (utente; vuoto = AI), testo_proposto, nota, provider_ai, modello_ai, versione_prompt (i tre facoltativi), errori_validazione (JSON `[{livello, regola, messaggio}]`), creata_il · unico su (post_id, numero) | MVP |
| versione_post_foto | contenuti | versione_id, posizione, foto_id · unico su (versione_id, posizione) | MVP |
| chiamata_ai | contenuti | campagna_id, post_id (facoltativo), tipo (analisi / piano / testo / immagine), provider_ai, modello_ai, token_ingresso, token_uscita, n_immagini (facoltativi), costo_usd (numerico), creata_il (spec R-44) | MVP (migrazione 012, T3-31) |
| errore_generazione | contenuti | campagna_id, tipo, messaggio, tappa, canale (facoltativo), creata_il | MVP |
| approvazione | revisione | versione_id, utente_id, ruolo, esito, creata_il | MVP |
| pubblicazione | pubblicazione | post_id, versione_id, n_tentativo, stato (in_corso / ok / errore), id_esterno, errore, creata_il · indice unico parziale su `ok` per post · unico su (post_id, n_tentativo) | MVP |
| notifica | notifiche | utente_id, campagna_id, post_id (facoltativo: solo `post_fallito`, per distinguere un evento dall'altro), tipo (`campagna_pronta`, `piano_da_rivedere`, `generazione_fallita`, `post_fallito` agli operatori; `campagna_respinta`, `campagna_scaduta` all'artigiano), canale (`email`), stato_invio (`da_inviare`, `inviata`, `fallita`), creata_il, inviata_il | congelato (righe ed email al catcher locale) |
| versione_foto | contenuti | foto_id, numero (0 = originale), file, origine (originale / ritocco_ai), nota, provider_ai, modello_ai, versione_prompt, creata_il; con `versione_post_foto.versione_foto_id` e `post.n_ritocchi_foto` | fuori MVP |
| metrica | pubblicazione | pubblicazione_id, data_rilevazione, like, commenti, copertura, salvataggi | fuori MVP |
| anagrafica_artigiano | artigiani | utente_id (1:1), codice (unico, es. ART-0042), codice_consorzio, nome_bottega, referente, citta, telefono, stato_iscrizione, iscritto_il | fuori MVP |

La versione corrente di un post è l'ultima; il piano corrente è l'ultimo. Versioni, piani, decisioni ed errori di generazione non si cancellano mai. `post.da_rivedere` è vero quando la versione corrente ha almeno un errore di livello `blocco`. Le note interne sono decisioni con esito `nota`. `campagna.chiusa_il` si scrive quando la campagna entra in uno stato chiuso. Un post nasce con il piano, senza versioni: la versione 1 arriva con il testo, e le sue foto sono quelle che il piano gli ha dato. Nel contratto Python `versione.legami_foto` è la lista dei record `VersionePostFoto`, ordinati per `posizione`, con `foto_id`: non contiene direttamente gli oggetti `Foto` di un altro modulo.

**Rimpiazzi e archivio** (spec R-27, R-28): un post che le foto non coprono ha `riempitivo` = `immagine_ai`, un'uscita senza gruppo e una foto con origine `creata_ai`, senza gruppo, data alla versione 1 del post. Campagna facoltativa su `gruppo_foto` e `foto` e gruppo facoltativo su `foto` e `uscita` servono anche all'archivio (congelato). Il riempitivo `cartolina` (foto con origine `cartolina`) resta per le righe vecchie: finché T3-34 non è su `main` la generazione compone ancora cartoline. Lo controllano i service, non il database.

**Migrazioni** (una catena Alembic; ogni migrazione scrive lo schema per esteso, senza importare i `models.py`): 001 accesso · 002 artigiani · 003 campagne · 004 contenuti · 005 revisione · 006 pubblicazione · 007 coda, le tabelle `procrastinate_*` con lo schema di `procrastinate==3.10.0` (cambiare versione richiede una migrazione nuova con gli script di aggiornamento di Procrastinate) · 008 riallineamento delle tabelle 002–006 alla forma di questa pagina · 009 `limite_login` (chiave, tentativi, scade_il; la usa solo `core/limite_login.py`, senza `models.py`) · 010 `foto.pubblicata_su` · 011 `notifica` · 012 `chiamata_ai` (T3-31). Le tabelle `versione_foto` e `anagrafica_artigiano` non si fanno (fuori MVP).

**Transizioni** (`campagne/domain.py` per la campagna, `contenuti/domain.py` per il post):
- campagna: bozza → inviata → in_generazione → in_revisione → attiva → conclusa · inviata / in_generazione → generazione_fallita → inviata · in_revisione → respinta · inviata / in_generazione / generazione_fallita / in_revisione → scaduta · attiva ⇄ sospesa · attiva / sospesa → annullata (congelati) · piano_da_rivedere → respinta / scaduta (nessuna campagna ci entra più, ADR-114: lo stato resta per le righe vecchie)
- post: da_approvare → approvato → pubblicato / fallito / annullato · fallito → approvato · da_approvare → scaduto · da_approvare → scartato
- `da_rivedere` è un indicatore (campo bool del post), non uno stato.

**Valori ammessi** (nel `domain.py` del modulo della tabella; alcuni restano solo per le righe vecchie o per il codice congelato):
| Campo | Valori |
|---|---|
| tipo_prodotto | legno_mobili, ceramica_vetro, gioielli_metalli, tessile_pelle, alimentare, altro |
| valori[] | artigianalita, sostenibilita, tradizione, innovazione, territorio, su_misura |
| fascia_prezzo | accessibile, media, alta |
| obiettivo | vendere, negozio, notorieta, fidelizzare |
| tono[] | caldo, elegante, diretto, ironico, professionale |
| cortesia | tu, lei, dipende |
| canali[] (profilo e campagna) | facebook, instagram (almeno uno; sulla campagna solo se collegati, spec R-22) |
| frequenza → post/settimana per canale | f1_2 → 2, f3_4 → 3, f5_piu → 5, decidete_voi → 3 |
| social_esistenti.canali[] | facebook, instagram, nessuno |
| foto_policy | quantita_mese: meno_5, da5_a12, da12_a20, oltre_20 · chi_scatta: artigiano, fotografo, consorzio · persone: mai, con_consenso, spesso |
| eventi_ricorrenti[].tipo | fiera_mercatino, festivita, lancio_prodotto, promozione, chiusura, altro |
| account_social.stato | collegato, scaduto, scollegato |
| gruppo_foto.origine | caricate, create_ai |
| foto.origine | caricata, creata_ai, cartolina |
| foto.analisi_ai.tipo | pezzo_finito, dettaglio, lavorazione, persona, ambientato, evento |
| decisione_campagna.esito / motivo | approvata, respinta, proseguita, canale_tolto, nota, sospesa, riattivata, annullata, riprogrammato / foto, altro |
| post.formato | singola, carosello |
| post.riempitivo | archivio, cartolina, immagine_ai (vuoto = post con una foto disponibile) |
| versione_post.tipo_intervento | generazione, rigenera_totale, rigenera_da_proposta, modifica_operatore, ritocco_foto, scelta_foto, cambio_foto |
| errori_validazione[].livello | blocco, avviso |
| errore_generazione.tipo | temporaneo, risposta, configurazione, richiesta, rifiuto |
| post.intervento_in_corso | rigenera_totale, rigenera_da_proposta, ritocco_foto |

**Scheda per canale**: `SCHEDE_CANALE` in `contenuti/domain.py`, una voce per canale con `max_caratteri` e `max_hashtag` (editoriali: avviso), `limite_caratteri` e `limite_hashtag` (della piattaforma: blocco), `max_foto`, `proporzioni`, `link_cliccabili`. I valori sono in spec R-21. `proporzioni` è una tupla di stringhe `"larghezza:altezza"`: `("1:1", "4:5")` su entrambi i canali; nella risposta JSON diventa `["1:1", "4:5"]`. `link_cliccabili` è un booleano riferito al testo del post: `true` per Facebook, `false` per Instagram. La leggono il validatore, il controllo del piano e, tramite le risposte dell'API, le anteprime.

## 3. API (prefisso `/api`)
| Stato | Modulo | Metodo e percorso | Ruolo | Esito |
|---|---|---|---|---|
| MVP | `main.py` | GET /health · GET /consorzio | tutti, senza sessione | `{"stato":"ok"}` · `{nome, telefono, email}` dalla configurazione |
| MVP | accesso | POST /auth/login · POST /auth/logout · GET /auth/me | tutti / autenticato | 200 + cookie `adflow_sessione` · 204 · 200; durata della sessione per ruolo, rinnovata a ogni richiesta (R-29) |
| MVP | artigiani | GET /canali | artigiano | `[{canale, collegato}]` per i canali dell'MVP |
| MVP | artigiani | GET /profilo · PUT /profilo | artigiano | 404 se assente · upsert, 422 obbligatori |
| MVP | artigiani | POST /artigiani `{email, nome}` | operatore | 201 con la password provvisoria, una sola volta (spec R-37) · 409 email già usata · 422 email non valida |
| MVP | campagne | GET /campagne?stato= (ripetibile) | autenticato | l'artigiano vede solo le sue; all'operatore ogni campagna porta anche `bottega` e `citta`, dal profilo |
| MVP | campagne | POST /campagne `{titolo,inizio,fine,descrizione,canali[]}` | artigiano | 201 bozza · 409 R-12 · 422 R-08, R-22 |
| MVP | campagne | GET /campagne/{id} | proprietario, operatore | campagna, gruppi con le loro foto, `post_chiesti_per_canale`, `avvisi[]` (R-25) (senza post); all'operatore anche snapshot e decisioni, note interne comprese |
| MVP | campagne | PATCH /campagne/{id} | artigiano | solo in bozza, stessi controlli della creazione; anche `canali[]` |
| MVP | campagne | POST /campagne/{id}/gruppi `{origine, descrizione, da_usare_il, n_immagini}` | artigiano | 201 · solo in bozza · 422 R-13 (i gruppi `create_ai` restano, nascosti nell'interfaccia) |
| MVP | campagne | PUT /campagne/{id}/gruppi/{gruppo_id} `{descrizione, da_usare_il, n_immagini}` | artigiano | solo in bozza · 422 R-13 |
| MVP | campagne | POST /campagne/{id}/foto (multipart: file, gruppo_id; entrambi obbligatori) | artigiano | 201 · solo in bozza, solo in un gruppo `caricate` già creato · 422 R-13 o senza gruppo |
| MVP | campagne | DELETE /foto/{id} · DELETE /campagne/{id}/gruppi/{gruppo_id} | artigiano | 204 · solo in bozza |
| MVP | campagne | GET /foto/{id}/file | proprietario, operatore | immagine; vale anche per le foto senza campagna dell'archivio |
| MVP | campagne | POST /campagne/{id}/invia `{dichiarazione}` | artigiano | → inviata + job `genera_campagna`; 409 senza profilo o con un canale non collegato (R-22); 422 R-08, R-13, senza dichiarazione (R-41) |
| MVP | campagne | POST /campagne/{id}/riprova | operatore | generazione_fallita → inviata + job |
| MVP | campagne | GET /foto/{id}/pubblica?canale=&firma= | senza sessione, con firma a tempo generata dal server | la foto sistemata per il canale (spec R-42), JPEG: è l'indirizzo pubblico che Instagram scarica. La firma è un HMAC-SHA256 di (id, canale, scadenza), con una chiave derivata da `LOGIN_LIMITE_SEGRETO` (con una separazione di dominio): cambiare quel segreto invalida anche gli indirizzi già dati a Instagram (`docs/sicurezza-accesso.md`). La base dell'indirizzo è `FOTO_URL_PUBBLICO` · 404 firma non valida o scaduta |
| MVP | contenuti | GET /campagne/{id}/calendario | proprietario, operatore | strategia del piano e soli post approvati, pubblicati, falliti o annullati (data, canale, stato, testo e foto della versione corrente); canali tolti con la nota; numero dei post scaduti · 409 prima dell'approvazione |
| MVP | revisione | GET /da-approvare | operatore | le campagne di tutti gli artigiani negli stati "da approvare" (spec §4), con bottega e città, conteggi dei post (totale, da approvare, da rivedere, riempitivi per canale), `entro_quando` e ultima nota interna, ordinate per `entro_quando` (R-38) |
| MVP | revisione | GET /campagne/{id}/post?stato= | operatore | in ogni stato dopo l'invio: piano corrente (strategia, esito del controllo, debole) o niente se non c'è ancora, uscite (tema, gruppo e data del gruppo) con i post dei canali (tipo di riempitivo, versione corrente con foto, autore, blocchi e avvisi, storico, spunta e intervento in corso), foto non usate per gruppo con il motivo, `ultimo_errore` della generazione (R-35), `costo_ai`, il totale della campagna in dollari (R-44) |
| MVP | revisione | POST /campagne/{id}/approva | operatore | → attiva, post `da_approvare` approvati (quelli con la data passata scaduti), righe approvazione + decisione · 409 R-14 |
| MVP | revisione | POST /campagne/{id}/respingi `{motivo, nota, foto_segnate[]}` | operatore | da in_revisione o piano_da_rivedere → respinta, post scartati, decisione, notifica · 422 R-18 o foto di altra campagna |
| MVP | revisione | POST /post/{id}/modifica `{testo, hashtag[]}` | operatore | solo in_revisione: versione `modifica_operatore` · 409 R-16, R-31 · 422 R-30 |
| MVP | revisione | POST /post/{id}/rigenera `{modalita, testo_proposto, nota}` | operatore | `totale` o `da_proposta`; solo in_revisione; stesse foto; accende l'intervento in corso + job · 409 R-03, R-16, R-31 · 422 `da_proposta` senza testo |
| congelato | campagne | GET /archivio | artigiano | `[gruppo]`: i gruppi senza campagna del suo profilo, ognuno con le sue foto, nella forma dei gruppi di `GET /campagne/{id}`; elenco vuoto se non ce ne sono (spec R-27) |
| congelato | campagne | POST /archivio/gruppi `{descrizione}` | artigiano | 201 gruppo `caricate` senza campagna, senza `da_usare_il` · 422 senza descrizione |
| congelato | campagne | POST /archivio/foto (multipart: file, gruppo_id; entrambi obbligatori) | artigiano | 201 foto, come `POST /campagne/{id}/foto` · 422 R-13 (tipo, peso, lato corto, più di 20 foto nel gruppo) · 404 se il gruppo non è del suo archivio |
| congelato | campagne | DELETE /archivio/foto/{id} · DELETE /archivio/gruppi/{id} | artigiano | 204; il gruppo si elimina con le sue foto · 409 se la foto, o una foto del gruppo, è già in un post (`n_utilizzi` > 0) · 404 se non è del suo archivio |
| congelato | revisione | POST /campagne/{id}/nota `{nota}` | operatore | in ogni stato dopo l'invio: decisione `nota`, nessuna email · 422 senza nota (R-32) |
| congelato | revisione | POST /campagne/{id}/togli-canale `{canale, nota}` | operatore | in generazione_fallita, piano_da_rivedere o in_revisione: post del canale scartati, canale in `canali_tolti`, decisione `canale_tolto`; da generazione_fallita, se resta un canale, riparte il job · 409 se è l'ultimo canale · 422 senza nota |
| congelato | revisione | POST /campagne/{id}/sospendi · /riattiva `{pubblica_ora[]}` · /annulla | operatore | R-33; decisione per ognuna · 409 fuori dalle transizioni · 422 se `pubblica_ora` contiene un post non in arretrato |
| congelato | revisione | POST /post/{id}/controllato `{valore}` | operatore | mette o toglie la spunta (R-30) · 409 fuori da in_revisione o su un post `da_rivedere` |
| congelato | revisione | POST /post/{id}/riprogramma `{data_ora}` | operatore | post `fallito` in campagna attiva o sospesa → `approvato`, decisione `riprogrammato` · 409 se non è fallito · 422 R-34 |
| fuori MVP | campagne | PUT /foto/{id} `{da_usare}` | artigiano | la stella (tolta da T3-01) |
| fuori MVP | revisione | POST /campagne/{id}/prosegui | operatore | piano_da_rivedere → in_generazione (tolto da T3-01, R-20) |
| fuori MVP | artigiani | PUT, GET, DELETE /profilo/logo | artigiano | il logo della bottega (tolto da T3-01, R-40) |
| fuori MVP | accesso | POST /auth/cambia-password `{password_attuale, password_nuova}` | autenticato | 204; spegne `deve_cambiare_password`; finché è acceso ogni altra chiamata → 403 (R-37) |
| fuori MVP | revisione | GET /artigiani · GET /artigiani/{id} | operatore | elenco (R-38); dettaglio per sezioni: campagne da approvare, in corso, le ultime 3 chiuse e il totale delle chiuse |
| fuori MVP | campagne | GET /campagne?artigiano=&stato= | operatore | filtro per artigiano, per la pagina delle campagne chiuse |
| fuori MVP | artigiani | POST /artigiani/{id}/password-provvisoria · POST /artigiani/{id}/social/{piattaforma}/collega | operatore | nuova password provvisoria · collegamento degli account |
| fuori MVP | revisione | POST /post/{id}/ritocca-foto · /scegli-foto · /cambia-foto · /sposta | operatore | ritocco e versioni della foto, cambio foto, spostamento (R-36) |
| fuori MVP | pubblicazione | GET /metriche?artigiano=&campagna=&dal=&al= | operatore; artigiano solo le sue | metriche (R-39) |

Per ogni percorso: una richiesta oltre `RICHIESTA_MAX_BYTE` (12 MiB: i 10 MB di una foto più il margine del multipart) riceve 413 prima di arrivare al router; `POST /auth/login` oltre il limite dei tentativi riceve 429 con `Retry-After`.

L'archivio (congelato) vuole un profilo già salvato: senza profilo ogni sua chiamata risponde 404, come `GET /profilo`. L'archivio non ha modifica del gruppo. Nella risposta di `GET /archivio` ci sono solo i gruppi caricati dal profilo: le foto delle campagne chiuse fanno parte dell'archivio (spec R-27) ma si leggono dalle loro campagne.

Non esistono: approvazione, scarto o annullamento del singolo post; togliere un'uscita; `rimanda`.

## 4. Job
| Stato | Modulo | Job | Quando | Cosa fa |
|---|---|---|---|---|
| MVP | contenuti | `genera_campagna(campagna_id)` | da /invia, /riprova; 3 esecuzioni, 30 s | A tappe, ognuna in una sua transazione e saltata se è già fatta (R-24). ① `inviata` → `in_generazione` ② analisi dei gruppi `caricate` non ancora analizzati → `aggiorna_foto()` ③ se manca il piano: piano dell'AI con lo snapshot, controllo (R-05, R-08, R-09, R-28), righe `piano`, `uscita`, `post` con il loro `riempitivo` ④ immagini dei rimpiazzi (vedi sotto) ⑤ per ogni post senza versione: testo, validatore (R-09), versione 1 con le sue foto ⑥ `in_revisione`, con la notifica agli operatori. Salta i canali in `canali_tolti`. Errori (R-35): ogni errore che ferma l'esecuzione si salva in `errore_generazione`; `temporaneo` e `risposta` → nuova esecuzione, alla terza `generazione_fallita` (con la notifica agli operatori); `configurazione` → `generazione_fallita` subito; `richiesta` o `rifiuto` su una foto → foto non idonea con il motivo, sul testo di un post → versione vuota con un blocco, e si continua |
| MVP | `worker.py` | `tick_pubblicazione` | ogni minuto, uno alla volta | `revisione.scadenze()`: scadenza morbida R-06 e campagne ferme da 30 minuti R-35; poi `pubblicazione.pubblica_dovuti()`: tentativo registrato → pubblica con la foto del post (sistemata per il canale con T3-21 e T3-42) → esito, notifica agli operatori per un post `fallito`; campagna conclusa secondo R-34 |
| MVP | contenuti | `rigenera_post(post_id)` | da /rigenera; 3 esecuzioni | non fa nulla se la campagna non è `in_revisione` o il post non è `da_approvare`; nuovo testo, stesse foto, versioni rifiutate come contesto, validatore; conta il ciclo e spegne l'intervento in corso quando nasce la versione; alla terza esecuzione fallita spegne l'intervento senza contare il ciclo (R-31) |
| congelato | notifiche | `invia_notifica(notifica_id)` | alla creazione; 3 tentativi | email via adattatore, verso il catcher locale; aggiorna `stato_invio` |
| fuori MVP | contenuti | `ritocca_foto(post_id)` | da /ritocca-foto | nuova `versione_foto` e nuova versione del post (R-17) |
| fuori MVP | revisione | `promemoria` | ogni ora | email all'operatore 48 ore prima dell'inizio (R-06) |
| fuori MVP | pubblicazione | `raccogli_metriche` · `report_settimanale` | giorno · settimana | metriche e riepiloghi (R-39) |

**Generazione nell'MVP** (ADR-114), tappe ③ e ④: il codice passa all'AI solo le foto migliori per punteggio, fino ai post chiesti per canale (T3-33); il piano non si ferma mai e i post scoperti hanno `riempitivo` = `immagine_ai`; per ogni uscita scoperta un'immagine AI quadrata 1:1, la stessa sui due canali (spec R-28, R-43), salvata con l'adattatore archivio e creata come foto `creata_ai` con `campagne.service.aggiungi_foto()` (T3-34, che toglie le cartoline). Ogni chiamata all'AI scrive una riga `chiamata_ai` (spec R-44). Finché T3-33 e T3-34 non sono su `main`, il codice usa ancora le foto d'archivio e le cartoline come riempitivi.

I nomi dei job stanno in `core/coda.py`, solo quelli dell'MVP; un job di un altro modulo si accoda con `accoda(nome, …)`, senza importarlo. Il job parte anche trovando la campagna già `in_generazione` (nuova esecuzione): riprende dalla prima tappa non fatta.

## 5. Adattatori
Ognuno in `adapters/<nome>/`: interfaccia, implementazione finta, implementazione reale.
- **ai**: `analizza_gruppo()` (le foto di un gruppo con la sua descrizione → per ogni foto `idonea`, `simile_a`, `tipo`, `punteggio`, `motivo`, `soggetto`), `pianifica_campagna()` (snapshot, campagna, gruppi analizzati, limiti per canale, schede dei canali → strategia, uscite e post per canale con formato, foto, data e ora), `genera_post()` (un post del piano → testo e hashtag per il suo canale), `genera_immagine(prompt, formato)` per i rimpiazzi (spec R-43, T3-34). Ogni metodo restituisce anche l'uso (token o immagini) per il costo (spec R-44, T3-31). Ogni errore esce dall'adattatore come `ErroreAI` con il suo `tipo` (R-35) e un messaggio per l'operatore: è l'adattatore a tradurre gli errori del provider. Provider da `AI_PROVIDER`: `finto` (sviluppo e test) o `litellm` (T3-31: risposte strutturate con modelli Pydantic, foto ridotte a 1024 px). Piano e versioni salvano provider, modello e versione del prompt; prompt in `adapters/ai/prompts/`, quello del piano scritto da social media manager. Il provider finto dà sempre lo stesso piano a parità di dati: una foto per post, le foto disponibili fino ai post chiesti, poi i rimpiazzi `immagine_ai` (T3-33; fino ad allora foto d'archivio e cartoline); date distribuite sul periodo, Instagram il giorno dopo Facebook; carosello ed errori, di ogni tipo, a comando. Il dettaglio di LiteLLM, del provider finto e delle immagini è in `brief-ai.md` (T3-31…T3-34). `ritocca_immagine()`: fuori MVP.
- **social**: `pubblica(canale, testo, hashtag, foto, url_foto)` (una foto: i byte servono a Facebook, l'indirizzo pubblico di §3 a Instagram); simulato e Meta (`SOCIAL_PROVIDER`). Meta: Facebook `POST /{page-id}/photos`; Instagram contenitore `POST /{ig-id}/media` con `image_url` (l'indirizzo pubblico di §3) e `POST /{ig-id}/media_publish`, stato del contenitore controllato una volta al minuto per al massimo 5 minuti; errori tradotti in temporaneo o definitivo. Token, id della Pagina e dell'account Instagram da `.env`: una sola pagina di prova per tutti gli artigiani, `account_social` non si legge. Dettaglio in `brief-meta.md` (T3-41…T3-43). `collega_account()` e `leggi_metriche()`: fuori MVP.
- **email**: `invia()`; catcher locale in sviluppo (congelato).
- **archivio**: salva, legge, elimina file sotto `ARCHIVIO_FOTO_DIR`.

## 6. Contratti tra moduli
Le sole funzioni di `moduli/<modulo>/service.py` che un altro modulo può chiamare. Ricevono la sessione `db` come primo argomento. Sprint 1 e, in fondo, 2a:

| Modulo | Funzione | Usata da | Scritta in |
|---|---|---|---|
| accesso | `utente_corrente` (dipendenza FastAPI → utente; rinnova la scadenza della sessione) · `richiede_ruolo(*ruoli)` (l'admin passa dove è ammesso l'operatore) | tutti i router | T1-12 (fino ad allora: utente di prova, T1-06; `richiede_ruolo` funziona già da T1-04; l'admin in T1-09) |
| accesso | `crea_utente(email, password, nome, ruolo)` · `cambia_password(email, password)` | `cli.py` | T1-13 |
| accesso | `crea_artigiano(db, email, nome)` → utente e password provvisoria; duplicato → 409, dati non validi → 422 | artigiani | T3-11 MVP |
| artigiani | `profilo_di(utente_id)` → profilo o `None` | campagne, revisione | T1-04 |
| artigiani | `canali_collegati(profilo_id)` → canali con account `collegato` | campagne, pubblicazione | T1-09 |
| artigiani | `profilo(profilo_id)` → profilo o `None` · `post_a_settimana(frequenza)` → post alla settimana per canale (senza frequenza vale `decidete_voi`) | campagne, contenuti | issue #39 |
| campagne | `campagna(id)` · `foto_della_campagna(id)` · `campagne_in_stato(stati)` | contenuti, revisione, pubblicazione | T1-04 |
| campagne | `gruppi_della_campagna(id)` (gruppi con le loro foto) | contenuti, revisione | T1-09 |
| campagne | `cambia_stato(campagna, nuovo)` | contenuti, revisione, pubblicazione | T1-04 |
| campagne | `registra_decisione(campagna, utente_id, esito, motivo, nota, foto_segnate, canale=None, post_id=None)` | revisione | T1-04; `canale`, `post_id` e i nuovi esiti in T1-09 |
| campagne | `aggiorna_foto(foto_id, analisi_ai, n_utilizzi)` | contenuti | T1-04 |
| campagne | `aggiungi_foto(campagna_id, origine, file, mime, larghezza, altezza)` → foto senza gruppo, per le cartoline | contenuti | T1-09 |
| campagne | `post_chiesti(post_a_settimana, inizio, fine)` → post chiesti su un canale (spec R-05); funzione pura, senza `db`: la formula sta solo qui | campagne (dettaglio), contenuti | issue #44 |
| contenuti | `post_della_campagna(campagna_id)` (post con `versione_corrente`, `versioni` e le foto di ogni versione) · `ha_blocchi(campagna_id, adesso)` · `approva_post(campagna_id, adesso)` → versioni approvate | revisione | T1-04; foto delle versioni, scartati, `adesso` in T1-09 |
| contenuti | `piano_corrente(campagna_id)` → piano o `None` · `uscite_della_campagna(campagna_id)` · `ultimo_errore(campagna_id)` → errore di generazione o `None` | revisione | T1-09 |
| contenuti | `post_dovuti(adesso)` (approvati, data raggiunta, campagna attiva) · `segna_esito(post, esito)` · `tutti_chiusi(campagna_id, adesso)` | pubblicazione | T1-04; scartati, scaduti, annullati e `adesso` in T1-09 |
| pubblicazione | `pubblica_dovuti(adesso)` | `tick_pubblicazione` | T1-43 |
| campagne | `foto_di_archivio(profilo_id, canale, adesso)` → lista di `FotoDiArchivio(foto, gruppo, mai_uscita)` | contenuti | firma T2a-01, corpo T2a-22 |
| campagne | `segna_pubblicata(foto_id, canale, quando)` | pubblicazione | firma T2a-01, corpo T2a-22 |
| campagne | `foto_per_id(ids)` → le foto con quegli id, di qualunque campagna o dell'archivio | contenuti, revisione, pubblicazione | T2a-01 |
| campagne | `sistema_foto(dati, canale="instagram", proporzione=None)` → bytes JPEG sistemati (spec R-42, CA-81) | anteprima, pubblicazione | T3-21 |
| campagne | `foto_sistemata(db, foto_id, canale="instagram", proporzione=None)` → `(bytes, "image/jpeg")` | pubblicazione | T3-21 |
| campagne | `url_foto_pubblica(db, foto_id, canale="instagram", durata_secondi=86400, url_base=None)` → str con firma a tempo (spec R-42, CA-81) | pubblicazione | T3-23 |

- Sprint 2a e 2b: le firme le fissava il task di apertura dello sprint. Dallo sprint 3 · MVP una funzione nuova la scrive il task che la usa, nel `service.py` del modulo proprietario, e la aggiunge a questa tabella (ADR-114).
  - **2a (T2a-01)**: le tre righe di campagne qui sopra. `contenuti` non può leggere `pubblicazione`, che viene dopo: per questo dove è uscita una foto sta sulla foto, in `campagne`.
    - `foto_di_archivio()` restituisce le foto `caricata` del profilo che stanno in una campagna chiusa o in un gruppo senza campagna (spec R-27), ordinate per gruppo e per id. Restano fuori le foto non idonee, quelle segnate in una decisione `respinta` e quelle uscite sul canale da meno di 90 giorni (`adesso` meno l'ultima pubblicazione lì). `mai_uscita` vero: la foto conta tra le foto disponibili del canale (R-05); falso: è uscita lì da almeno 90 giorni e vale solo come riempitivo `archivio` (R-28). `gruppo` è il gruppo della foto, con la descrizione per l'AI. Una foto non ancora analizzata è compresa, con `mai_uscita` vero: la generazione la analizza prima del piano e richiama la funzione. `simile_a` non la toglie dall'elenco: lo guarda `contenuti`, come per le foto della campagna.
    - `segna_pubblicata()` scrive `quando` in `foto.pubblicata_su` sotto il canale, senza toccare gli altri; un istante precedente a quello già scritto non lo sostituisce, così due chiamate uguali fanno una sola scrittura. Foto che non esiste → `NonTrovato`. Quali foto segnare (le caricate, non le cartoline) lo decide chi chiama.
    - `foto_per_id()` serve dove un post può avere una foto d'archivio, che `foto_della_campagna()` non restituisce: le foto di una versione (`versione.legami_foto`) in generazione, in Vedi campagna e in pubblicazione si leggono con questa. Un id che non esiste manca dall'elenco, senza errore.
  - **2b (T2b-01)**: notifiche `crea()`; accesso `utente()` e la lettura degli operatori; campagne `campagne_di()`, `togli_canale()`, `ultima_nota()`; contenuti `scarta_post_della_campagna()`, `scarta_post_del_canale()`, `scadi_post()`, `annulla_post()`, `riprogramma_post()`, `modifica_post()`, `segna_controllato()`, `accendi_intervento()`, `puo_rigenerare()`, `ferma_generazione()` (per le campagne ferme da 30 minuti: `errore_generazione` è di contenuti); revisione `scadenze()`. Le firme sono nei `service.py`, con `NotImplementedError` e il task che scrive il corpo (T2b-11, -21, -31…-33, -44); il dettaglio sta nelle loro docstring. Ne seguono le scelte che servono a chi le usa:
    - `notifiche.crea(db, tipo, campagna_id, adesso, *, artigiano_id=None, post_id=None, contenuto=None)` → le notifiche scritte adesso. `contenuto` è un oggetto JSON serializzabile preparato dal chiamante per il testo dell'email; notifiche non legge dati di campagne o post. Per la respinta contiene titolo, motivo, nota e nomi/MIME delle foto segnate; il job legge i byte dall'adattatore archivio e allega miniature. Il tipo decide il destinatario (`notifiche/domain.py`): per i tipi degli operatori `crea()` legge `accesso.operatori()` (operatori e admin attivi), per quelli dell'artigiano usa `artigiano_id`, che chi chiama ha già. Stessa terna destinatario-campagna-tipo e stesso `post_id` → non si scrive due volte (`post_id` serve solo a `post_fallito`: due post falliti sono due eventi). `notifiche` precede `campagne`: per questo `crea()` non cerca l'artigiano della campagna.
    - `campagne.togli_canale(db, campagna, canale)` scrive solo `canali_tolti`: scartare i post del canale (`contenuti.scarta_post_del_canale()`) e registrare la decisione `canale_tolto` tocca a `revisione`. `campagne.ultima_nota(db, campagna_id)` → la decisione `nota` più recente o `None`. `campagne.campagne_di(db, profilo_id, stati=None)` → le campagne di una bottega, dalla più recente.
    - `contenuti.annulla_post(db, campagna_id, post_ids=None)`: senza `post_ids` annulla tutti i post `approvato` (annulla la campagna); con `post_ids` solo quelli (riattiva: gli arretrati che l'operatore non vuole pubblicare adesso; `revisione` calcola gli arretrati con `post_della_campagna()` e rifiuta con 422 un `pubblica_ora` che non lo è).
    - `contenuti.ferma_generazione(db, campagna_id, adesso)` salva l'errore `temporaneo` e porta la campagna a `generazione_fallita` con `campagne.cambia_stato()`.
    - `revisione.scadenze(db, adesso)` per ora non fa niente (T2b-44 ne scrive il corpo): il tick la chiama già, prima di `pubblica_dovuti()`, e i percorsi degli sprint prima lo attraversano.
  - **3 · MVP**: le funzioni nuove le aggiungono i loro task (per esempio la sistemazione delle foto di T3-21 in `campagne`). Le firme del vecchio T3-01 (ritocco, anagrafica, collegamento degli account) sono in roadmap.
- I dati di un altro modulo si leggono solo con le funzioni di questa tabella: niente SQL scritto a mano sulle sue tabelle e niente copie delle sue costanti (`tests/test_confini.py` controlla gli import, non questo).
- Lo stato si passa per nome, `cambia_stato(db, campagna, "attiva")`: il `domain.py` di un altro modulo non si importa. Dentro il modulo proprietario si usano le sue costanti.
- `approva_post(campagna_id, adesso)` porta a `scaduto` i post `da_approvare` con la data passata e approva gli altri; lascia `scartato` e `scaduto` come sono. Se non resta nessun post da approvare solleva `StatoNonValido` e nessun post cambia stato.
- `ha_blocchi(campagna_id, adesso)` è vero se un post `da_approvare` ha `da_rivedere` oppure un intervento in corso partito da meno di 10 minuti (spec R-31).
- `tutti_chiusi(campagna_id, adesso)` è vero quando ogni post è `pubblicato`, `fallito`, `annullato`, `scartato` o `scaduto` e, se c'è un post `fallito`, il periodo della campagna è finito (spec R-34).
- Job accodati per nome: `genera_campagna` da campagne (/invia, /riprova); `rigenera_post` (2b) da revisione; `invia_notifica` da notifiche. Solo questi nomi stanno in `core/coda.py`: i job di ritocco, promemoria e metriche sono in roadmap.
- **Fabbriche di test** in `tests/moduli/<modulo>/fabbrica.py`: `utente(ruolo)`, `profilo()`, `account_social(profilo, piattaforma, stato)`, `campagna_in_bozza()`, `gruppo(campagna, origine)`, `foto(gruppo)`, `campagna_inviata()`, `campagna_con_piano_da_rivedere()`, `campagna_in_revisione()`, `campagna_attiva()`, `piano(campagna)`, `uscita(campagna, gruppo)`, `post_da_approvare()`, `post_approvato()`. Ricevono `db` come primo argomento e fanno `flush`, non `commit`. Ogni utente creato ha la password `PASSWORD_DI_PROVA` (fabbrica di accesso). `profilo()` crea anche gli account collegati dei suoi canali; `campagna_inviata()` e le successive hanno un gruppo con 4 foto. Dalla 2b (T2b-01): `campagna_sospesa()`, `nota_interna(campagna)` (decisione `nota`), `post_fallito()` (in campagna attiva) e `notifica(campagna, utente)`. Dalla 2a (T2a-01): `campagna_conclusa()`, chiusa nell'autunno 2029, con 4 foto idonee e mai pubblicate; `gruppo_di_archivio(profilo_id, n_foto)`, un gruppo senza campagna con `n_foto` foto idonee e mai pubblicate (2 se non si dice); `ANALISI_IDONEA`, l'analisi di una foto che il piano può usare. Dove è uscita una foto lo scrive il test in `foto.pubblicata_su`. Fixture `utente_di_prova(ruolo)` (T1-06) al posto di `utente_corrente` nei test delle API: §7.
- Una firma o una fabbrica si cambia nel task che ne ha bisogno, dicendolo nella PR (ADR-114).

## 7. Base comune
Ciò che ogni modulo trova già pronto: si usa; se va cambiato, la PR la rivede il referente dei file comuni.

| Dove | Cosa | Come si usa |
|---|---|---|
| `core/config.py` | `leggi_impostazioni()` | `leggi_impostazioni().archivio_foto_dir`; mai `os.environ` |
| `core/db.py` | `Base` · `get_db` · `transazione()` | i modelli ereditano da `Base`; la connessione è in UTC; nei router `db: Session = Depends(get_db)`; nei job `with transazione() as db:`. Commit alla fine, rollback se c'è un errore: router, job e service non chiamano `commit` |
| `core/errori.py` | `NonAutenticato` 401 · `NonPermesso` 403 · `NonTrovato` 404 · `StatoNonValido` 409 · `DatiNonValidi` 422 | il service fa `raise NonTrovato("Campagna non trovata.")`; `main.py` risponde `{"detail": …}`. Niente `HTTPException` nei service. Anche il 422 di uno schema esce così (`frase_di_validazione()`): il messaggio in italiano del validatore, se c'è, altrimenti «Dati non validi.» con i campi da controllare, mai i valori ricevuti |
| `core/orologio.py` | `adesso()` (UTC) · `ROMA` | nei router `ora: datetime = Depends(adesso)`, poi passata al service; nei test si passa un'ora fissa. Per le prove a mano `OROLOGIO_GIORNI_AVANTI` la manda avanti in API e worker (mai in produzione) |
| `core/security.py` | `hash_password()` · `verifica_password()` · `genera_token()` · `hash_token()` | scrypt per salvare la password e per verificarla al login; `genera_token()` va nel cookie, `hash_token()` (sha256) in `sessione.token_hash`. Non serve altro scrypt |
| `core/limite_richiesta.py` · `core/limite_login.py` · `core/eventi_sicurezza.py` | limite di 12 MiB per richiesta (413) · limite dei tentativi di login (429) · `X-Request-ID` ed eventi di sicurezza senza dati personali | già montati in `main.py` e nel login: non si richiamano dai moduli. Un router non rifà il controllo della dimensione della richiesta; quello dei 10 MB di una foto (R-13) resta in campagne |
| `core/transizioni.py` | `verifica_transizione(transizioni, da, a)` | `transizioni` è il dizionario stato → stati ammessi del `domain.py` del modulo; se il passaggio non è ammesso solleva `StatoNonValido` |
| `tabelle.py` | importa i `models.py` dei moduli | un `models.py` nuovo viene visto da Alembic senza toccare altro; le tabelle `procrastinate_*` restano fuori dall'autogenerazione (`del_modello()`) |
| `main.py` | router di ogni modulo montato sotto `/api` · `GET /health` · `GET /consorzio` | gli endpoint di plan §3 si scrivono nel `router.py` del modulo, senza `/api` |
| `core/coda.py` | `accoda(nome, …)` · nomi dei job · `app` | `accoda(GENERA_CAMPAGNA, campagna_id=…)` restituisce l'id del job e scrive subito nella coda, fuori dalla transazione di chi chiama: si chiama per ultima. Il job parte dopo `ATTESA_PARTENZA_SECONDI` (3), quando chi l'ha accodato ha salvato, e controlla lo stato quando parte (la richiesta può essere fallita) |
| `worker.py` | importa `tabelle.py` e il `jobs.py` di ogni modulo · `tick_pubblicazione` | un job si scrive nel `jobs.py` del suo modulo: `@app.task(name=GENERA_CAMPAGNA)` su una `def` normale (non `async`), con `app` e il nome presi da `core/coda.py`; dentro, `with transazione() as db:`. Avvio del worker: README |
| `tests/conftest.py` | fixture `db` · `client` · `coda` · `utente_di_prova` | `db`: sessione su `adflow_test`, annullata a fine test anche dopo un commit; `client`: `TestClient` che usa la stessa sessione; `coda`: coda in memoria attiva in ogni test, i job accodati si leggono in `coda.jobs.values()`, ognuno con `task_name` e `args`; `utente_di_prova("operatore", nome=…)`: crea l'utente con la fabbrica e lo rende l'utente autenticato di `client`, anche per `richiede_ruolo()` (ruolo sbagliato → 403); richiamata, lo cambia |

A ogni esecuzione di `pytest` il database `adflow_test` viene svuotato e portato all'ultima migrazione con Alembic: le migrazioni sono provate da ogni test.


### Creazione artigiano MVP (T3-11)

`POST /artigiani` restituisce `{id, email, nome, password_provvisoria}` con
`Cache-Control: no-store`. La password è generata dall'accesso, memorizzata
soltanto come hash e non fa parte delle letture successive dell'utente.
Il primo `GET /profilo` resta 404: l'artigiano compila il proprio profilo.
Poiché `account_social.profilo_id` è obbligatorio, Facebook e Instagram vengono
preparati come nel seed al primo salvataggio del profilo, nella stessa
transazione; le modifiche successive preservano gli account già esistenti.
