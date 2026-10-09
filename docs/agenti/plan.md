# Plan · come è fatto

Ogni tabella nasce già nella forma definitiva, nello sprint indicato. Le tabelle dello sprint 1 già su `main` si riallineano una volta, con T1-08 (§2). Cartelle e regole dei moduli: `constitution.md` §2. Vincoli: regole R-xx di `spec.md` §5.

## 1. Stack e configurazione
Python 3.11+ · FastAPI · Pydantic · SQLAlchemy 2 + Alembic · PostgreSQL 16 · Procrastinate (coda e job in PostgreSQL) · LiteLLM (AI; primo provider OpenAI; provider `finto` per sviluppo e test) · React + Vite + TypeScript + Mantine · pytest. Social simulato; email verso un catcher locale (Mailpit). Sessione con cookie httpOnly. Driver psycopg 3: gli indirizzi iniziano con `postgresql+psycopg://`. Le versioni stanno in `backend/requirements.txt`; l'ambiente virtuale è `.venv` nella radice. Cosa offre già il codice comune: §7.

`backend/.env` (ogni variabile è un campo di `core/config.py`, in minuscolo):
```
DATABASE_URL · DATABASE_URL_TEST · ARCHIVIO_FOTO_DIR · RICHIESTA_MAX_BYTE=12582912
AI_PROVIDER=finto|litellm · AI_MODELLO_VISIONE · AI_MODELLO_TESTO · OPENAI_API_KEY
ANTICIPO_MINIMO_GIORNI=3 · MARGINE_SLOT_MINUTI=15 · SMTP_HOST · SMTP_PORT
SESSIONE_ARTIGIANO_GIORNI=7 · SESSIONE_OPERATORE_ORE=12 · CONSORZIO_NOME · CONSORZIO_TELEFONO · CONSORZIO_EMAIL
AMBIENTE=sviluppo|test|produzione · LOGIN_LIMITE_TENTATIVI=5 · LOGIN_FINESTRA_SECONDI=900 · LOGIN_LIMITE_SEGRETO · EMAIL_TEST_ENVIRONMENT · COOKIE_SECURE
```

## 2. Modello dati
| Tabella | Modulo | Campi | Sprint |
|---|---|---|---|
| utente | accesso | email (unica), password_hash, nome, ruolo (artigiano / operatore / admin), attivo, deve_cambiare_password (bool; usato dallo sprint 3) | 1 |
| sessione | accesso | token_hash (sha256), utente_id, scade_il (spostata in avanti a ogni richiesta, spec R-29) | 1 |
| profilo_bottega | artigiani | utente_id (1:1), nome, referente, citta, anni_attivita, sito, storia, origine, valori[], tipo_prodotto, gamma, fascia_prezzo, stagionalita, clienti_ideali, obiettivo, zona, tono[], cortesia, vincoli, canali[] (proposta iniziale per le campagne), frequenza (per canale), orari (JSON), social_esistenti (JSON `{canali[], profili, cosa_funziona}`), foto_policy (JSON `{quantita_mese, chi_scatta, persone}`), eventi_ricorrenti (JSON `[{nome, quando, tipo}]`), chiusure, logo (file, facoltativo), aggiornato_il · obbligatori: nome, referente, citta, tipo_prodotto, clienti_ideali, obiettivo, canali | 1 (seed; schermate 2a) |
| account_social | artigiani | profilo_id, piattaforma, id_pagina, permesso (cifrato), scadenza, stato · unico su (profilo_id, piattaforma) | 1 (seed; collegamento dall'operatore 3) |
| campagna | campagne | profilo_id, titolo, inizio, fine, descrizione, stato, canali[] (dichiarati in bozza), canali_tolti[], frequenza, obiettivo, profilo_snapshot (JSON), inviata_il, chiusa_il | 1 |
| gruppo_foto | campagne | profilo_id, campagna_id (facoltativa: vuota = gruppo dell'archivio, caricato dal profilo), origine, descrizione, da_usare_il (data, facoltativa), n_immagini (solo `create_ai`) | 1 |
| foto | campagne | profilo_id, campagna_id (facoltativa, come il suo gruppo), gruppo_id (→ gruppo_foto; facoltativo: vuoto per cartoline e immagini AI senza gruppo), origine (default `caricata`), file, mime, larghezza, altezza, da_usare (bool, la stella), analisi_ai (JSON `{idonea, simile_a, tipo, punteggio, motivo, soggetto}`), n_utilizzi, pubblicata_su (JSON `{canale: data dell'ultima pubblicazione}`; dalla 2a, la scrive la pubblicazione con `segna_pubblicata()`) | 1 |
| decisione_campagna | campagne | campagna_id, utente_id, esito, motivo, nota, foto_segnate[], canale (solo `canale_tolto`), post_id (solo `riprogrammato`), creata_il | 1 (`approvata`, `proseguita`), 2b |
| piano | contenuti | campagna_id, numero, strategia (testo), contenuto (JSON, come lo ha scritto l'AI), esito_controllo (JSON), debole (bool), provider_ai, modello_ai, versione_prompt, creata_il · unico su (campagna_id, numero) | 1 |
| uscita | contenuti | campagna_id, gruppo_id (facoltativo: vuoto per cartoline e immagini AI senza gruppo), numero, tema · unico su (campagna_id, numero) | 1 |
| post | contenuti | campagna_id, uscita_id, canale, formato, riempitivo (facoltativo), data_ora, stato, da_rivedere (bool), n_rigenerazioni_testo · n_ritocchi_foto (3), controllato_da (utente, facoltativo) · controllato_il (2b), intervento_in_corso (tipo, facoltativo) · intervento_dal (2b) · unico su (uscita_id, canale) | 1 |
| versione_post | contenuti | post_id, numero, testo, hashtag[], tipo_intervento, autore_id (utente; vuoto = AI), testo_proposto, nota, provider_ai, modello_ai, versione_prompt (i tre facoltativi), errori_validazione (JSON `[{livello, regola, messaggio}]`), creata_il · unico su (post_id, numero) | 1 |
| versione_post_foto | contenuti | versione_id, posizione, foto_id · versione_foto_id (3) · unico su (versione_id, posizione) | 1 |
| versione_foto | contenuti | foto_id, numero (0 = originale), file, origine (originale / ritocco_ai), nota, provider_ai, modello_ai, versione_prompt, creata_il | 3 |
| errore_generazione | contenuti | campagna_id, tipo, messaggio, tappa, canale (facoltativo), creata_il | 1 |
| approvazione | revisione | versione_id, utente_id, ruolo, esito, creata_il | 1 |
| pubblicazione | pubblicazione | post_id, versione_id, n_tentativo, stato (in_corso / ok / errore), id_esterno, errore, creata_il · indice unico parziale su `ok` per post · unico su (post_id, n_tentativo) | 1 |
| metrica | pubblicazione | pubblicazione_id, data_rilevazione, like, commenti, copertura, salvataggi | 4 |
| notifica | notifiche | utente_id, campagna_id, tipo (`campagna_respinta`, `campagna_scaduta`, `campagna_sospesa`, `campagna_pronta`, `piano_da_rivedere`, `generazione_fallita`, `post_fallito`, `campagna_conclusa`, …), canale, stato_invio, creata_il, inviata_il | 2b |
| anagrafica_artigiano | artigiani | utente_id (1:1), codice (unico, es. ART-0042), codice_consorzio, nome_bottega, referente, citta, telefono, stato_iscrizione, iscritto_il | 3 |

La versione corrente di un post è l'ultima; il piano corrente è l'ultimo. Versioni, piani, decisioni ed errori di generazione non si cancellano mai. `post.da_rivedere` è vero quando la versione corrente ha almeno un errore di livello `blocco`. Le note interne sono decisioni con esito `nota`. `campagna.chiusa_il` si scrive quando la campagna entra in uno stato chiuso. Un post nasce con il piano, senza versioni: la versione 1 arriva con il testo, e le sue foto sono quelle che il piano gli ha dato. Nel contratto Python `versione.legami_foto` è la lista dei record `VersionePostFoto`, ordinati per `posizione`, con `foto_id`: non contiene direttamente gli oggetti `Foto` di un altro modulo.

**Archivio e riempitivi** (spec R-27, R-28): le tabelle nascono già pronte, con campagna facoltativa su `gruppo_foto` e `foto`, gruppo facoltativo su `foto` e `uscita`, `profilo_bottega.logo`, `post.riempitivo`. Nello sprint 1 ogni gruppo e ogni foto hanno la loro campagna, e l'unico riempitivo è la `cartolina`: un'uscita senza gruppo, e una foto con origine `cartolina`, senza gruppo, creata dalla generazione e data alla versione 1 del post. Lo controllano i service, non il database.

Migrazioni dello sprint 1: 001 accesso, 002 artigiani, 003 campagne, 004 contenuti, 005 revisione, 006 pubblicazione (T1-03); 007 coda, le tabelle `procrastinate_*` con lo schema di `procrastinate==3.10.0` (T1-05; cambiare versione richiede una migrazione nuova con gli script di aggiornamento di Procrastinate); 008 riallineamento alle tabelle qui sopra (T1-08); 009 `limite_login` (chiave, tentativi, scade_il: i contatori dei tentativi di accesso, issue #16; la usa solo `core/limite_login.py`, senza `models.py`). I file delle migrazioni 002–004 conservano la forma precedente, che la 008 corregge: `foto.gruppo_id` come uuid senza tabella, `foto.descrizione`, `campagna.crea_immagini_ai`, `versione_post.foto_id`, `foto.campagna_id` obbligatorio, `campagna.rimandata`, e mancano `account_social`, `gruppo_foto`, `piano`, `uscita`, `versione_post_foto`, `errore_generazione`, `profilo_bottega.logo`, `post.riempitivo`, la spunta e l'intervento in corso sul post, `versione_post.autore_id`, `decisione_campagna.post_id`, `campagna.chiusa_il`, `utente.deve_cambiare_password`. Una migrazione scrive lo schema per esteso, senza importare i `models.py`. Ogni migrazione successiva è un task della corsia 0. Previste, una per apertura di sprint: 010 `foto.pubblicata_su` (T2a-01); 011 `notifica` (T2b-01); 012 `versione_foto`, `versione_post_foto.versione_foto_id`, `post.n_ritocchi_foto` e `anagrafica_artigiano` (T3-01).

**Transizioni** (`campagne/domain.py` per la campagna, `contenuti/domain.py` per il post):
- campagna: bozza → inviata → in_generazione → in_revisione → attiva → conclusa · in_generazione → piano_da_rivedere → in_generazione / respinta · inviata / in_generazione → generazione_fallita → inviata · in_revisione → respinta · inviata / in_generazione / piano_da_rivedere / generazione_fallita / in_revisione → scaduta · attiva ⇄ sospesa · attiva / sospesa → annullata
- post: da_approvare → approvato → pubblicato / fallito / annullato · fallito → approvato · da_approvare → scaduto · da_approvare → scartato
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
| Sprint | Modulo | Metodo e percorso | Ruolo | Esito |
|---|---|---|---|---|
| 1 | `main.py` | GET /health · GET /consorzio | tutti, senza sessione | `{"stato":"ok"}` · `{nome, telefono, email}` dalla configurazione |
| 1 | accesso | POST /auth/login · POST /auth/logout · GET /auth/me | tutti / autenticato | 200 + cookie `adflow_sessione` · 204 · 200; durata della sessione per ruolo, rinnovata a ogni richiesta (R-29) |
| 1 | artigiani | GET /canali | artigiano | `[{canale, collegato}]` per i canali dell'MVP |
| 1 | campagne | GET /campagne?stato= (ripetibile) | autenticato | l'artigiano vede solo le sue; all'operatore ogni campagna porta anche `bottega` e `citta`, dal profilo |
| 1 | campagne | POST /campagne `{titolo,inizio,fine,descrizione,canali[]}` | artigiano | 201 bozza · 409 R-12 · 422 R-08, R-22 |
| 1 | campagne | GET /campagne/{id} | proprietario, operatore | campagna, gruppi con le loro foto, `post_chiesti_per_canale`, `avvisi[]` (R-25) (senza post); all'operatore anche snapshot e decisioni, note interne comprese |
| 1 | campagne | POST /campagne/{id}/gruppi `{origine, descrizione, da_usare_il, n_immagini}` | artigiano | 201 · solo in bozza · 422 R-13 |
| 1 | campagne | PUT /campagne/{id}/gruppi/{gruppo_id} `{descrizione, da_usare_il, n_immagini}` | artigiano | solo in bozza · 422 R-13 |
| 1 | campagne | POST /campagne/{id}/foto (multipart: file, gruppo_id; entrambi obbligatori) | artigiano | 201 · solo in bozza, solo in un gruppo `caricate` già creato · 422 R-13 o senza gruppo |
| 1 | campagne | PUT /foto/{id} `{da_usare}` | artigiano | la stella · solo in bozza |
| 1 | campagne | DELETE /foto/{id} · DELETE /campagne/{id}/gruppi/{gruppo_id} | artigiano | 204 · solo in bozza |
| 1 | campagne | GET /foto/{id}/file | proprietario, operatore | immagine |
| 1 | campagne | POST /campagne/{id}/invia | artigiano | → inviata + job `genera_campagna`; 409 senza profilo o con un canale non collegato (R-22); 422 R-08, R-13 |
| 1 | campagne | POST /campagne/{id}/riprova | operatore | generazione_fallita → inviata + job |
| 1 | revisione | GET /campagne/{id}/post?stato= | operatore | in ogni stato dopo l'invio: piano corrente (strategia, esito del controllo, debole) o niente se non c'è ancora, uscite (tema, gruppo e data del gruppo) con i post dei canali (tipo di riempitivo, versione corrente con foto, autore, blocchi e avvisi, storico; dalla 2b spunta e intervento in corso), foto non usate per gruppo con il motivo, `ultimo_errore` della generazione (R-35) |
| 1 | revisione | POST /campagne/{id}/prosegui | operatore | piano_da_rivedere → in_generazione + job, decisione `proseguita` · 409 se il piano non ha post (R-20) |
| 1 | revisione | POST /campagne/{id}/approva | operatore | → attiva, post `da_approvare` approvati (quelli con la data passata scaduti), righe approvazione + decisione · 409 R-14 |
| 2a | artigiani | GET /profilo · PUT /profilo | artigiano | 404 se assente · upsert, 422 obbligatori |
| 2a | campagne | PATCH /campagne/{id} | artigiano | solo in bozza, stessi controlli della creazione; anche `canali[]` |
| 2a | artigiani | PUT /profilo/logo (multipart: file) · GET /profilo/logo · DELETE /profilo/logo | artigiano | il logo della bottega (spec R-40) · 404 senza profilo o senza logo · 422 R-40. La forma esatta la fissa T2a-01 |
| 2a | campagne | GET /archivio · POST /archivio/gruppi · POST /archivio/foto (multipart) · DELETE di foto e gruppo d'archivio | artigiano | gruppi e foto senza campagna, per l'archivio della bottega (spec R-27) · 422 R-13 · 404 per l'archivio di un altro. La forma esatta la fissa T2a-01 |
| 2b | revisione | GET /da-approvare | operatore | le campagne di tutti gli artigiani negli stati "da approvare" (spec §4), con bottega e città, conteggi dei post (totale, da approvare, da rivedere, riempitivi per canale), `entro_quando` e ultima nota interna, ordinate per `entro_quando` (R-38) |
| 2b | revisione | POST /campagne/{id}/nota `{nota}` | operatore | in ogni stato dopo l'invio: decisione `nota`, nessuna email · 422 senza nota (R-32) |
| 2b | revisione | POST /campagne/{id}/respingi `{motivo, nota, foto_segnate[]}` | operatore | da in_revisione o piano_da_rivedere → respinta, post scartati, decisione, notifica · 422 R-18 o foto di altra campagna |
| 2b | revisione | POST /campagne/{id}/togli-canale `{canale, nota}` | operatore | in generazione_fallita, piano_da_rivedere o in_revisione: post del canale scartati, canale in `canali_tolti`, decisione `canale_tolto`; da generazione_fallita, se resta un canale, riparte il job · 409 se è l'ultimo canale · 422 senza nota |
| 2b | revisione | POST /campagne/{id}/sospendi · /riattiva `{pubblica_ora[]}` · /annulla | operatore | R-33; decisione per ognuna · 409 fuori dalle transizioni · 422 se `pubblica_ora` contiene un post non in arretrato |
| 2b | revisione | POST /post/{id}/modifica `{testo, hashtag[]}` | operatore | solo in_revisione: versione `modifica_operatore` · 409 R-16, R-31 · 422 R-30 |
| 2b | revisione | POST /post/{id}/controllato `{valore}` | operatore | mette o toglie la spunta (R-30) · 409 fuori da in_revisione o su un post `da_rivedere` |
| 2b | revisione | POST /post/{id}/rigenera `{modalita, testo_proposto, nota}` | operatore | `totale` o `da_proposta`; solo in_revisione; stesse foto; accende l'intervento in corso + job · 409 R-03, R-16, R-31 · 422 `da_proposta` senza testo |
| 2b | revisione | POST /post/{id}/riprogramma `{data_ora}` | operatore | post `fallito` in campagna attiva o sospesa → `approvato`, decisione `riprogrammato` · 409 se non è fallito · 422 R-34 |
| 3 | accesso | POST /auth/cambia-password `{password_attuale, password_nuova}` | autenticato | 204; spegne `deve_cambiare_password`. Finché è acceso ogni altra chiamata dell'utente → 403 (R-37) |
| 3 | revisione | GET /artigiani · GET /artigiani/{id} | operatore | elenco (R-38); dettaglio per sezioni (spec §4): campagne da approvare, in corso, le ultime 3 chiuse e il totale delle chiuse |
| 3 | campagne | GET /campagne?artigiano=&stato= | operatore | filtro per artigiano, per la pagina delle campagne chiuse |
| 3 | artigiani | POST /artigiani · PUT /artigiani/{id}/anagrafica | operatore | creazione (201 con la password provvisoria, una sola volta), anagrafica · 422 R-37 |
| 3 | artigiani | POST /artigiani/{id}/password-provvisoria | operatore | nuova password provvisoria, mostrata una sola volta |
| 3 | artigiani | POST /artigiani/{id}/social/{piattaforma}/collega | operatore | collegamento (simulato) |
| 3 | revisione | POST /post/{id}/ritocca-foto `{nota}` | operatore | solo in_revisione; intervento in corso + job · 409 R-03, R-31 |
| 3 | revisione | POST /post/{id}/scegli-foto `{versione_foto_id}` | operatore | originale o precedente; non consuma cicli |
| 3 | revisione | POST /post/{id}/cambia-foto `{foto_id}` | operatore | versione `cambio_foto` · 422 R-36 |
| 3 | revisione | POST /post/{id}/sposta `{data_ora}` | operatore | nuova data, spunta azzerata · 422 R-36 |
| 3 | contenuti | GET /campagne/{id}/calendario | proprietario, operatore | strategia del piano e soli post approvati, pubblicati, falliti o annullati (data, canale, stato, testo e foto della versione corrente); canali tolti con la nota; numero dei post scaduti · 409 prima dell'approvazione |
| 4 | pubblicazione | GET /metriche?artigiano=&campagna=&dal=&al= | operatore; artigiano solo le sue | metriche (R-39) |

Per ogni percorso: una richiesta oltre `RICHIESTA_MAX_BYTE` (12 MiB: i 10 MB di una foto più il margine del multipart) riceve 413 prima di arrivare al router; `POST /auth/login` oltre il limite dei tentativi riceve 429 con `Retry-After`.

Non esistono: approvazione, scarto o annullamento del singolo post; togliere un'uscita; `rimanda`. Non esistono ancora, finché i loro task non sono su `main`: logo e archivio della bottega (2a: T2a-12, T2a-22).

## 4. Job
| Sprint | Modulo | Job | Quando | Cosa fa |
|---|---|---|---|---|
| 1 | contenuti | `genera_campagna(campagna_id)` | da /invia, /riprova, /prosegui; 3 esecuzioni, 30 s | A tappe, ognuna in una sua transazione e saltata se è già fatta (R-24). ① `inviata` → `in_generazione` ② analisi dei gruppi `caricate` non ancora analizzati → `aggiorna_foto()`; una foto con la stella non resta `simile_a` (R-23) ③ se manca il piano: piano dell'AI con lo snapshot, controllo (R-05, R-08, R-09, R-23, R-28), righe `piano`, `uscita`, `post` con il loro `riempitivo`; se è debole (R-20) → `piano_da_rivedere` e fine ④ per ogni post `cartolina` senza immagine: la compone, la salva con l'adattatore archivio e crea la foto con `campagne.service.aggiungi_foto()`; (dal 3) ritocco delle foto del piano → `versione_foto` 1 ⑤ per ogni post senza versione: testo, validatore (R-09), versione 1 con le sue foto ⑥ `in_revisione`. Salta i canali in `canali_tolti`. Errori (R-35): ogni errore che ferma l'esecuzione si salva in `errore_generazione`; `temporaneo` e `risposta` → nuova esecuzione, alla terza `generazione_fallita`; `configurazione` → `generazione_fallita` subito; `richiesta` o `rifiuto` su una foto → foto non idonea con il motivo, sul testo di un post → versione vuota con un blocco, e si continua. (2b) Notifica agli operatori a `piano_da_rivedere`, a `in_revisione` e a `generazione_fallita` |
| 1 | `worker.py` | `tick_pubblicazione` | ogni minuto, uno alla volta | (2b) `revisione.scadenze()`: scadenza morbida R-06 e campagne ferme da 30 minuti R-35; poi `pubblicazione.pubblica_dovuti()`: tentativo registrato → pubblica con tutte le foto → esito, (2b) notifica agli operatori per un post `fallito`; campagna conclusa secondo R-34; (3) sospensione R-07 |
| 2b | contenuti | `rigenera_post(post_id)` | da /rigenera; 3 esecuzioni | non fa nulla se la campagna non è `in_revisione` o il post non è `da_approvare`; nuovo testo, stesse foto, versioni rifiutate come contesto, validatore; conta il ciclo e spegne l'intervento in corso quando nasce la versione; alla terza esecuzione fallita spegne l'intervento senza contare il ciclo (R-31) |
| 2b | notifiche | `invia_notifica(notifica_id)` | alla creazione; 3 tentativi | email via adattatore, aggiorna `stato_invio` |
| 3 | contenuti | `ritocca_foto(post_id)` | da /ritocca-foto; 3 esecuzioni | nuova `versione_foto` e nuova versione del post; stesse regole di R-31 |
| 3 | revisione | `promemoria` | ogni ora | email all'operatore per le campagne `in_revisione` o `piano_da_rivedere`, R-06, una volta per campagna |
| 4 | pubblicazione | `raccogli_metriche` · `report_settimanale` | giorno · settimana | metriche; email di riepilogo agli operatori; all'artigiano un riepilogo quando la campagna è `conclusa` (R-39) |

I nomi dei job stanno in `core/coda.py`; un job di un altro modulo si accoda con `accoda(nome, …)`, senza importarlo. Il job parte anche trovando la campagna già `in_generazione` (nuova esecuzione o Prosegui): riprende dalla prima tappa non fatta. Con un piano già salvato non si ferma di nuovo per il piano debole.

## 5. Adattatori
Ognuno in `adapters/<nome>/`: interfaccia, implementazione finta, implementazione reale.
- **ai**: `analizza_gruppo()` (le foto di un gruppo con la sua descrizione → per ogni foto `idonea`, `simile_a`, `tipo`, `punteggio`, `motivo`, `soggetto`), `pianifica_campagna()` (snapshot, campagna, gruppi analizzati, limiti per canale, schede dei canali → strategia, uscite e post per canale con formato, foto, data e ora), `genera_post()` (un post del piano → testo e hashtag per il suo canale), `ritocca_immagine()` (3); `crea_immagine()` non ancora pianificata (spec R-19). Le cartoline non passano dall'AI: le compone `contenuti` (spec R-28). Ogni errore esce dall'adattatore come `ErroreAI` con il suo `tipo` (R-35) e un messaggio per l'operatore: è l'adattatore a tradurre gli errori del provider. Provider da `AI_PROVIDER`; piano e versioni salvano provider, modello e versione del prompt. Prompt in `adapters/ai/prompts/`; quello del piano è scritto da social media manager. Il provider finto dà sempre lo stesso piano a parità di dati: una foto per post, tutte le foto disponibili fino ai post chiesti, poi cartoline per i post che mancano, date distribuite sul periodo, Instagram il giorno dopo Facebook; carosello ed errori, di ogni tipo, a comando.
- **social**: `collega_account()`, `pubblica()` (testo, hashtag e una o più foto), `leggi_metriche()`; simulato e Meta.
- **email**: `invia()`; catcher locale in sviluppo.
- **archivio**: salva, legge, elimina file sotto `ARCHIVIO_FOTO_DIR`.

## 6. Contratti tra moduli
Le sole funzioni di `moduli/<modulo>/service.py` che un altro modulo può chiamare. Ricevono la sessione `db` come primo argomento. Sprint 1:

| Modulo | Funzione | Usata da | Scritta in |
|---|---|---|---|
| accesso | `utente_corrente` (dipendenza FastAPI → utente; rinnova la scadenza della sessione) · `richiede_ruolo(*ruoli)` (l'admin passa dove è ammesso l'operatore) | tutti i router | T1-12 (fino ad allora: utente di prova, T1-06; `richiede_ruolo` funziona già da T1-04; l'admin in T1-09) |
| accesso | `crea_utente(email, password, nome, ruolo)` · `cambia_password(email, password)` | `cli.py` | T1-13 |
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

- Sprint successivi: le firme le fissa il task di apertura dello sprint, della corsia 0, che le scrive nei `service.py` con `NotImplementedError` e in questa tabella.
  - **2a (T2a-01)**: campagne `foto_di_archivio(profilo_id, canale, adesso)` (usata da contenuti) e `segna_pubblicata(foto_id, canale, quando)` (usata da pubblicazione). `contenuti` non può leggere `pubblicazione`, che viene dopo: per questo dove è uscita una foto sta sulla foto, in `campagne`.
  - **2b (T2b-01)**: notifiche `crea()`; accesso `utente()` e la lettura degli operatori; campagne `campagne_di()`, `togli_canale()`, `ultima_nota()`; contenuti `scarta_post_della_campagna()`, `scarta_post_del_canale()`, `scadi_post()`, `annulla_post()`, `riprogramma_post()`, `modifica_post()`, `segna_controllato()`, `accendi_intervento()`, `puo_rigenerare()`, `ferma_generazione()` (per le campagne ferme da 30 minuti: `errore_generazione` è di contenuti); revisione `scadenze()`.
  - **3 (T3-01)**: accesso `password_provvisoria()`; artigiani `account_social()`, `anagrafica_di()`; contenuti `puo_ritoccare()`, `scegli_foto()`, `cambia_foto()`, `sposta_post()`; negli adattatori `ritocca_immagine()` (AI) e `collega_account()` (social).
- I dati di un altro modulo si leggono solo con le funzioni di questa tabella: niente SQL scritto a mano sulle sue tabelle e niente copie delle sue costanti (`tests/test_confini.py` controlla gli import, non questo).
- Lo stato si passa per nome, `cambia_stato(db, campagna, "attiva")`: il `domain.py` di un altro modulo non si importa. Dentro il modulo proprietario si usano le sue costanti.
- `approva_post(campagna_id, adesso)` porta a `scaduto` i post `da_approvare` con la data passata e approva gli altri; lascia `scartato` e `scaduto` come sono. Se non resta nessun post da approvare solleva `StatoNonValido` e nessun post cambia stato.
- `ha_blocchi(campagna_id, adesso)` è vero se un post `da_approvare` ha `da_rivedere` oppure un intervento in corso partito da meno di 10 minuti (spec R-31).
- `tutti_chiusi(campagna_id, adesso)` è vero quando ogni post è `pubblicato`, `fallito`, `annullato`, `scartato` o `scaduto` e, se c'è un post `fallito`, il periodo della campagna è finito (spec R-34).
- Job accodati per nome: `genera_campagna` da campagne (/invia, /riprova) e da revisione (/prosegui); `rigenera_post` (2b) e `ritocca_foto` (3) da revisione.
- **Fabbriche di test** in `tests/moduli/<modulo>/fabbrica.py`, della corsia 0: `utente(ruolo)`, `profilo()`, `account_social(profilo, piattaforma, stato)`, `campagna_in_bozza()`, `gruppo(campagna, origine)`, `foto(gruppo)`, `campagna_inviata()`, `campagna_con_piano_da_rivedere()`, `campagna_in_revisione()`, `campagna_attiva()`, `piano(campagna)`, `uscita(campagna, gruppo)`, `post_da_approvare()`, `post_approvato()`. Ricevono `db` come primo argomento e fanno `flush`, non `commit`. Ogni utente creato ha la password `PASSWORD_DI_PROVA` (fabbrica di accesso). `profilo()` crea anche gli account collegati dei suoi canali; `campagna_inviata()` e le successive hanno un gruppo con 4 foto. Fixture `utente_di_prova(ruolo)` (T1-06) al posto di `utente_corrente` nei test delle API: §7.
- Una firma o una fabbrica si cambia solo con un task della corsia 0.

## 7. Base comune (T1-01)
Ciò che ogni modulo trova già pronto. È della corsia 0: si usa, non si cambia.

| Dove | Cosa | Come si usa |
|---|---|---|
| `core/config.py` | `leggi_impostazioni()` | `leggi_impostazioni().archivio_foto_dir`; mai `os.environ` |
| `core/db.py` | `Base` · `get_db` · `transazione()` | i modelli ereditano da `Base`; la connessione è in UTC; nei router `db: Session = Depends(get_db)`; nei job `with transazione() as db:`. Commit alla fine, rollback se c'è un errore: router, job e service non chiamano `commit` |
| `core/errori.py` | `NonAutenticato` 401 · `NonPermesso` 403 · `NonTrovato` 404 · `StatoNonValido` 409 · `DatiNonValidi` 422 | il service fa `raise NonTrovato("Campagna non trovata.")`; `main.py` risponde `{"detail": …}`. Niente `HTTPException` nei service |
| `core/orologio.py` | `adesso()` (UTC) · `ROMA` | nei router `ora: datetime = Depends(adesso)`, poi passata al service; nei test si passa un'ora fissa |
| `core/security.py` | `hash_password()` · `verifica_password()` · `genera_token()` · `hash_token()` | scrypt per salvare la password e per verificarla al login; `genera_token()` va nel cookie, `hash_token()` (sha256) in `sessione.token_hash`. Non serve altro scrypt |
| `core/limite_richiesta.py` · `core/limite_login.py` · `core/eventi_sicurezza.py` | limite di 12 MiB per richiesta (413) · limite dei tentativi di login (429) · `X-Request-ID` ed eventi di sicurezza senza dati personali | già montati in `main.py` e nel login: non si richiamano dai moduli. Un router non rifà il controllo della dimensione della richiesta; quello dei 10 MB di una foto (R-13) resta in campagne |
| `core/transizioni.py` | `verifica_transizione(transizioni, da, a)` | `transizioni` è il dizionario stato → stati ammessi del `domain.py` del modulo; se il passaggio non è ammesso solleva `StatoNonValido` |
| `tabelle.py` | importa i `models.py` dei moduli | un `models.py` nuovo viene visto da Alembic senza toccare altro; le tabelle `procrastinate_*` restano fuori dall'autogenerazione (`del_modello()`) |
| `main.py` | router di ogni modulo montato sotto `/api` · `GET /health` · `GET /consorzio` | gli endpoint di plan §3 si scrivono nel `router.py` del modulo, senza `/api` |
| `core/coda.py` | `accoda(nome, …)` · nomi dei job · `app` | `accoda(GENERA_CAMPAGNA, campagna_id=…)` restituisce l'id del job e scrive subito nella coda, fuori dalla transazione di chi chiama: si chiama per ultima, e il job controlla lo stato quando parte (la richiesta può essere fallita o non ancora conclusa) |
| `worker.py` | importa il `jobs.py` di ogni modulo · `tick_pubblicazione` | un job si scrive nel `jobs.py` del suo modulo: `@app.task(name=GENERA_CAMPAGNA)` su una `def` normale (non `async`), con `app` e il nome presi da `core/coda.py`; dentro, `with transazione() as db:`. Avvio del worker: README |
| `tests/conftest.py` | fixture `db` · `client` · `coda` · `utente_di_prova` | `db`: sessione su `adflow_test`, annullata a fine test anche dopo un commit; `client`: `TestClient` che usa la stessa sessione; `coda`: coda in memoria attiva in ogni test, i job accodati si leggono in `coda.jobs.values()`, ognuno con `task_name` e `args`; `utente_di_prova("operatore", nome=…)`: crea l'utente con la fabbrica e lo rende l'utente autenticato di `client`, anche per `richiede_ruolo()` (ruolo sbagliato → 403); richiamata, lo cambia |

A ogni esecuzione di `pytest` il database `adflow_test` viene svuotato e portato all'ultima migrazione con Alembic: le migrazioni sono provate da ogni test.
