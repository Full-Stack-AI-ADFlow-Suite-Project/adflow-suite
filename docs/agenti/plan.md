# Plan · come è fatto

Versione corta (ADR-122): la mappa per orientarsi nel codice, che resta la fonte. Il testo completo (campi di ogni tabella, esiti di ogni rotta, note sulle funzioni tra moduli) è in `docs/archivio/completi/plan.md`; le API vive sono documentate da FastAPI su `/docs`. Cartelle e regole dei moduli: `constitution.md` §2. Regole R-xx: `spec.md` §5.

**Stato**: `MVP` = nel prodotto; `congelato` = codice e test restano, l'interfaccia lo nasconde, non si estende; `fuori MVP` = non c'è (`docs/archivio/fuori-mvp.md`, `docs/ROADMAP.md`).

## 1. Stack e configurazione
Python 3.11+ · FastAPI · Pydantic · SQLAlchemy 2 + Alembic · PostgreSQL 16 (driver psycopg 3, `postgresql+psycopg://`) · Procrastinate (coda e job in PostgreSQL) · LiteLLM (AI; provider `finto` per sviluppo e test) · React + Vite + TypeScript + Mantine · pytest. Social `finto` o `meta`, su una pagina di prova; email verso Mailpit. Sessione con cookie httpOnly.

Ogni variabile di `backend/.env` è un campo di `core/config.py` ed è in `.env.example` con un valore finto: database, archivio foto, AI (`AI_PROVIDER`, modelli, chiavi, prezzi), Meta (`SOCIAL_PROVIDER`, pagina, token, `FOTO_URL_PUBBLICO`), tempi (`ANTICIPO_MINIMO_GIORNI=3`, `MARGINE_SLOT_MINUTI=15`, `OROLOGIO_GIORNI_AVANTI=0`, durate delle sessioni), consorzio, sicurezza (`AMBIENTE`, limiti del login, `LOGIN_LIMITE_SEGRETO`, `COOKIE_SECURE`: `backend/README.md`, sezione In produzione).

## 2. Modello dati
| Modulo | Tabelle |
|---|---|
| accesso | `utente` (email unica, password_hash, ruolo artigiano / operatore / admin, attivo) · `sessione` (token_hash sha256, scade_il rinnovata) · `limite_login` (migrazione 009, solo `core/limite_login.py`) |
| artigiani | `profilo_bottega` (1:1 con l'utente: i campi dei passi 1–9, frequenza, foto_policy, eventi in JSON) · `account_social` (unico per profilo e piattaforma; nell'MVP dice solo se un canale è collegato) |
| campagne | `campagna` (periodo, stato, canali[], canali_tolti[], frequenza, obiettivo, profilo_snapshot) · `gruppo_foto` (campagna facoltativa: vuota = archivio) · `foto` (origine `caricata` / `creata_ai` / `cartolina`, analisi_ai JSON, pubblicata_su JSON per canale) · `decisione_campagna` (esito, motivo, nota, foto_segnate[], canale, post_id: la storia di approvazioni, respinte, interventi e richieste) |
| contenuti | `piano` · `uscita` (tema, gruppo) · `post` (canale, data_ora, stato, riempitivo, da_rivedere, n_rigenerazioni_testo, intervento_in_corso) · `versione_post` (testo, hashtag, tipo_intervento, autore, errori_validazione) · `versione_post_foto` · `chiamata_ai` (costo, prompt, richiesta, risposta, esito, durata: 012 e 013) · `valutazione_ai` · `errore_generazione` |
| revisione | `approvazione` (versione, utente, esito) |
| pubblicazione | `pubblicazione` (tentativo, stato `in_corso` / `ok` / `errore`, id_esterno, chiamata_il: 014; un solo `ok` per post) |
| notifiche | `notifica` (congelata: righe ed email al catcher locale) |

Nulla si cancella: versioni, piani, decisioni ed errori restano. La versione corrente di un post è l'ultima; il piano corrente è l'ultimo. La richiesta all'artigiano (R-46) non ha tabella: si ricava dalle decisioni `integrazione*`. I valori ammessi di ogni campo stanno nel `domain.py` del modulo della tabella; la scheda per canale è `SCHEDE_CANALE` in `contenuti/domain.py` (valori in spec R-21).

**Migrazioni**, una catena Alembic, ognuna con lo schema per esteso: 001–006 i moduli · 007 coda Procrastinate 3.10.0 · 008 riallineamento · 009 `limite_login` · 010 `foto.pubblicata_su` · 011 `notifica` · 012 `chiamata_ai` · 013 storico dell'AI · 014 `pubblicazione.chiamata_il`.

**Stati** (`campagne/domain.py`, `contenuti/domain.py`):
- campagna: bozza → inviata → in_generazione → in_revisione → attiva → conclusa · inviata / in_generazione → generazione_fallita → inviata · in_revisione → respinta · prima dell'approvazione → scaduta · attiva ⇄ sospesa · attiva / sospesa → annullata. `piano_da_rivedere` resta solo per le righe vecchie.
- post: da_approvare → approvato → pubblicato / fallito / annullato · fallito → approvato · da_approvare → scaduto / scartato. `da_rivedere` è un indicatore, non uno stato.
- Interventi ammessi per stato: `INTERVENTI_AMMESSI` in `contenuti/domain.py`, unica fonte, letta anche da Vedi campagna tramite `interventi_ammessi()`.

## 3. API (prefisso `/api`)
| Modulo | Rotte | Chi |
|---|---|---|
| `main.py` | `GET /health` · `GET /consorzio` | senza sessione |
| accesso | `POST /auth/login` · `POST /auth/logout` · `GET /auth/me` | tutti |
| artigiani | `GET /canali` · `GET`, `PUT /profilo` | artigiano |
| artigiani | `POST /artigiani` (password provvisoria una volta, `no-store`) · `GET /artigiani/{id}` | operatore |
| campagne | `GET`, `POST /campagne` · `GET`, `PATCH /campagne/{id}` · gruppi e foto in bozza (`POST`, `PUT`, `DELETE`) · `POST /campagne/{id}/invia` | artigiano (l'operatore legge) |
| campagne | `POST /campagne/{id}/riprova` · `POST /campagne/{id}/richiesta` | operatore |
| campagne | `POST /campagne/{id}/richiesta/foto` · `POST /campagne/{id}/richiesta/invia` | artigiano |
| campagne | `GET /foto/{id}/file` · `GET /archivio-foto` | proprietario, operatore |
| campagne | `GET /foto/{id}/pubblica?canale=&firma=` (indirizzo firmato per Instagram, HMAC da `LOGIN_LIMITE_SEGRETO`) | senza sessione |
| contenuti | `GET /campagne/{id}/calendario` · `GET /calendario?dal=` | proprietario, operatore |
| contenuti | `GET /storico-ai` · `/storico-ai/numeri` · `/storico-ai/{id}` · `POST /storico-ai/{id}/voto` | operatore |
| revisione | `GET /da-approvare` · `GET /artigiani` · `GET /campagne/{id}/post` · `POST /campagne/{id}/approva` · `/respingi` · `/sospendi` · `/riattiva` · `/annulla` | operatore |
| revisione | `POST /post/{id}/modifica` · `/rigenera` · `/rigenera-immagine` · `GET /post/{id}/foto-possibili` · `POST /post/{id}/cambia-foto` · `/sposta` · `/annulla` · `/riprogramma` | operatore |
| congelato | `/archivio` e `/archivio/*` · `POST /campagne/{id}/nota` · `/togli-canale` · `POST /post/{id}/controllato` | — |

Errori: 401 non autenticato, 403 ruolo, 404 risorsa di un altro o inesistente, 409 stato (le regole R-xx), 422 dati. Una richiesta oltre 12 MiB riceve 413; il login oltre il limite dei tentativi 429 con `Retry-After`.

## 4. Job
| Job | Quando | Cosa fa |
|---|---|---|
| `genera_campagna` | da /invia e /riprova; 3 esecuzioni | a tappe, ognuna nella sua transazione e saltata se fatta (R-24): analisi, piano, immagini AI, testi con il validatore, `in_revisione` e notifica; errori secondo R-35 |
| `tick_pubblicazione` (`worker.py`) | ogni minuto, uno alla volta | `revisione.scadenze()` (R-06, R-35), poi `pubblicazione.pubblica_dovuti()`: tentativo registrato prima della chiamata, al massimo una pubblicazione per post (ADR-121), campagne concluse (R-34) |
| `rigenera_post` · `rigenera_immagine` | da revisione; 3 esecuzioni | nuovo testo o nuova immagine; non fanno nulla fuori da `in_revisione`; spengono l'intervento in corso (R-31, R-49) |
| `invia_notifica` | congelato | email verso il catcher locale |

I nomi dei job stanno in `core/coda.py`; un job di un altro modulo si accoda con `accoda(nome, …)`, senza importarlo.

## 5. Adattatori
In `adapters/<nome>/`, ognuno con interfaccia, finto e reale. **ai**: `analizza_gruppo()`, `pianifica_campagna()`, `genera_post()`, `genera_immagine()`; ogni errore esce come `ErroreAI` con il tipo di R-35; dopo ogni chiamata `ultimo_uso` va in `chiamata_ai`; prompt versionati in `adapters/ai/prompts/`. **social**: `pubblica()`; Meta con Facebook `/{page-id}/photos` e Instagram contenitore + `media_publish`, errori tradotti in temporaneo o definitivo; una sola pagina di prova da `.env`. **email**: catcher locale (congelato). **archivio**: file sotto `ARCHIVIO_FOTO_DIR`.

## 6. Contratti tra moduli
Un modulo legge i dati di un altro solo con le funzioni del `service.py` di quel modulo (niente SQL sulle sue tabelle, niente copie delle sue costanti, lo stato si passa per nome). Ordine: accesso → notifiche → artigiani → campagne → contenuti → revisione → pubblicazione; un modulo usa solo quelli che lo precedono (`tests/test_confini.py`). Le funzioni pubbliche principali:

| Modulo | Funzioni |
|---|---|
| accesso | `utente_corrente`, `richiede_ruolo` (l'admin passa dove passa l'operatore), `crea_utente`, `cambia_password`, `crea_artigiano`, `utente`, `operatori`, `artigiani` |
| notifiche | `crea` |
| artigiani | `profilo_di`, `profilo`, `canali_collegati`, `post_a_settimana` |
| campagne | `campagna`, `campagna_bloccata`, `foto_della_campagna`, `campagne_in_stato`, `campagne_di`, `gruppi_della_campagna`, `cambia_stato`, `registra_decisione`, `ultima_nota`, `togli_canale`, `aggiorna_foto`, `aggiungi_foto`, `post_chiesti` (la formula di R-05, solo qui), `campagna_per_calendario`, `decisioni_canali_tolti`, `foto_di_archivio`, `segna_pubblicata`, `foto_per_id`, `sistema_foto`, `foto_sistemata`, `url_foto_pubblica`, `richiesta_di` |
| contenuti | `post_della_campagna`, `ha_blocchi`, `approva_post`, `piano_corrente`, `uscite_della_campagna`, `ultimo_errore`, `costo_ai_campagna`, `scarta_post_*`, `scadi_post`, `annulla_post`, `accendi_intervento`, `puo_rigenerare`, `ferma_generazione`, `interventi_ammessi`, `modifica_post`, `riprogramma_post`, `sposta_post`, `annulla_un_post`, `foto_possibili`, `cambia_foto`, `post_dovuti`, `post_per_id`, `segna_esito`, `tutti_chiusi` |
| revisione | `scadenze` (per il tick). È revisione a scrivere le righe `approvazione`, anche quelle delle versioni nate dopo l'approvazione: contenuti non conosce quella tabella |
| pubblicazione | `pubblica_dovuti` e le sue fasi: `prepara_tentativi`, `avvia_chiamata`, `chiama_social`, `registra_esito`, `chiudi_campagne` |

Una firma si cambia nel task che ne ha bisogno, dicendolo nella PR.

## 7. Base comune
| Dove | Cosa |
|---|---|
| `core/config.py` | `leggi_impostazioni()`; mai `os.environ` |
| `core/db.py` | `Base`, `get_db` nei router, `with transazione() as db:` nei job; commit alla fine, rollback sull'errore: service e router non chiamano `commit` |
| `core/errori.py` | `NonAutenticato` 401, `NonPermesso` 403, `NonTrovato` 404, `StatoNonValido` 409, `DatiNonValidi` 422; niente `HTTPException` nei service |
| `core/orologio.py` | `adesso()` in UTC passata ai service, `ROMA`; `OROLOGIO_GIORNI_AVANTI` solo per le prove a mano |
| `core/security.py` | scrypt per le password, token di sessione e il suo hash |
| `core/limite_richiesta.py` · `limite_login.py` · `eventi_sicurezza.py` | 413, 429, `X-Request-ID` ed eventi senza dati personali; già montati in `main.py` |
| `core/transizioni.py` | `verifica_transizione()` con il dizionario del `domain.py` |
| `core/coda.py` · `worker.py` | `accoda()` (si chiama per ultima: scrive fuori dalla transazione), nomi dei job; i job in `jobs.py` di ogni modulo, `def` normali |
| `tabelle.py` · `main.py` | i `models.py` per Alembic; i router montati sotto `/api` |
| `tests/conftest.py` | fixture `db` (su `adflow_test`, annullata a fine test), `client`, `coda` (in memoria), `utente_di_prova(ruolo)`; fabbriche in `tests/moduli/<modulo>/fabbrica.py`, con `flush` e mai `commit` |

A ogni `pytest` il database `adflow_test` si svuota e torna all'ultima migrazione.
