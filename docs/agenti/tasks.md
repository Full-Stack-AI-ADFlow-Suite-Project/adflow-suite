# Tasks

Sei corsie. La **corsia 0** è di tutto il team: si lavora e si approva insieme. Le **corsie 1–5** sono di una persona ciascuna e procedono in parallelo. Prendi i task della tua corsia in ordine, quando ciò che sta in "Dipende da" è su `main`; nella PR cambia ☐ in ☑. Solo lo sprint corrente è diviso in task.

| Corsia | Chi | Di sua proprietà |
|---|---|---|
| 0 · Comune | tutto il team | `core/`, `main.py`, `worker.py`, `cli.py`, `tabelle.py`, `alembic/`; di ogni modulo `models.py`, `domain.py` e le funzioni di plan §6 scritte in T1-04 e T1-09; `tests/percorsi/`, `tests/test_confini.py`, `tests/moduli/*/fabbrica.py` |
| 1 · Accesso e artigiani | Gianluca | `moduli/accesso/`, `moduli/notifiche/`, `moduli/artigiani/`, `adapters/email/` |
| 2 · Campagne | Silvia | `moduli/campagne/`, `adapters/archivio/` |
| 3 · Contenuti | Giovanni | `moduli/contenuti/`, `adapters/ai/` |
| 4 · Revisione e pubblicazione | Nilton | `moduli/revisione/`, `moduli/pubblicazione/`, `adapters/social/` |
| 5 · Frontend | Angelo | `frontend/` |

Nei loro moduli le corsie 1–4 possiedono `router.py`, `schemas.py`, `jobs.py`, le altre funzioni di `service.py` e i test (`tests/moduli/<modulo>/`, `tests/adapters/<nome>/`).

- Corsia 0: la PR si unisce solo con l'approvazione di tutti.
- Corsie 1–5: la PR tocca solo ciò che è della sua corsia; revisione di gruppo; unisce l'admin.
- Ciò che è della corsia 0 si cambia solo con un nuovo task della corsia 0: apri una domanda, non una PR.

## Sprint 1 · Scheletro che cammina (modello definitivo, AI e social finti, profilo e account social dal seed)

**Ordine.** T1-01 → T1-02 e T1-03 → T1-04, T1-05, T1-06 → T1-08 → T1-09 → corsie 1–5 in parallelo → T1-07. Le corsie 1–5 partono quando T1-01…T1-06, T1-08 e T1-09 sono su `main`. Nessun task delle corsie 1–4 dipende da un'altra corsia personale, tranne T1-35, che usa l'adattatore archivio di T1-21.

**Riallineamento.** Il codice di T1-01…T1-06 su `main` segue il modello precedente (una foto per versione di post, gruppo come etichetta, canali copiati dal profilo, `approva_post()` tutto o niente, etichetta "rimandata", nessuna modifica a mano). T1-08 e T1-09 lo portano al modello di plan §2 e §6, comprese le regole di revisione del 07/10 (spec R-29…R-36): fino ad allora, dove codice e documenti non tornano, valgono i documenti.

### Corsia 0 · Comune (tutto il team)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-01 | **Struttura**: `backend/` da zero (`requirements.txt`, `.env.example`, `.gitignore`); albero di constitution §2 con i sette moduli (ognuno con `router.py` vuoto montato in `main.py`, `jobs.py` vuoto registrato in `worker.py`, `service.py` vuoto); `core/` (config, db, errori, orologio, `verifica_transizione()`); `GET /api/health`; `tabelle.py`; Alembic configurato; fixture pytest su `adflow_test`; `test_confini.py`; README con installazione e avvio | constitution §2; plan §1 | — | app avviata; health e test dei confini verdi | ☑ |
| T1-02 | **Contratti**: le firme di plan §6 nei `service.py` (tipi, docstring, `NotImplementedError`); i nomi dei job di plan §4 in `core/coda.py` | plan §4, §6 | T1-01 | ogni firma approvata da chi la scrive e da chi la usa | ☑ |
| T1-03 | **Tabelle**: `models.py` e migrazioni 001–006 delle tabelle con sprint 1 in plan §2; fabbriche di base | plan §2, §6 | T1-01 | upgrade e downgrade su DB vuoto; secondo `ok` di pubblicazione sullo stesso post rifiutato | ☑ |
| T1-04 | **Stati e letture comuni**: `domain.py` di artigiani, campagne e contenuti (valori ammessi, stati, transizioni); le funzioni di plan §6 segnate T1-04; fabbriche complete | plan §2, §6 | T1-02, T1-03 | test su ogni transizione ammessa e vietata di campagna e post; un test per funzione | ☑ |
| T1-05 | **Coda e worker**: `accoda(nome, …)` in `core/coda.py`; worker avviabile; `tick_pubblicazione` ogni minuto, uno alla volta, che chiama `pubblicazione.pubblica_dovuti()` | plan §1, §4, §6 | T1-02 | job di prova accodato per nome ed eseguito in un test; tick provato con una funzione finta | ☑ |
| T1-06 | **Seed e utente di prova**: scrypt e token in `core/security.py`; in `cli.py` il seed (artigiano con profilo, operatore, admin) e il comando crea-utente, che chiama `accesso.service.crea_utente()`; fixture `utente_di_prova(ruolo)` che sostituisce `utente_corrente` | plan §2, §6; constitution §3 | T1-03 | seed funzionante; un test di API passa con l'utente di prova | ☑ |
| T1-07 | **Chiusura**: test API del percorso completo con il codice di tutte le corsie; frontend sulle API vere; percorso a mano | converge §3 | tutti i task dello sprint | tutti i CA con S = 1 verdi, compresa la Riprova di CA-19 | ☐ |
| T1-08 | **Riallineamento delle tabelle**: `models.py` e migrazione 008 per portare le tabelle dello sprint 1 alla forma di plan §2. Nuove: `account_social`, `gruppo_foto` (con `profilo_id` e campagna facoltativa), `piano`, `uscita` (gruppo facoltativo), `versione_post_foto`, `errore_generazione`. Cambiate: `utente` (`deve_cambiare_password`), `foto` (`gruppo_id` verso `gruppo_foto`, facoltativo come `campagna_id`; `da_usare`; via `descrizione`), `campagna` (`canali_tolti`, `chiusa_il`; via `crea_immagini_ai` e `rimandata`), `decisione_campagna` (`canale`, `post_id`), `post` (`uscita_id`, `formato`, `riempitivo`, `controllato_da`, `controllato_il`, `intervento_in_corso`, `intervento_dal`), `versione_post` (`autore_id`; via `foto_id`), `profilo_bottega` (`logo`). Fabbriche di base | plan §2 | T1-03 | upgrade e downgrade su DB vuoto; `alembic check` senza differenze; i test di T1-03 aggiornati e verdi | ☑ |
| T1-09 | **Riallineamento di stati e contratti**: nei `domain.py` lo stato `piano_da_rivedere` e la transizione `inviata` → `generazione_fallita`, lo stato `annullato` del post, gli esiti delle decisioni (`nota` al posto di `rimandata`), le origini del gruppo e della foto, i formati del post, i tipi di riempitivo, di contenuto, di versione, di errore di generazione, i livelli del validatore, gli stati dell'account, `SCHEDE_CANALE` con i numeri di R-21; le funzioni di plan §6 segnate T1-09, comprese `approva_post()`, `ha_blocchi()` e `tutti_chiusi()` con `adesso`; `campagna.chiusa_il` scritta da `cambia_stato()`; l'admin ammesso da `richiede_ruolo()`; in `core/config.py` durata della sessione e contatto del consorzio, `GET /consorzio` in `main.py`; in `cli.py` il comando `cambia-password`; fabbriche complete; nel seed gli account social collegati dell'artigiano (Facebook e Instagram) | plan §1, §2, §3, §6; spec R-14, R-21, R-22, R-29, R-34 | T1-04, T1-06, T1-08 | test su ogni transizione nuova, ammessa e vietata; un test per funzione nuova o cambiata; CA-39 (funzione), CA-61, CA-63; seed con i due account | ☑ |

### Corsia 1 · Accesso e artigiani (Gianluca)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-11 | Login: `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`; cookie `adflow_sessione` httpOnly; nel database solo l'hash del token; durata della sessione per ruolo, dalla configurazione | plan §1, §2, §3; constitution §3; spec R-29 | T1-06, T1-09 | CA-01, CA-02 | ☑ |
| T1-12 | Permessi: `utente_corrente` e `richiede_ruolo()` veri (401 senza sessione o con la sessione scaduta, 403 per ruolo, l'admin dove passa l'operatore); ogni richiesta sposta in avanti la scadenza della sessione | plan §6; constitution §3; spec R-29 | T1-11 | CA-03, CA-62; CA-61 e i test delle altre corsie restano verdi | ☑ |
| T1-13 | `crea_utente()` e `cambia_password()`: email unica, ruolo ammesso, password con scrypt | plan §2, §6; constitution §3 | T1-06, T1-09 | utente creato e password cambiata da riga di comando | ☑ |
| T1-14 | Canali collegati: `GET /canali` con lo stato del collegamento per ogni canale dell'MVP | plan §3, §6; spec R-22 | T1-09 | l'artigiano del seed vede Facebook e Instagram collegati; un account scaduto o scollegato risulta non collegato | ☑ |

### Corsia 2 · Campagne (Silvia)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-21 | Adattatore archivio: salva, legge, elimina sotto `ARCHIVIO_FOTO_DIR`; nome del file generato dal server; implementazione finta | plan §5; constitution §3 | T1-01 | test senza toccare l'archivio reale | ☑ |
| T1-22 | API bozza: `POST /campagne` con i canali, `GET /campagne` con lo stato ripetibile e, per l'operatore, bottega e città di ogni campagna, `GET /campagne/{id}` con gruppi, foto, post chiesti per canale e avvisi; vincoli su date e durata, una sola bozza, periodi non sovrapposti, canali solo se collegati; l'artigiano vede solo le sue | plan §2, §3, §6; spec R-05, R-08, R-12, R-22, R-25 | T1-09 | CA-04, CA-09 (creazione), CA-10…12, CA-48 (creazione), CA-54; elenco con due stati insieme | ☑ |
| T1-23 | Gruppi e foto: gruppi `caricate` e `create_ai` con descrizione, data e numero di immagini; caricamento con controllo di tipo reale, peso e dimensioni, al massimo 20 foto per gruppo; stella; eliminazione di foto e gruppo; file della foto; solo in bozza | plan §3, §5; spec R-13, R-19; constitution §3 | T1-21, T1-22 | CA-13, CA-46, CA-47 | ☑ |
| T1-24 | Invio e Riprova: controlli all'invio (minimi, descrizioni dei gruppi, canali collegati), copia di frequenza e obiettivo dal profilo, `profilo_snapshot`, stato `inviata`, `accoda("genera_campagna")`; Riprova da `generazione_fallita` | plan §3, §6; spec §2.1, R-08, R-11, R-13, R-22 | T1-23, T1-05 | CA-09 (invio), CA-14, CA-15, CA-48 (invio); Riprova → `inviata` e job accodato | ☐ |

### Corsia 3 · Contenuti (Giovanni)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-31 | Adattatore AI: interfaccia `analizza_gruppo()`, `pianifica_campagna()`, `genera_post()`; `ErroreAI` con i cinque tipi di R-35; provider finto con risposte prevedibili (lo stesso piano a parità di dati, con le cartoline per i post che le foto non coprono; carosello ed errori di ogni tipo a comando); LiteLLM non usato nei test | plan §5; spec §2.2, R-28, R-35 | T1-09 | nessuna chiamata di rete nei test; il piano del provider finto passa il controllo di T1-32; un test per tipo di errore | ☐ |
| T1-32 | Limiti e controllo del piano: funzioni pure per i post chiesti e le foto disponibili per canale; controllo di un piano (post per canale uguali a quelli chiesti, riempitivi solo dove le foto non bastano, nessun carosello su un canale con riempitivi, foto ripetute sul canale, date nel periodo e non nel passato, foto con la stella, massimo di foto per post); piano debole | spec R-05, R-08, R-20, R-21, R-23, R-28 | T1-09 | CA-17 (limiti) + casi limite; un test per ogni regola del controllo | ☐ |
| T1-33 | Validatore a regole, a due livelli: blocchi (parole vietate, "cose da non dire", prezzi o premi, testo vuoto, limiti della piattaforma) e avvisi (limiti editoriali della scheda del canale); restituisce `[{livello, regola, messaggio}]` | spec R-09, R-21; plan §2 (scheda per canale) | T1-09 | un test per regola e per canale, con il suo livello | ☐ |
| T1-34 | Job `genera_campagna` a tappe: usa lo snapshot; analisi dei gruppi, piano con controllo e riscritture, uscite e post con i riempitivi, piano debole e `piano_da_rivedere`, cartoline, testo per post, validatore con riscritture, `da_rivedere` solo con un blocco; ripresa dalle tappe già salvate; errori tecnici secondo il tipo, salvati in `errore_generazione`, e `generazione_fallita`; alla fine campagna `in_revisione` | plan §4, §5, §6; spec §2.2, R-05, R-09, R-11, R-20, R-23, R-24, R-28, R-35 | T1-31, T1-32, T1-33, T1-35, T1-05 | CA-17, CA-18, CA-19 (fino a `generazione_fallita`), CA-20, CA-49 (fino a `piano_da_rivedere`), CA-50, CA-51, CA-52 (post con più foto), CA-57 (fino ai post `da_approvare`), CA-58, CA-59 | ☐ |
| T1-35 | Cartoline: funzione che compone l'immagine di un post `cartolina` (nome della bottega dallo snapshot e tema dell'uscita), la salva con l'adattatore archivio e crea la foto con `campagne.service.aggiungi_foto()`; la libreria per le immagini si dichiara nella PR | spec R-28; plan §4, §5, §6; constitution §3 | T1-09, T1-21 | un test sulla misura e sul formato del file; un test sulla foto creata, senza gruppo e con origine `cartolina`; nessun file fuori dall'archivio di prova | ☐ |

### Corsia 4 · Revisione e pubblicazione (Nilton)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-41 | Adattatore social simulato: `pubblica()` con una o più foto, con esito ok, errore temporaneo ed errore definitivo a comando | plan §5 | T1-01 | nessuna chiamata di rete nei test | ☑ |
| T1-42 | Vedi campagna, Approva e Prosegui: `GET /campagne/{id}/post` in ogni stato dopo l'invio, con il piano, le uscite, i post dei canali con tipo di riempitivo, versione corrente, autore, blocchi e avvisi, foto e storico, le foto non usate, l'ultimo errore della generazione; `POST /campagne/{id}/approva` in blocco, con righe di approvazione e decisione; `POST /campagne/{id}/prosegui` | plan §3, §6; spec §2.3, R-14, R-20, R-35 | T1-09, T1-05 | CA-21, CA-22, CA-49 (Prosegui), CA-60 | ☑ |
| T1-43 | Pubblicazione: `pubblica_dovuti()`; tentativo registrato prima della chiamata, tutte le foto del post (per una cartolina la sua immagine), un solo `ok` per post, nuovi tentativi, post `fallito`, campagna `conclusa` secondo `tutti_chiusi()` | plan §4, §5, §6; constitution §1; spec §2.4, R-34 | T1-41, T1-09, T1-05 | CA-36…39, CA-52 (pubblicazione), CA-57 (pubblicazione) | ☑ |

### Corsia 5 · Frontend (Angelo)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-51 | Base: `frontend/` da zero (Vite + React + TypeScript); Mantine, `api/` con un file per modulo, `auth.tsx`, pagina di login con il contatto del consorzio, rotte per ruolo (artigiano → Campagna; operatore e admin → campagne da approvare), ritorno al login a ogni 401 e poi alla pagina di partenza, proxy `/api` | plan §3; constitution §2, §4; spec R-29 | T1-01 | login sui dati di esempio; build e lint puliti; README con installazione e avvio | ☐ |
| T1-52 | Artigiano minimo, pagina Campagna: bozza con i canali collegati, gruppi di foto con descrizione, data e stella, avvisi letti dal dettaglio della campagna, invio, stato della campagna | spec §2.1, §4, R-08, R-13, R-19, R-22, R-25; plan §3 | T1-51 | pagina completa sui dati di esempio; build e lint puliti | ☐ |
| T1-53 | Operatore minimo: pagina Campagne da approvare (tutti gli artigiani, con `GET /campagne` e lo stato ripetuto), Vedi campagna in ogni stato dopo l'invio: decisione e piano in cima, elenco per uscite con i post dei canali affiancati, etichetta dei riempitivi, blocchi e avvisi, scheda Foto e profilo, errore accanto a Riprova; Approva, Prosegui, Riprova | spec §2.3, §4, R-14, R-35; plan §3 | T1-51 | pagine complete sui dati di esempio; build e lint puliti | ☐ |

Finché un endpoint non è su `main`, la pagina usa dati di esempio con la forma di plan §3 (`src/api/esempi/`). Il passaggio alle API vere (login di T1-11, canali di T1-14, invio di T1-24, approvazione di T1-42) si chiude in T1-07. La pagina statica di Vedi campagna è approvata e segue il modello a uscite: per T1-53 è il riferimento visivo, da dare nel brief; delle sue azioni lo sprint 1 costruisce solo Approva, Prosegui e Riprova.

## Sprint successivi (si dividono in task quando si arriva)
Le corsie restano le stesse: ogni novità va alla corsia del suo modulo; tabelle, stati e funzioni condivise alla corsia 0.
- **2a · Pagine Profilo e Campagna**: profilo, PATCH bozza, pagina Profilo (passi 1–9, con archivio della bottega e logo), pagina Campagna (Bentornato, passi 10–12), foto d'archivio nel piano (R-27) e logo nelle cartoline. CA-05…08, CA-16.
- **2b · Revisione**: modifica a mano e spunta "va bene", rigenera (2 modalità) con l'intervento in corso, nota interna, respingi con motivo (anche da `piano_da_rivedere`), togli il canale, scadenza morbida e campagne ferme, sospendi / riattiva con gli arretrati / annulla (nel modulo revisione), riprogramma un post fallito, lettura delle campagne da approvare con conteggi ed "entro quando", notifiche ed email (all'artigiano e agli operatori), visibilità artigiano (viste di stato nella pagina Campagna, scelta tra più campagne, campagne passate). CA-23…32, CA-53, CA-55, CA-64…70.
- **3 · Ritocco foto e pagine operatore**: `versione_foto`, ritocco delle foto del piano, ritocca / scegli foto, cambia foto e sposta, ritaglio unico per anteprima e pubblicazione, anagrafica, nuovo artigiano con la password provvisoria e il cambio obbligato, pagine dell'operatore (ingresso con "Da sistemare", elenco artigiani, nuovo artigiano, pagina artigiano, campagne chiuse), collegamento degli account social e sospensione, calendario (in Vedi campagna e, con il piano approvato, nella pagina Campagna dell'artigiano, da `GET /campagne/{id}/calendario`), promemoria. CA-33…35, CA-40…43, CA-56, CA-71…74.
- **4 · Monitoraggio e demo**: metriche con il filtro per periodo (pagina dell'operatore; per l'artigiano nella pagina Campagna), report settimanale agli operatori, riepilogo di fine campagna all'artigiano, E2E, dati demo, prova con OpenAI. CA-44, CA-45, CA-75.
- **Da pianificare · Immagini create dall'AI** (spec R-19): per i gruppi `create_ai`, ① creazione delle immagini dentro la generazione, dopo il piano e solo per quelle che servono; ② ritocco e rigenerazione con un prompt dell'operatore, dopo il ritocco foto dello sprint 3. Nessun task finché non è chiusa l'analisi.
- **Presenza costante a tappe** (spec R-27, R-28): cartoline nello sprint 1 (T1-35); archivio della bottega, logo e foto d'archivio nel piano nella 2a; immagini AI come riempitivo insieme alle immagini create, quando avranno un task. Le tabelle sono già pronte da T1-08.

## Follow-up sicurezza accesso · issue #16–19

Richiesti da Gianluca per le issue #16–19. Modifiche comuni della corsia 0 e accesso
della corsia 1 raccolte nella PR #36 su `main` (sostituisce la #21 chiusa senza merge), dopo il merge della #30 che include
T1-12 e T1-13: revisione di tutto il team,
merge dell'admin. Non si introducono servizi nuovi. Le caselle descrivono la
preparazione per revisione, non la chiusura formale dopo il merge.

| Issue | Corsia | Task / fatto quando | Preparato |
|---|---|---|---|
| #16 | 0/1 | Limite IP/account 5/15 min configurabile su PostgreSQL, condiviso e testato tra processi, 429 con Retry-After | ☑ |
| #18 | 0 | Eventi JSON distinti senza PII, request ID generato, guasto logger testato, procedure operative documentate | ☑ |
| #19 | 1/0 | email-validator senza DNS, Unicode/.test/account storici verificati, dipendenza documentata | ☑ |
| #17 | 0 | Configurazione proxy/cookie documentata e testata localmente con TLS; evidenza nello staging reale da allegare | ☐ |
