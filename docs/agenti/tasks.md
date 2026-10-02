# Tasks

Sei corsie. La **corsia 0** è di tutto il team: si lavora e si approva insieme. Le **corsie 1–5** sono di una persona ciascuna e procedono in parallelo. Prendi i task della tua corsia in ordine, quando ciò che sta in "Dipende da" è su `main`; nella PR cambia ☐ in ☑. Solo lo sprint corrente è diviso in task.

| Corsia | Chi | Di sua proprietà |
|---|---|---|
| 0 · Comune | tutto il team | `core/`, `main.py`, `worker.py`, `cli.py`, `tabelle.py`, `alembic/`; di ogni modulo `models.py`, `domain.py` e le funzioni di plan §6 scritte in T1-04; `tests/percorsi/`, `tests/test_confini.py`, `tests/moduli/*/fabbrica.py` |
| 1 · Accesso e artigiani | Gianluca | `moduli/accesso/`, `moduli/notifiche/`, `moduli/artigiani/`, `adapters/email/` |
| 2 · Campagne | Silvia | `moduli/campagne/`, `adapters/archivio/` |
| 3 · Contenuti | Giovanni | `moduli/contenuti/`, `adapters/ai/` |
| 4 · Revisione e pubblicazione | Nilton | `moduli/revisione/`, `moduli/pubblicazione/`, `adapters/social/` |
| 5 · Frontend | Angelo | `frontend/` |

Nei loro moduli le corsie 1–4 possiedono `router.py`, `schemas.py`, `jobs.py`, le altre funzioni di `service.py` e i test (`tests/moduli/<modulo>/`, `tests/adapters/<nome>/`).

- Corsia 0: la PR si unisce solo con l'approvazione di tutti.
- Corsie 1–5: la PR tocca solo ciò che è della sua corsia; revisione di gruppo; unisce l'admin.
- Ciò che è della corsia 0 si cambia solo con un nuovo task della corsia 0: apri una domanda, non una PR.

## Sprint 1 · Scheletro che cammina (modello definitivo, AI e social finti, profilo dal seed)

**Ordine.** T1-01 → T1-02 e T1-03 → T1-04, T1-05, T1-06 → corsie 1–5 in parallelo → T1-07. Le corsie 1–5 partono quando T1-01…T1-06 sono su `main`. Nessun task delle corsie 1–4 dipende da un'altra corsia personale.

### Corsia 0 · Comune (tutto il team)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-01 | **Struttura**: `backend/` da zero (`requirements.txt`, `.env.example`, `.gitignore`); albero di constitution §2 con i sette moduli (ognuno con `router.py` vuoto montato in `main.py`, `jobs.py` vuoto registrato in `worker.py`, `service.py` vuoto); `core/` (config, db, errori, orologio, `verifica_transizione()`); `GET /api/health`; `tabelle.py`; Alembic configurato; fixture pytest su `adflow_test`; `test_confini.py`; README con installazione e avvio | constitution §2; plan §1 | — | app avviata; health e test dei confini verdi | ☑ |
| T1-02 | **Contratti**: le firme di plan §6 nei `service.py` (tipi, docstring, `NotImplementedError`); i nomi dei job di plan §4 in `core/coda.py` | plan §4, §6 | T1-01 | ogni firma approvata da chi la scrive e da chi la usa | ☑ |
| T1-03 | **Tabelle**: `models.py` e migrazioni 001–006 delle tabelle con sprint 1 in plan §2; fabbriche di base | plan §2, §6 | T1-01 | upgrade e downgrade su DB vuoto; secondo `ok` di pubblicazione sullo stesso post rifiutato | ☑ |
| T1-04 | **Stati e letture comuni**: `domain.py` di artigiani, campagne e contenuti (valori ammessi, stati, transizioni); le funzioni di plan §6 segnate T1-04; fabbriche complete | plan §2, §6 | T1-02, T1-03 | test su ogni transizione ammessa e vietata di campagna e post; un test per funzione | ☑ |
| T1-05 | **Coda e worker**: `accoda(nome, …)` in `core/coda.py`; worker avviabile; `tick_pubblicazione` ogni minuto, uno alla volta, che chiama `pubblicazione.pubblica_dovuti()` | plan §1, §4, §6 | T1-02 | job di prova accodato per nome ed eseguito in un test; tick provato con una funzione finta | ☐ |
| T1-06 | **Seed e utente di prova**: scrypt e token in `core/security.py`; in `cli.py` il seed (artigiano con profilo, operatore, admin) e il comando crea-utente, che chiama `accesso.service.crea_utente()`; fixture `utente_di_prova(ruolo)` che sostituisce `utente_corrente` | plan §2, §6; constitution §3 | T1-03 | seed funzionante; un test di API passa con l'utente di prova | ☑ |
| T1-07 | **Chiusura**: test API del percorso completo con il codice di tutte le corsie; frontend sulle API vere; percorso a mano | converge §3 | tutti i task dello sprint | tutti i CA con S = 1 verdi, compresa la Riprova di CA-19 | ☐ |

### Corsia 1 · Accesso e artigiani (Gianluca)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-11 | Login: `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`; cookie `adflow_sessione` httpOnly; nel database solo l'hash del token; scadenza della sessione | plan §2, §3; constitution §3 | T1-06 | CA-01, CA-02 | ☐ |
| T1-12 | Permessi: `utente_corrente` e `richiede_ruolo()` veri (401 senza sessione, 403 per ruolo) | plan §6; constitution §3 | T1-11 | CA-03; i test delle altre corsie restano verdi | ☐ |
| T1-13 | `crea_utente()`: email unica, ruolo ammesso, password con scrypt | plan §2, §6; constitution §3 | T1-06 | utente creato da riga di comando | ☐ |

### Corsia 2 · Campagne (Silvia)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-21 | Adattatore archivio: salva, legge, elimina sotto `ARCHIVIO_FOTO_DIR`; nome del file generato dal server; implementazione finta | plan §5; constitution §3 | T1-01 | test senza toccare l'archivio reale | ☐ |
| T1-22 | API bozza: `POST /campagne` (con `crea_immagini_ai`), `GET /campagne`, `GET /campagne/{id}`; vincoli su date, una sola bozza, periodi non sovrapposti; l'artigiano vede solo le sue | plan §2, §3, §6; spec R-08, R-12, R-19 | T1-04, T1-06 | CA-04, CA-09 (creazione), CA-10…12, CA-46 | ☐ |
| T1-23 | Foto e gruppi: caricamento con controllo di tipo reale, peso e dimensioni; descrizione di gruppo; eliminazione di foto e gruppo; file della foto; solo in bozza | plan §3, §5; spec R-13; constitution §3 | T1-21, T1-22 | CA-13 | ☐ |
| T1-24 | Invio e Riprova: controlli all'invio, copia di canali, frequenza e obiettivo dal profilo, `profilo_snapshot`, stato `inviata`, `accoda("genera_campagna")`; Riprova da `generazione_fallita` | plan §3, §6; spec §2.1, R-08, R-11, R-13 | T1-23, T1-05 | CA-09 (invio), CA-14, CA-15; Riprova → `inviata` e job accodato | ☐ |

### Corsia 3 · Contenuti (Giovanni)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-31 | Adattatore AI: interfaccia `analizza_immagine()`, `genera_post()`; provider finto con risposte prevedibili ed errori a comando; LiteLLM non usato nei test | plan §5 | T1-01 | nessuna chiamata di rete nei test | ☐ |
| T1-32 | Calcolo slot: funzione pura da periodo, frequenza, canali e foto a date, ore e canali | spec R-05, R-08; plan §2 (frequenza) | T1-01 | CA-17 (calcolo) + casi limite | ☐ |
| T1-33 | Validatore a regole: lunghezza, hashtag, parole vietate, "cose da non dire", niente prezzi o premi | spec R-09 | T1-01 | un test per regola | ☐ |
| T1-34 | Job `genera_campagna`: usa lo snapshot; analisi foto, slot, testo per slot, validatore con riscritture, `da_rivedere`; errore tecnico e `generazione_fallita`; alla fine campagna `in_revisione` | plan §4, §5, §6; spec §2.2, R-05, R-09, R-11 | T1-31, T1-32, T1-33, T1-04, T1-05 | CA-17, CA-18, CA-19 (fino a `generazione_fallita`), CA-20 | ☐ |

### Corsia 4 · Revisione e pubblicazione (Nilton)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-41 | Adattatore social simulato: `pubblica()` con esito ok, errore temporaneo ed errore definitivo a comando | plan §5 | T1-01 | nessuna chiamata di rete nei test | ☐ |
| T1-42 | Vedi campagna e Approva: `GET /campagne/{id}/post` con versione corrente e storico; `POST /campagne/{id}/approva` in blocco, con righe di approvazione e decisione | plan §3, §6; spec §2.3, R-14 | T1-04, T1-06 | CA-21, CA-22 | ☐ |
| T1-43 | Pubblicazione: `pubblica_dovuti()`; tentativo registrato prima della chiamata, un solo `ok` per post, nuovi tentativi, post `fallito`, campagna `conclusa` | plan §4, §5, §6; constitution §1; spec §2.4 | T1-41, T1-04, T1-05 | CA-36…39 | ☐ |

### Corsia 5 · Frontend (Angelo)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-51 | Base: `frontend/` da zero (Vite + React + TypeScript); Mantine, `api/` con un file per modulo, `auth.tsx`, pagina di login, rotte per ruolo, proxy `/api` | plan §3; constitution §2, §4 | T1-01 | login sui dati di esempio; build e lint puliti; README con installazione e avvio | ☐ |
| T1-52 | Artigiano minimo, pagina Campagna: bozza, foto a gruppi con descrizione, spunta immagini AI, invio, stato della campagna | spec §2.1, §4, R-08, R-13; plan §3 | T1-51 | pagina completa sui dati di esempio; build e lint puliti | ☐ |
| T1-53 | Operatore minimo: campagne da approvare, Vedi campagna in elenco, Approva, Riprova | spec §2.3, §4; plan §3 | T1-51 | pagine complete sui dati di esempio; build e lint puliti | ☐ |

Finché un endpoint non è su `main`, la pagina usa dati di esempio con la forma di plan §3 (`src/api/esempi/`). Il passaggio alle API vere (login di T1-11, invio di T1-24, approvazione di T1-42) si chiude in T1-07.

## Sprint successivi (si dividono in task quando si arriva)
Le corsie restano le stesse: ogni novità va alla corsia del suo modulo; tabelle, stati e funzioni condivise alla corsia 0.
- **2a · Pagine Profilo e Campagna**: profilo, PATCH bozza, pagina Profilo (passi 1–9), pagina Campagna (Bentornato, passi 10–12). CA-05…08, CA-16.
- **2b · Revisione e motivi del No**: rimanda, respingi con motivo, notifiche ed email, scadenza, rigenera (2 modalità), sospendi / riattiva / annulla, visibilità artigiano. CA-23…32.
- **3 · Ritocco foto e pagine operatore**: `versione_foto`, ritocca / scegli foto, anagrafica, elenco e pagina artigiano, account social e sospensione, calendario, promemoria. CA-33…35, CA-40…43.
- **4 · Monitoraggio e demo**: metriche, dashboard, report, E2E, dati demo, prova con OpenAI. CA-44, CA-45.
- **Da pianificare · Immagini create dall'AI** (spec R-19): creazione delle immagini e invio senza foto. Nessun task finché non è chiusa l'analisi.
