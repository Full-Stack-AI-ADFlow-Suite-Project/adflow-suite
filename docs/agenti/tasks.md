# Tasks

Sei corsie. La **corsia 0** è di tutto il team: si lavora e si approva insieme. Le **corsie 1–5** sono di una persona ciascuna e procedono in parallelo. Prendi i task della tua corsia in ordine, quando ciò che sta in "Dipende da" è su `main`; nella PR cambia ☐ in ☑. Gli sprint 1, 2a, 2b e 3 sono divisi in task; lo sprint corrente è il primo che ha ancora un task da fare.

**Da dove riparto?** Dalla radice: `uv run python allinea.py <corsia>`. Allinea la tua copia a `main` e legge questa pagina per te: stampa i task pronti della tua corsia (quelli con le dipendenze già ☑), cosa leggere e il branch da aprire. Le caselle di questa pagina sono l'unica fonte dello stato: non tenere elenchi a parte.

| Corsia | Chi | Di sua proprietà |
|---|---|---|
| 0 · Comune | tutto il team | `core/`, `main.py`, `worker.py`, `cli.py`, `tabelle.py`, `alembic/`, `backend/requirements.txt`, `.github/`, `allinea.py`; di ogni modulo `models.py`, `domain.py` e le funzioni di plan §6 scritte in T1-04 e T1-09; `tests/percorsi/`, `tests/test_confini.py`, `tests/moduli/*/fabbrica.py` |
| 1 · Accesso e artigiani | Gianluca | `moduli/accesso/`, `moduli/notifiche/`, `moduli/artigiani/`, `adapters/email/` |
| 2 · Campagne | Silvia | `moduli/campagne/`, `adapters/archivio/` |
| 3 · Contenuti | Giovanni | `moduli/contenuti/`, `adapters/ai/` |
| 4 · Revisione e pubblicazione | Nilton | `moduli/revisione/`, `moduli/pubblicazione/`, `adapters/social/` |
| 5 · Frontend | Angelo | `frontend/` |

Nei loro moduli le corsie 1–4 possiedono `router.py`, `schemas.py`, `jobs.py`, le altre funzioni di `service.py` e i test (`tests/moduli/<modulo>/`, `tests/adapters/<nome>/`).

- Corsia 0: la PR si unisce solo con l'approvazione di tutti.
- Corsie 1–5: la PR tocca solo ciò che è della sua corsia; revisione di gruppo; unisce l'admin.
- Ciò che è della corsia 0 si cambia solo con un nuovo task della corsia 0: apri una domanda, non una PR.
- Una libreria nuova è della corsia 0: entra in `backend/requirements.txt` con una PR sua (nome, motivo, licenza), unita **prima** della PR del task che la usa.

**Come si evita di pestarsi i piedi** (dallo sprint 2a):

- **Apertura e chiusura.** Ogni sprint si apre con un task della corsia 0 (`-01`) che fissa tabelle, valori ammessi, firme di plan §6 con `NotImplementedError`, fabbriche e forma delle API. Le corsie partono quando l'apertura è su `main`. Ogni sprint si chiude con un task della corsia 0 (`-07`): percorso completo, frontend sulle API vere, percorso a mano (converge §4).
- **Tocca.** Ogni task dice quali file tocca. La logica nuova va nel file che il task nomina, spesso un file nuovo del modulo, non in coda a `service.py`: in `service.py` restano le funzioni di plan §6. Se ti serve un file che il task non nomina, fermati e chiedi.
- **Frontend.** Una cartella di pagina e un file di `api/` per task. Finché l'endpoint non è su `main` la pagina usa i dati di esempio, con la forma di plan §3; il passaggio alle API vere si fa nella chiusura.
- **Riserva.** Ogni task del frontend ha una riserva: se due giorni dopo che le sue dipendenze sono su `main` nessuno l'ha aperto, lo prende la riserva, e il proprietario della corsia rivede la PR.
- **Prestito.** Un task segnato "prestabile" vive in un file suo: può farlo la persona indicata, se il proprietario della corsia è carico. Gli altri task non si prestano senza una decisione del team.
- **Ciò che manca.** Una regola o una firma che non c'è diventa una issue e una PR della corsia 0, mai un pezzo della PR del task.

## Sprint 1 · Scheletro che cammina (modello definitivo, AI e social finti, profilo e account social dal seed)

**Ordine.** T1-01 → T1-02 e T1-03 → T1-04, T1-05, T1-06 → T1-08 → T1-09 → corsie 1–5 in parallelo → T1-07. Le corsie 1–5 partono quando T1-01…T1-06, T1-08 e T1-09 sono su `main`. Nessun task delle corsie 1–4 dipende da un'altra corsia personale, tranne T1-35, che usa l'adattatore archivio di T1-21.

**Riallineamento.** Fatto: T1-08 e T1-09 hanno portato tabelle, stati e contratti al modello di plan §2 e §6, comprese le regole di revisione del 07/10 (spec R-29…R-36). Dove codice e documenti non tornano valgono i documenti: non adattare il codice a memoria, apri una domanda.

### Corsia 0 · Comune (tutto il team)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-01 | **Struttura**: `backend/` da zero (`requirements.txt`, `.env.example`, `.gitignore`); albero di constitution §2 con i sette moduli (ognuno con `router.py` vuoto montato in `main.py`, `jobs.py` vuoto registrato in `worker.py`, `service.py` vuoto); `core/` (config, db, errori, orologio, `verifica_transizione()`); `GET /api/health`; `tabelle.py`; Alembic configurato; fixture pytest su `adflow_test`; `test_confini.py`; README con installazione e avvio | constitution §2; plan §1 | — | app avviata; health e test dei confini verdi | ☑ |
| T1-02 | **Contratti**: le firme di plan §6 nei `service.py` (tipi, docstring, `NotImplementedError`); i nomi dei job di plan §4 in `core/coda.py` | plan §4, §6 | T1-01 | ogni firma approvata da chi la scrive e da chi la usa | ☑ |
| T1-03 | **Tabelle**: `models.py` e migrazioni 001–006 delle tabelle con sprint 1 in plan §2; fabbriche di base | plan §2, §6 | T1-01 | upgrade e downgrade su DB vuoto; secondo `ok` di pubblicazione sullo stesso post rifiutato | ☑ |
| T1-04 | **Stati e letture comuni**: `domain.py` di artigiani, campagne e contenuti (valori ammessi, stati, transizioni); le funzioni di plan §6 segnate T1-04; fabbriche complete | plan §2, §6 | T1-02, T1-03 | test su ogni transizione ammessa e vietata di campagna e post; un test per funzione | ☑ |
| T1-05 | **Coda e worker**: `accoda(nome, …)` in `core/coda.py`; worker avviabile; `tick_pubblicazione` ogni minuto, uno alla volta, che chiama `pubblicazione.pubblica_dovuti()` | plan §1, §4, §6 | T1-02 | job di prova accodato per nome ed eseguito in un test; tick provato con una funzione finta | ☑ |
| T1-06 | **Seed e utente di prova**: scrypt e token in `core/security.py`; in `cli.py` il seed (artigiano con profilo, operatore, admin) e il comando crea-utente, che chiama `accesso.service.crea_utente()`; fixture `utente_di_prova(ruolo)` che sostituisce `utente_corrente` | plan §2, §6; constitution §3 | T1-03 | seed funzionante; un test di API passa con l'utente di prova | ☑ |
| T1-07 | **Chiusura**: test API del percorso completo con il codice di tutte le corsie; frontend sulle API vere; percorso a mano | converge §3 | tutti i task dello sprint | tutti i CA con S = 1 verdi, compresa la Riprova di CA-19 | ☑ |
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
| T1-24 | Invio e Riprova: controlli all'invio (minimi, descrizioni dei gruppi, canali collegati), copia di frequenza e obiettivo dal profilo, `profilo_snapshot`, stato `inviata`, `accoda("genera_campagna")`; Riprova da `generazione_fallita` | plan §3, §6; spec §2.1, R-08, R-11, R-13, R-22 | T1-23, T1-05 | CA-09 (invio), CA-14, CA-15, CA-48 (invio); Riprova → `inviata` e job accodato | ☑ |

### Corsia 3 · Contenuti (Giovanni)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-31 | Adattatore AI: interfaccia `analizza_gruppo()`, `pianifica_campagna()`, `genera_post()`; `ErroreAI` con i cinque tipi di R-35; provider finto con risposte prevedibili (lo stesso piano a parità di dati, con le cartoline per i post che le foto non coprono; carosello ed errori di ogni tipo a comando); LiteLLM non usato nei test | plan §5; spec §2.2, R-28, R-35 | T1-09 | nessuna chiamata di rete nei test; il piano del provider finto passa il controllo di T1-32; un test per tipo di errore | ☑ |
| T1-32 | Limiti e controllo del piano: funzioni pure per i post chiesti e le foto disponibili per canale; controllo di un piano (post per canale uguali a quelli chiesti, riempitivi solo dove le foto non bastano, nessun carosello su un canale con riempitivi, foto ripetute sul canale, date nel periodo e non nel passato, foto con la stella, massimo di foto per post); piano debole | spec R-05, R-08, R-20, R-21, R-23, R-28 | T1-09 | CA-17 (limiti) + casi limite; un test per ogni regola del controllo | ☑ |
| T1-33 | Validatore a regole, a due livelli: blocchi (parole vietate, "cose da non dire", prezzi o premi, testo vuoto, limiti della piattaforma) e avvisi (limiti editoriali della scheda del canale); restituisce `[{livello, regola, messaggio}]` | spec R-09, R-21; plan §2 (scheda per canale) | T1-09 | un test per regola e per canale, con il suo livello | ☑ |
| T1-34 | Job `genera_campagna` a tappe: usa lo snapshot; analisi dei gruppi, piano con controllo e riscritture, uscite e post con i riempitivi, piano debole e `piano_da_rivedere`, cartoline, testo per post, validatore con riscritture, `da_rivedere` solo con un blocco; ripresa dalle tappe già salvate; errori tecnici secondo il tipo, salvati in `errore_generazione`, e `generazione_fallita`; alla fine campagna `in_revisione` | plan §4, §5, §6; spec §2.2, R-05, R-09, R-11, R-20, R-23, R-24, R-28, R-35 | T1-31, T1-32, T1-33, T1-35, T1-05 | CA-17, CA-18, CA-19 (fino a `generazione_fallita`), CA-20, CA-49 (fino a `piano_da_rivedere`), CA-50, CA-51, CA-52 (post con più foto), CA-57 (fino ai post `da_approvare`), CA-58, CA-59 | ☑ |
| T1-35 | Cartoline: funzione che compone l'immagine di un post `cartolina` (nome della bottega dallo snapshot e tema dell'uscita), la salva con l'adattatore archivio e crea la foto con `campagne.service.aggiungi_foto()`; la libreria per le immagini entra in `requirements.txt` con una PR della corsia 0, prima della PR del task | spec R-28; plan §4, §5, §6; constitution §3 | T1-09, T1-21 | un test sulla misura e sul formato del file; un test sulla foto creata, senza gruppo e con origine `cartolina`; nessun file fuori dall'archivio di prova | ☑ |

### Corsia 4 · Revisione e pubblicazione (Nilton)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-41 | Adattatore social simulato: `pubblica()` con una o più foto, con esito ok, errore temporaneo ed errore definitivo a comando | plan §5 | T1-01 | nessuna chiamata di rete nei test | ☑ |
| T1-42 | Vedi campagna, Approva e Prosegui: `GET /campagne/{id}/post` in ogni stato dopo l'invio, con il piano, le uscite, i post dei canali con tipo di riempitivo, versione corrente, autore, blocchi e avvisi, foto e storico, le foto non usate, l'ultimo errore della generazione; `POST /campagne/{id}/approva` in blocco, con righe di approvazione e decisione; `POST /campagne/{id}/prosegui` | plan §3, §6; spec §2.3, R-14, R-20, R-35 | T1-09, T1-05 | CA-21, CA-22, CA-49 (Prosegui), CA-60 | ☑ |
| T1-43 | Pubblicazione: `pubblica_dovuti()`; tentativo registrato prima della chiamata, tutte le foto del post (per una cartolina la sua immagine), un solo `ok` per post, nuovi tentativi, post `fallito`, campagna `conclusa` secondo `tutti_chiusi()` | plan §4, §5, §6; constitution §1; spec §2.4, R-34 | T1-41, T1-09, T1-05 | CA-36…39, CA-52 (pubblicazione), CA-57 (pubblicazione) | ☑ |

### Corsia 5 · Frontend (Angelo)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-51 | Base: `frontend/` da zero (Vite + React + TypeScript); Mantine, `api/` con un file per modulo, `auth.tsx`, pagina di login con il contatto del consorzio, rotte per ruolo (artigiano → Campagna; operatore e admin → campagne da approvare), ritorno al login a ogni 401 e poi alla pagina di partenza, proxy `/api`; controllo automatico di lint e build a ogni PR (`.github/workflows/frontend.yml`, da concordare con la corsia 0) | plan §3; constitution §2, §4; spec R-29 | T1-01 | login sui dati di esempio; build e lint puliti; README con installazione e avvio | ☑ |
| T1-52 | Artigiano minimo, pagina Campagna: bozza con i canali collegati, gruppi di foto con descrizione, data e stella, avvisi letti dal dettaglio della campagna, invio, stato della campagna | spec §2.1, §4, R-08, R-13, R-19, R-22, R-25; plan §3 | T1-51 | pagina completa sui dati di esempio; build e lint puliti | ☑ |
| T1-53 | Operatore minimo: pagina Campagne da approvare (tutti gli artigiani, con `GET /campagne` e lo stato ripetuto), Vedi campagna in ogni stato dopo l'invio: decisione e piano in cima, elenco per uscite con i post dei canali affiancati, etichetta dei riempitivi, blocchi e avvisi, scheda Foto e profilo, errore accanto a Riprova; Approva, Prosegui, Riprova | spec §2.3, §4, R-14, R-35; plan §3 | T1-51 | pagine complete sui dati di esempio; build e lint puliti | ☑ |

Finché un endpoint non è su `main`, la pagina usa dati di esempio con la forma di plan §3 (`src/api/esempi/`). Il passaggio alle API vere (login di T1-11, canali di T1-14, invio di T1-24, approvazione di T1-42) si chiude in T1-07. La pagina statica di Vedi campagna è approvata e segue il modello a uscite: per T1-53 è il riferimento visivo, da dare nel brief; delle sue azioni lo sprint 1 costruisce solo Approva, Prosegui e Riprova.

**Prestiti per chiudere lo sprint 1** (decisi il 9 ottobre): T1-24 lo fa Gianluca; T1-52 (PR #57) e poi T1-53 li fa Nilton, che ha già fatto T1-51. T1-07 lo fa Giovanni, quando questi tre sono su `main`. Silvia e Angelo restano proprietari delle corsie 2 e 5 e rivedono le PR.

## Sprint 2a · Pagine Profilo e Campagna (profilo, bozza modificabile, archivio della bottega, logo)

**Ordine.** T2a-01 → corsie 1–5 in parallelo → T2a-07. Apertura e chiusura le scrive Giovanni e le approva il team. T2a-11 è già scritto (PR #46) e non aspetta l'apertura. La pagina Campagna di T1-52 (PR #57) ha già, sui dati di esempio, il Bentornato, i passi 10–12 e una vista per stato: T2a-53 e T2b-53 partono da lì e la completano. CA dello sprint: CA-05…CA-08, CA-16, CA-76…CA-78.

### Corsia 0 · Comune (tutto il team)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2a-01 | **Apertura**: migrazione 010 con `foto.pubblicata_su` (per ogni canale la data dell'ultima pubblicazione) e il suo campo in `campagne/models.py`; firme con `NotImplementedError` di `campagne.service.foto_di_archivio(profilo_id, canale, adesso)` e `segna_pubblicata(foto_id, canale, quando)`; `foto_per_id(ids)`, già scritta, per leggere le foto d'archivio di un post; forma delle API del logo e dell'archivio in plan §3; fabbriche `gruppo_di_archivio()` e `campagna_conclusa()`; lato minimo del logo in spec R-40; percorso a mano dello sprint in converge §4 | `alembic/`, `campagne/models.py`, in `campagne/service.py` solo le due firme e `foto_per_id()`, `tests/moduli/*/fabbrica.py`, `docs/agenti/` | plan §2, §3, §6; spec R-27, R-28, R-40 | T1-07 | upgrade e downgrade su DB vuoto; `alembic check` senza differenze; ogni firma approvata da chi la scrive e da chi la usa | ☑ |
| T2a-07 | **Chiusura**: test API del percorso (profilo → bozza modificata → archivio → invio → generazione con foto d'archivio e logo → approvazione → pubblicazione che segna le foto); profilo modificato dopo l'invio: generazione e Riprova usano lo snapshot; frontend sulle API vere; percorso a mano | `tests/percorsi/`, `frontend/src/api/` | converge §4 | tutti i task dello sprint | tutti i CA con S = 2a verdi, compreso CA-16 | ☐ |

### Corsia 1 · Accesso e artigiani (Gianluca)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2a-11 | Profilo: `GET /profilo` (404 se assente) e `PUT /profilo` (crea o aggiorna; 422 per obbligatori mancanti e valori non ammessi); il salvataggio non tocca logo, account social e snapshot delle campagne. È la PR #46 | `artigiani/router.py`, `artigiani/profilo_schemas.py`, `artigiani/service.py` (funzioni nuove) | plan §2, §3; spec §2.1, R-10 | T1-12 | CA-07 (API); 404 senza profilo e lettura con profilo, per CA-05 e CA-06; il profilo salvato non cambia lo snapshot di una campagna inviata | ☑ |
| T2a-12 | Logo: `PUT /profilo/logo` (multipart), `GET /profilo/logo`, `DELETE /profilo/logo`; controllo di tipo reale e peso; file nell'adattatore archivio con il nome del server; il file precedente non si elimina, perché lo usano gli snapshot; se il profilo non si salva il file nuovo si toglie | `artigiani/logo.py` (nuovo), `artigiani/router.py` | spec R-40; plan §3, §5; constitution §3 | T2a-01, T2a-11 | CA-78; CA-77 (profilo: logo sostituito, il file precedente si legge ancora); senza profilo → 404 | ☑ |

### Corsia 2 · Campagne (Silvia)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2a-21 | Modifica della bozza: `PATCH /campagne/{id}` con titolo, date, descrizione e canali; solo in bozza; stessi controlli della creazione; se la data di un gruppo esce dal nuovo periodo → 422 | `campagne/bozza.py` (nuovo), `campagne/router.py`, `campagne/schemas.py` | plan §3; spec R-08, R-12, R-13, R-22 | T2a-01 | CA-08 (API: la bozza riletta ha dati, canali, gruppi e foto), CA-48 (modifica), CA-09 e CA-10 sulla modifica; fuori dalla bozza → 409 | ☑ |
| T2a-22 | Archivio della bottega: gruppi e foto senza campagna (`GET /archivio`, `POST /archivio/gruppi`, `POST /archivio/foto`, eliminazione, `GET /foto/{id}/file` anche per le foto d'archivio: la forma è in plan §3), con i controlli di R-13 sul file; `foto_di_archivio()` secondo R-27, che dice per ogni foto se sul canale non è mai uscita o è uscita da più di 90 giorni; `segna_pubblicata()` | `campagne/archivio.py` (nuovo), `campagne/router.py`, `campagne/schemas.py`, in `campagne/service.py` il corpo delle due funzioni | spec R-13, R-27; plan §2, §3, §6 | T2a-01 | CA-76 (funzione); un test per ogni esclusione di R-27; l'archivio di un altro → 404 | ☑ |

### Corsia 3 · Contenuti (Giovanni)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2a-31 | Foto d'archivio nel piano: analisi dei gruppi d'archivio non ancora analizzati; tra le foto disponibili di un canale anche quelle d'archivio mai uscite lì; riempitivo `archivio` prima della cartolina; le foto di un post si leggono con `campagne.service.foto_per_id()`; controllo del piano e provider finto aggiornati | `contenuti/piano.py`, `contenuti/generazione.py`, `adapters/ai/` | spec R-05, R-27, R-28; plan §4, §5, §6 | T2a-22 | CA-76 (generazione); CA-17 e CA-57 restano verdi; una foto d'archivio non esce due volte sullo stesso canale nella stessa campagna | ☐ |
| T2a-32 | Logo nelle cartoline: il logo dello snapshot, se c'è, sopra il nome della bottega; senza logo la cartolina di oggi; un logo che non si legge non ferma la generazione | `contenuti/cartoline.py` | spec R-28, R-40; constitution §1 | T2a-12 | CA-77 (cartolina: il logo è quello dello snapshot; cambiato dopo l'invio non entra) | ☐ |

### Corsia 4 · Revisione e pubblicazione (Nilton)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2a-41 | Foto pubblicate per canale: dopo ogni `ok` la pubblicazione chiama `campagne.service.segna_pubblicata()` per le foto caricate del post, non per le cartoline; le foto delle versioni si leggono con `campagne.service.foto_per_id()`, così un post con una foto d'archivio si vede e si pubblica; Vedi campagna mostra il riempitivo `archivio` | `pubblicazione/service.py`, `revisione/service.py`, `revisione/schemas.py` | spec R-27, R-28; plan §3, §6 | T2a-22 | CA-76 (pubblicazione); due tick → una sola scrittura, CA-36 resta verde | ☐ |

### Corsia 5 · Frontend (Angelo)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2a-51 | Pagina Profilo, passi 1–9: l'artigiano senza profilo arriva al passo 1; si salva uscendo dal passo 9; gli obbligatori mancanti sono indicati; il passo 7 resta senza logo e archivio. Riserva: Gianluca | `pages/artigiano/profilo/`, `api/artigiani.ts`, `api/esempi/artigiani.ts`, rotte in `App.tsx` | spec §2.1, R-10, R-29; plan §2, §3; constitution §4 | T1-52, T2a-01 | CA-05 e CA-07 sui dati di esempio; build e lint puliti | ☐ |
| T2a-52 | Passo 7 del profilo: logo (carica, sostituisci, togli) e archivio della bottega (gruppi e foto), con gli errori di R-13 e R-40. Riserva: Gianluca | `pages/artigiano/profilo/passo7/`, `api/archivio.ts`, `api/esempi/archivio.ts` | spec R-13, R-27, R-40; plan §3 | T2a-51 | logo e archivio completi sui dati di esempio; build e lint puliti | ☐ |
| T2a-53 | Pagina Campagna completa: Bentornato ("Va bene così" non salva il profilo, "Modifica" apre la pagina Profilo), passi 10–12 con la modifica della bozza, riepilogo e avvisi. Riserva: Nilton | `pages/artigiano/campagna/`, `api/campagne.ts`, `api/esempi/campagne.ts` | spec §2.1, R-08, R-13, R-22, R-25; plan §3 | T1-52, T2a-51 | CA-06 e CA-08 sui dati di esempio; build e lint puliti | ☐ |

## Sprint 2b · Revisione (interventi sul post, decisioni sulla campagna, scadenze, notifiche)

**Ordine.** T2b-01 → corsie 1–5 in parallelo → T2b-07. La corsia 4 ha cinque task, tutti in `revisione`: per questo T2b-44 vive in un file suo ed è prestabile. Le funzioni che cambiano lo stato di un post sono di `contenuti` (T2b-31…T2b-33) e quelle sulla campagna di `campagne` (T2b-21): gli endpoint di `revisione` le chiamano, non le riscrivono. CA dello sprint: CA-23…CA-32, CA-53, CA-55, CA-64…CA-70.

### Corsia 0 · Comune (tutto il team)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2b-01 | **Apertura**: migrazione 011 con la tabella `notifica`; `notifiche/models.py` e `notifiche/domain.py` (tipi di notifica, stati di invio); firme con `NotImplementedError`: `notifiche.crea()`, `accesso.utente()` e la lettura degli operatori, in `campagne` `campagne_di()`, `togli_canale()`, `ultima_nota()`, in `contenuti` `scarta_post_della_campagna()`, `scarta_post_del_canale()`, `scadi_post()`, `annulla_post()`, `riprogramma_post()`, `modifica_post()`, `segna_controllato()`, `accendi_intervento()`, `puo_rigenerare()`, `ferma_generazione()`, in `revisione` `scadenze()`; in `worker.py` il tick chiama `scadenze()` prima di `pubblica_dovuti()`; fabbriche; plan §6 e converge §4 aggiornati | `alembic/`, `notifiche/models.py`, `notifiche/domain.py`, `tabelle.py`, `worker.py`, i `service.py` (solo le firme), `tests/moduli/*/fabbrica.py`, `docs/agenti/` | plan §2, §4, §6; spec R-06, R-30…R-35 | T2a-07 | upgrade e downgrade su DB vuoto; `alembic check` senza differenze; firme approvate; il tick provato con una `scadenze()` finta | ☐ |
| T2b-07 | **Chiusura**: test API del percorso di revisione (modifica, rigenera, togli un canale, approva; respingi; sospendi, riattiva, annulla; scadenza), con le notifiche; frontend sulle API vere; percorso a mano | `tests/percorsi/`, `frontend/src/api/` | converge §4 | tutti i task dello sprint | tutti i CA con S = 2b verdi | ☐ |

### Corsia 1 · Accesso e artigiani (Gianluca)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2b-11 | Notifiche: `crea()` scrive una riga per destinatario (l'artigiano della campagna o gli operatori, secondo il tipo) e accoda `invia_notifica`; lo stesso evento non crea due volte la stessa notifica | `notifiche/service.py` | plan §2, §4, §6; spec §2.2, §4, R-32 | T2b-01 | un test per tipo di notifica, con i suoi destinatari; nessun doppione; nessuna email inviata nei test | ☐ |
| T2b-12 | Email: adattatore (`invia()`, finto, SMTP verso il catcher locale); job `invia_notifica` con 3 tentativi, `stato_invio` e `inviata_il`; testo di ogni tipo di email, con motivo, nota e miniature per la respinta | `adapters/email/`, `notifiche/jobs.py`, `notifiche/testi.py` (nuovo) | plan §4, §5; spec §4, R-18; constitution §3 | T2b-11 | CA-25 (email con motivo, nota e 2 miniature), CA-30 (email della scaduta); errore ×3 → invio fallito; nessun dato personale nei log | ☐ |

### Corsia 2 · Campagne (Silvia)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2b-21 | Funzioni di campagne: `togli_canale()` (il canale va in `canali_tolti`; mai l'ultimo), `ultima_nota()`, `campagne_di()` | in `campagne/service.py` il corpo delle tre funzioni | plan §6; spec R-18, R-32 | T2b-01 | un test per funzione; togliere l'ultimo canale → errore (CA-53, funzione) | ☐ |
| T2b-22 | Cosa vede l'artigiano: elenco e dettaglio delle sue campagne secondo spec §4: nessun piano e nessun post prima dell'approvazione, respinta con motivo, nota e foto da rifare, scaduta con avviso, canale tolto con la nota, mai le note interne; ordine di apertura; campagne passate | `campagne/viste.py` (nuovo), `campagne/router.py`, `campagne/schemas.py` | spec §4, R-15, R-32; plan §3 | T2b-21 | CA-31, CA-70 (API), CA-23 (l'artigiano non vede la nota), CA-53 (l'artigiano vede il canale tolto e la nota) | ☐ |

### Corsia 3 · Contenuti (Giovanni)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2b-31 | Funzioni sui post: `scarta_post_della_campagna()`, `scarta_post_del_canale()`, `scadi_post()`, `annulla_post()`, `riprogramma_post()`, `segna_controllato()`, `ferma_generazione()`; ogni cambio di stato con `verifica_transizione()`; la spunta si azzera a ogni versione e a ogni cambio di data | `contenuti/service.py` (il corpo delle firme) | plan §2, §6; spec R-14, R-30, R-33, R-34, R-35; constitution §1 | T2b-01 | un test per funzione e per transizione vietata; CA-65 e CA-67 (funzioni) | ☐ |
| T2b-32 | Modifica a mano: `modifica_post()` crea una versione `modifica_operatore` con l'autore, validata; con un blocco o senza cambiamenti nessuna versione; non conta cicli; sblocca un post `da_rivedere` | `contenuti/interventi.py` (nuovo) | spec §3, R-02, R-09, R-30; plan §6 | T2b-31 | CA-64 (funzione); dopo 3 rigenerazioni la modifica resta ammessa (CA-28) | ☐ |
| T2b-33 | Rigenera: `puo_rigenerare()`, `accendi_intervento()`, job `rigenera_post` (da zero o da testo proposto, stesse foto, versioni rifiutate come "cosa non rifare", validatore; il ciclo si conta quando nasce la versione; alla terza esecuzione fallita il post resta com'è); `genera_post()` dell'adattatore riceve le versioni rifiutate | `contenuti/interventi.py`, `contenuti/jobs.py`, `adapters/ai/` | plan §4, §5; spec R-03, R-04, R-31 | T2b-32 | CA-26, CA-27, CA-28, CA-66 (funzioni e job) | ☐ |
| T2b-34 | Notifiche della generazione: `campagna_pronta`, `piano_da_rivedere` e `generazione_fallita` agli operatori, una per evento | `contenuti/generazione.py` | plan §4; spec §2.2 | T2b-11 | CA-55 (generazione); una nuova esecuzione non ripete la notifica | ☐ |

### Corsia 4 · Revisione e pubblicazione (Nilton)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2b-41 | Nota, respingi, togli il canale: `POST /campagne/{id}/nota`, `/respingi` (motivo, nota, foto segnate; anche da `piano_da_rivedere`), `/togli-canale`; ognuna con la sua decisione e, dove serve, la notifica | `revisione/decisioni.py` (nuovo), `revisione/router.py`, `revisione/schemas.py` | plan §3, §6; spec §2.3, R-15, R-18, R-32 | T2b-11, T2b-21, T2b-31 | CA-23, CA-24, CA-25 (API e notifica), CA-53 | ☐ |
| T2b-42 | Interventi sul post: `POST /post/{id}/modifica`, `/controllato`, `/rigenera`, `/riprogramma`; solo dove R-16 lo ammette | `revisione/interventi.py` (nuovo), `revisione/router.py`, `revisione/schemas.py` | plan §3; spec R-03, R-16, R-30, R-31, R-34 | T2b-32, T2b-33 | CA-26…CA-29, CA-64, CA-65, CA-67 (API); intervento in corso → approva 409, partito da più di 10 minuti → approva ammesso (CA-22, CA-66) | ☐ |
| T2b-43 | Sospendi, riattiva, annulla: `POST /campagne/{id}/sospendi`, `/riattiva` con i post in arretrato da pubblicare, `/annulla`; ognuna con la sua decisione | `revisione/sospensione.py` (nuovo), `revisione/router.py`, `revisione/schemas.py` | plan §3; spec R-16, R-33 | T2b-31 | CA-32 | ☐ |
| T2b-44 | Scadenze: `scadenze(adesso)`: i post `da_approvare` con la data passata diventano `scaduto`; la campagna diventa `scaduta` sotto la metà dei post chiesti, o alle 00:00 del giorno di inizio se non ha un piano; una campagna ferma da 30 minuti in `inviata` o `in_generazione` va in `generazione_fallita`. Prestabile a Silvia | `revisione/scadenze.py` (nuovo) | spec R-06, R-35; plan §4, §6 | T2b-11, T2b-31 | CA-30, CA-68; due tick di seguito: il secondo non cambia nulla | ☐ |
| T2b-45 | Campagne da approvare: `GET /da-approvare` con conteggi dei post, "entro quando" e ultima nota, dalla più urgente; in `GET /campagne/{id}/post` la spunta e l'intervento in corso; notifica `post_fallito` dalla pubblicazione | `revisione/letture.py` (nuovo), `revisione/router.py`, `revisione/schemas.py`, `pubblicazione/service.py` | plan §3; spec §4, R-38 | T2b-11, T2b-21 | CA-69, CA-55 (post fallito) | ☐ |

### Corsia 5 · Frontend (Angelo)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2b-51 | Vedi campagna, azioni sul post: modifica a mano, spunta "va bene", rigenera nelle due modalità con l'intervento in corso e il limite dei cicli, storico delle versioni con l'autore. Riserva: Nilton | `pages/operatore/vedi-campagna/post/`, `api/interventi.ts`, `api/esempi/interventi.ts` | spec §3, §4, R-03, R-30, R-31; plan §3 | T1-53, T2b-01 | CA-26…CA-29, CA-64, CA-65 sui dati di esempio; build e lint puliti | ☐ |
| T2b-52 | Vedi campagna, decisioni: nota interna, respingi con le foto segnate, togli il canale, sospendi, riattiva, annulla, riprogramma; pagina Campagne da approvare con conteggi, "entro quando" e ultima nota. Riserva: Nilton | `pages/operatore/vedi-campagna/decisioni/`, `pages/operatore/da-approvare/`, `api/decisioni.ts`, `api/esempi/decisioni.ts` | spec §2.3, §4, R-18, R-32, R-33, R-34, R-38; plan §3 | T1-53, T2b-01 | CA-23…CA-25, CA-32, CA-53, CA-67, CA-69 sui dati di esempio; build e lint puliti | ☐ |
| T2b-53 | Pagina Campagna dell'artigiano per stato: le viste di spec §4, la riga di scelta tra più campagne, le campagne passate, la respinta con le foto da rifare. Riserva: Gianluca | `pages/artigiano/campagna/viste/`, `api/esempi/campagne.ts` | spec §4, R-15, R-29 | T2a-53, T2b-01 | CA-31 e CA-70 sui dati di esempio; build e lint puliti | ☐ |

## Sprint 3 · Ritocco foto e pagine dell'operatore (versioni delle foto, anagrafica, account social, calendario, promemoria)

**Ordine.** T3-01 → corsie 1–5 in parallelo → T3-07. La corsia 2 ha un solo task: Silvia è la persona a cui si presta T3-45. T3-13 aspetta l'adattatore di T3-41, e T3-43 aspetta T3-13: sono in quest'ordine apposta. CA dello sprint: CA-33…CA-35, CA-40…CA-43, CA-56, CA-71…CA-74.

### Corsia 0 · Comune (tutto il team)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T3-01 | **Apertura**: migrazione 012 con `versione_foto`, `versione_post_foto.versione_foto_id`, `post.n_ritocchi_foto` e `anagrafica_artigiano`; modelli e valori ammessi; firme con `NotImplementedError`: in `contenuti` `puo_ritoccare()`, `scegli_foto()`, `cambia_foto()`, `sposta_post()`, in `accesso` `password_provvisoria()`, in `artigiani` `account_social()`, `anagrafica_di()`; `ritocca_immagine()` nell'interfaccia dell'adattatore AI e `collega_account()` in quella del social; job `promemoria` ogni ora in `worker.py`; fabbriche; plan §6 e converge §4 aggiornati | `alembic/`, i `models.py` e i `domain.py` che cambiano, `tabelle.py`, `worker.py`, i `service.py` (solo le firme), `adapters/ai/base.py`, `adapters/social/base.py`, `tests/moduli/*/fabbrica.py`, `docs/agenti/` | plan §2, §4, §5, §6; spec R-03, R-36, R-37 | T2b-07 | upgrade e downgrade su DB vuoto; `alembic check` senza differenze; firme approvate | ☐ |
| T3-07 | **Chiusura**: test API del percorso (nuovo artigiano con il cambio password, account collegato, campagna con le foto ritoccate, cambia foto e sposta, approvazione, calendario, sospensione per account scaduto, promemoria); frontend sulle API vere; percorso a mano | `tests/percorsi/`, `frontend/src/api/` | converge §4 | tutti i task dello sprint | tutti i CA con S = 3 verdi | ☐ |

### Corsia 1 · Accesso e artigiani (Gianluca)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T3-11 | Cambio password obbligato: `POST /auth/cambia-password`; finché `deve_cambiare_password` è acceso ogni altra chiamata dell'utente → 403; `password_provvisoria()` | `accesso/router.py`, `accesso/schemas.py`, `accesso/service.py` | plan §3, §6; spec R-29, R-37; constitution §3 | T3-01 | CA-73 (accesso); i test delle altre corsie restano verdi | ☐ |
| T3-12 | Nuovo artigiano e anagrafica: `POST /artigiani` (201 con la password provvisoria, una sola volta), `PUT /artigiani/{id}/anagrafica`, `POST /artigiani/{id}/password-provvisoria`; codice ART assegnato dal sistema; `anagrafica_di()` | `artigiani/anagrafica.py` (nuovo), `artigiani/router.py`, `artigiani/schemas.py` | plan §2, §3, §6; spec R-37 | T3-11 | CA-73 (creazione); i 422 di R-37; la password non compare nei log né in una seconda risposta | ☐ |
| T3-13 | Account social: `POST /artigiani/{id}/social/{piattaforma}/collega` (simulato), permesso cifrato, `account_social()` | `artigiani/social.py` (nuovo), `artigiani/router.py` | plan §2, §3, §5, §6; spec R-07, R-22; constitution §3 | T3-41 | account collegato visibile in `GET /canali`; stato e scadenza letti da `account_social()`; nessun permesso nei log | ☐ |

### Corsia 2 · Campagne (Silvia)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T3-21 | Campagne di un artigiano e iscrizione sospesa: `GET /campagne?artigiano=&stato=` per l'operatore; con l'iscrizione sospesa l'invio → 409, e le campagne approvate continuano | `campagne/viste.py`, `campagne/router.py`, il controllo nell'invio | plan §3; spec §4, R-37, R-38 | T3-12 | CA-74; il filtro restituisce le chiuse di un solo artigiano | ☐ |

### Corsia 3 · Contenuti (Giovanni)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T3-31 | Versioni delle foto e ritocco nella generazione: la versione 0 è l'originale e resta; dopo il piano si ritoccano le sole foto usate (versione 1); `ritocca_immagine()` nel provider finto; la versione del post punta alla foto ritoccata | `contenuti/foto.py` (nuovo), `contenuti/generazione.py`, `adapters/ai/` | plan §2, §4, §5; spec §2.2, R-17, R-24 | T3-01 | CA-33; la ripresa non ritocca due volte la stessa foto | ☐ |
| T3-32 | Ritocca, scegli, cambia foto, sposta: `puo_ritoccare()`, job `ritocca_foto`, `scegli_foto()`, `cambia_foto()`, `sposta_post()` | `contenuti/foto.py`, `contenuti/interventi.py`, `contenuti/jobs.py` | plan §4, §6; spec §3, R-03, R-17, R-31, R-36 | T3-31 | CA-34, CA-35, CA-71, CA-72 (funzioni e job) | ☐ |
| T3-33 | Ritaglio e calendario: una sola funzione di ritaglio per canale, per anteprima e pubblicazione; `GET /campagne/{id}/calendario` | `contenuti/ritaglio.py` (nuovo), `contenuti/router.py`, `contenuti/schemas.py` | plan §3; spec §4, R-21, R-36 | T3-31 | CA-56; un test per proporzione ammessa e non ammessa; in un carosello valgono le proporzioni della prima foto | ☐ |

### Corsia 4 · Revisione e pubblicazione (Nilton)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T3-41 | Adattatore social, collegamento: `collega_account()` simulato, con esito ok ed errore a comando | `adapters/social/` | plan §5 | T3-01 | nessuna chiamata di rete nei test | ☐ |
| T3-42 | Foto e data del post: `POST /post/{id}/ritocca-foto`, `/scegli-foto`, `/cambia-foto`, `/sposta` | `revisione/interventi.py`, `revisione/router.py`, `revisione/schemas.py` | plan §3; spec R-03, R-16, R-31, R-36 | T3-32 | CA-34, CA-35, CA-71, CA-72 (API); in campagna attiva o sospesa → 409 | ☐ |
| T3-43 | Pubblicazione, sospensione e ritaglio: permesso scaduto o account scollegato → campagna `sospesa` con gli avvisi; le foto escono nella versione scelta e ritagliate con la funzione di contenuti | `pubblicazione/service.py` | plan §4, §6; spec R-07, R-36 | T3-13, T3-33 | CA-40; un post esce con la versione ritoccata e ritagliata | ☐ |
| T3-44 | Promemoria: un promemoria per ogni campagna `in_revisione` o `piano_da_rivedere` a meno di 48 ore dall'inizio, una volta sola | `revisione/promemoria.py` (nuovo), `revisione/jobs.py` | plan §4; spec R-06 | T3-01 | CA-42 | ☐ |
| T3-45 | Letture dell'operatore: `GET /artigiani` (R-38) e `GET /artigiani/{id}` per sezioni, con la differenza tra anagrafica e profilo e le cose da sistemare. Prestabile a Silvia | `revisione/artigiani.py` (nuovo), le sue rotte in `revisione/router.py`, `revisione/schemas.py` | plan §3; spec §4, R-38 | T3-12 | CA-41, CA-43 | ☐ |

### Corsia 5 · Frontend (Angelo)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T3-51 | Pagine dell'operatore: ingresso con "Da sistemare", elenco artigiani con ricerca e filtri nel browser, pagina artigiano per sezioni, campagne chiuse con il filtro per esito. Riserva: Nilton | `pages/operatore/ingresso/`, `pages/operatore/artigiani/`, `api/operatore.ts`, `api/esempi/operatore.ts` | spec §4, R-29, R-38; plan §3 | T2b-52, T3-01 | CA-41 e CA-43 sui dati di esempio; build e lint puliti | ☐ |
| T3-52 | Nuovo artigiano e accesso: nuovo artigiano con la password provvisoria mostrata una volta, anagrafica, collegamento degli account, cambio password obbligato al primo accesso. Riserva: Gianluca | `pages/operatore/nuovo-artigiano/`, `pages/CambiaPassword.tsx`, `auth.tsx`, `api/anagrafica.ts`, `api/esempi/anagrafica.ts` | spec R-29, R-37; plan §3 | T3-51 | CA-73 sui dati di esempio; build e lint puliti | ☐ |
| T3-53 | Vedi campagna, foto e calendario: ritocca di nuovo, scegli foto, cambia foto, sposta, anteprima ritagliata; calendario in Vedi campagna e nella pagina Campagna dell'artigiano. Riserva: Nilton | `pages/operatore/vedi-campagna/foto/`, `pages/operatore/vedi-campagna/calendario/`, `pages/artigiano/campagna/calendario/`, `api/foto.ts`, `api/esempi/foto.ts` | spec §3, §4, R-03, R-36; plan §3 | T2b-51, T3-01 | CA-34, CA-35, CA-56, CA-71, CA-72 sui dati di esempio; build e lint puliti | ☐ |

## Sprint successivi (si dividono in task quando si arriva)
Le corsie restano le stesse: ogni novità va alla corsia del suo modulo; tabelle, stati e funzioni condivise alla corsia 0.
- **4 · Monitoraggio e demo**: metriche con il filtro per periodo (pagina dell'operatore; per l'artigiano nella pagina Campagna), report settimanale agli operatori, riepilogo di fine campagna all'artigiano, E2E, dati demo, provider LiteLLM in `adapters/ai/` con i suoi prompt (corsia 3; la libreria è già in `requirements.txt`) e prova con OpenAI. CA-44, CA-45, CA-75.
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

## Follow-up della revisione del 9 ottobre · issue #39–41

Emersi dalla revisione delle PR #23 e #24 (T1-22, T1-23). Corsia 0 e corsia 2 insieme, su
`feature/39-41-chiusura-revisione`: revisione di tutto il team, merge dell'admin. Le caselle
descrivono la preparazione per la revisione, come sopra.

| Issue | Corsia | Task / fatto quando | Preparato |
|---|---|---|---|
| #39 | 0/2 | Contratti `artigiani.service.profilo()` e `post_a_settimana()` in plan §6; campagne senza SQL diretto su `profilo_bottega` e senza costanti copiate | ☑ |
| #40 | 0 | `core/limite_richiesta.py`: 413 oltre `RICHIESTA_MAX_BYTE`, con `Content-Length` e a blocchi; una foto da 10 MB passa | ☑ |
| #41 | 2 | `gruppo_id` obbligatorio in `POST /campagne/{id}/foto` (422 se manca); nessun gruppo nasce dal caricamento | ☑ |

## Follow-up di T1-32 · issue #44–45

Emersi scrivendo T1-32 (limiti e controllo del piano). Corsia 0, su
`feature/44-45-post-chiesti-e-stelle`: revisione di tutto il team, merge dell'admin, **prima**
della PR di T1-32, che usa la funzione nuova. Le caselle descrivono la preparazione per la
revisione, come sopra.

| Issue | Corsia | Task / fatto quando | Preparato |
|---|---|---|---|
| #44 | 0 | Contratto `campagne.service.post_chiesti()` in plan §6; il dettaglio della campagna lo usa: la formula di R-05 è scritta una volta sola | ☑ |
| #45 | 0 | R-23: con più foto con la stella che post chiesti, il piano ne usa almeno quanti sono i post chiesti; il controllo del piano la segue in T1-32 | ☑ |
