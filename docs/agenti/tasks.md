# Tasks

Lo sprint di lavoro è lo **Sprint 3 · MVP** (ADR-114, `perimetro-mvp.md`): consegna e pitch il 6 novembre, codice bloccato il 30 ottobre. Gli sprint 1, 2a e 2b sono chiusi: i loro task sono in `docs/archivio/tasks-sprint-1-2.md`. Ciò che non entra nell'MVP è in `docs/ROADMAP.md`.

**Da dove riparto?** Dalla radice: `uv run python allinea.py <area>`. Allinea la tua copia a `main` e legge questa pagina per te: stampa i task pronti della tua area (quelli con le dipendenze già ☑), cosa leggere e il branch da aprire. Le caselle di questa pagina sono l'unica fonte dello stato: non tenere elenchi a parte.

| Area | Chi | Di cosa si occupa |
|---|---|---|
| 0 · Comune e deliverable | tutto il team | Perimetro nel codice (T3-01), proposta tecnica e pitch, pagine statiche, dati della demo, sistemazione definitiva, chiusura |
| 1 · Nuovo artigiano e calendario | Gianluca | Creazione dell'artigiano da parte dell'operatore, calendario della campagna |
| 2 · Foto e invio | Silvia | Sistemazione locale delle foto, invio senza minimo e con la dichiarazione, indirizzo pubblico delle foto |
| 3 · AI vera | Giovanni | Adattatore LiteLLM, prova su 10 post, generazione MVP, immagini AI |
| 4 · Meta | Nilton | Pagina di prova, adattatore Meta, pubblicazione reale |
| 5 · Frontend | Angelo | Vedi campagna e pagina Campagna ridotte all'MVP, calendario, nuovo artigiano |
| 6 · Interventi e richiesta all'artigiano | Giovanni | ADR-116: interventi sul post dopo l'approvazione, cambia foto e sposta, sospendi e riattiva, richiesta all'artigiano (`brief-interventi.md`) |
| 7 · Pagine, archivio foto e calendario | Giovanni | ADR-117: ingresso e campagne dell'artigiano, pagine degli artigiani per l'operatore, archivio foto in sola lettura, calendario settimanale (`brief-pagine.md`); il restyling è passato alla corsia 8 |
| 8 · Interfaccia ed esperienza d'uso | da assegnare | ADR-118: scelte d'uso e visive fatte da chi sviluppa con la guida di `brief-interfaccia.md`, tema, testi, layout e telefono, prova con due persone, senza cambi di comportamento |

Nelle tabelle le aree si chiamano ancora "Corsia", perché `allinea.py` le legge così.

**Regole dello sprint MVP** (ADR-114, decisioni F1–F3):

- **Un'area non è un elenco di file proibiti.** Il task tocca i file che gli servono, con i loro test. Se cambia un file su cui lavora un'altra area, lo dice a chi ci lavora.
- **Una PR per task**, su `feature/<id>-<breve>`. La rivede un collega; i controlli di GitHub devono essere verdi; unisce l'admin. Se la PR cambia composizione, `core/`, `alembic/`, `backend/requirements.txt` o un `domain.py`, la rivede il referente dei file comuni.
- **Le firme nascono nel task che le usa.** Niente apertura con `NotImplementedError` e niente colonna "Tocca".
- **Una libreria nuova** entra in `backend/requirements.txt` nella PR del task che la usa, con nome, motivo e licenza.
- **Frontend.** Finché l'endpoint non è su `main` la pagina usa i dati di esempio (`src/api/esempi/`); passa alle API vere nel suo task appena l'endpoint c'è, o al più tardi in T3-07.
- **La chiusura (T3-07)** è la prova del percorso della demo da database vuoto, non un controllo di proprietà.

## Sprint 3 · MVP (AI vera, immagini AI, pubblicazione su Meta, calendario, deliverable)

**Ordine.** T3-01 apre lo sprint. Senza aspettarlo partono T3-02, T3-03, T3-11, T3-12, T3-21, T3-31, T3-41, T3-53 e T3-54; gli altri quando ciò che sta in "Dipende da" è su `main`. CA dello sprint: quelli di spec §6.

**Date.** T3-31 entro il 16/10 e la prova su 10 post (T3-32) entro il 20/10. Meta (T3-41) parte il 14/10; se Instagram non pubblica entro il 23/10 resta simulato (D1). Corsia 6 (ADR-116): una persona, un task alla volta nell'ordine di `brief-interventi.md` §2; tutto su `main` entro il 24/10, prima di T3-08 parte 2, altrimenti ciò che manca resta fuori. Corsia 7 (ADR-117): una persona, un task alla volta nell'ordine di `brief-pagine.md` §2; lavoro dal 22 al 27/10, tutto su `main` entro il 28/10, altrimenti ciò che manca resta fuori. Corsia 8 (ADR-118): nell'ordine di `brief-interfaccia.md` §5, dal 26 al 30/10; ciò che il 30/10 non è su `main` resta com'è oggi. Codice bloccato il 30/10; dal 2 al 6/11 solo correzioni, slide, video e prove.

### Corsia 0 · Comune e deliverable (tutto il team)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T3-01 | **Perimetro nel codice**: toglie, congela e nasconde il codice secondo `perimetro-mvp.md`, con le istruzioni di `brief-T3-01.md` (ora in `docs/archivio/`) | `perimetro-mvp.md`; `brief-T3-01.md` | — | comandi di converge §1 verdi; `tests/test_confini.py` verde; nella PR le decisioni applicate e il numero dei test prima e dopo | ☑ |
| T3-02 | **Proposta tecnica** (G1–G3), un solo documento per il cliente in tre capitoli: 1 analisi dei requisiti, 2 architettura, schema dati e stack, 3 piano con costi e tempi. Responsabili dei capitoli: da assegnare | `perimetro-mvp.md`; spec §0–§6; plan §1–§5; constitution §2; questa pagina; `docs/ROADMAP.md` | — | cap. 1: requisiti funzionali e non funzionali, attori, casi d'uso; cap. 2: componenti, flussi, adattatori, tabelle, stack con le motivazioni; cap. 3: milestone, ore del team, costi di sviluppo e di esercizio (AI con i numeri di T3-32, hosting); tutto al perimetro MVP; riletto da un collega | ☐ |
| T3-03 | **Pagine statiche all'MVP**: `docs/pagine` allineate al perimetro (vedi `perimetro-mvp.md`, sezione Pagine statiche), mappa `index.html` aggiornata. Giovanni con Claude | `perimetro-mvp.md` | — | ogni pagina MVP senza ciò che è tolto o congelato e con ciò che è nuovo; le pagine fuori MVP segnate come roadmap nella mappa; riletto da Angelo | ☑ |
| T3-05 | **Pitch**: slide e scaletta dei 10 minuti, con la roadmap e la pagina statica delle metriche come anteprima. Coordina Giovanni | la proposta tecnica di T3-02; `docs/ROADMAP.md`; `docs/pagine` | T3-02, T3-03 | slide pronte; due prove cronometrate sotto i 10 minuti | ☐ |
| T3-06 | **Dati della demo**: nel seed un artigiano con profilo e foto vere, collegato alla pagina di prova Meta; una campagna pronta da inviare | `perimetro-mvp.md`; plan §1 | T3-01 | da database vuoto un comando prepara la demo; nessuna password o token nel codice | ☑ |
| T3-07 | **Chiusura**: percorso della demo provato da database vuoto (converge §4) e video di riserva registrato | converge §4 | tutti i task dello sprint | tutti i CA di spec §6 verdi; percorso a mano senza errori; video salvato | ☐ |
| T3-08 | **Sistemazione definitiva**: documenti di `docs/agenti/` allo stato di oggi (la storia in `docs/archivio/`), codice e test senza resti degli sprint, nomi coerenti, nessun cambio di comportamento. La parte 1 (documenti, archivio, file che nessun task aperto tocca) è fatta; la parte 2 segue `brief-sistemazione.md`. Entro il 29/10 | `brief-sistemazione.md`; converge §1 | T3-06, T3-11, T3-12, T3-21, T3-22, T3-23, T3-31, T3-32, T3-33, T3-34, T3-42, T3-43, T3-51, T3-52, T3-53, T3-54, T3-61, T3-62, T3-63, T3-64, T3-65, T3-66, T3-71, T3-72, T3-73, T3-74, T3-75, T3-76, T3-77, T3-78 | schema OpenAPI identico prima e dopo; comandi di converge §1 verdi; percorso della demo senza errori da un clone pulito; nella PR l'inventario approvato e il numero dei test prima e dopo | ☐ |
| T3-09 | **Controlli di sicurezza**: protezione CSRF same-origin attiva in produzione, tracciamento richieste e log JSONL senza segreti, validazione HTTPS di `FOTO_URL_PUBBLICO`, probe SAST/DAST locali con runner e documento di valutazione. Porta su `main` il lavoro del branch SEC-01 | constitution §3; `docs/sicurezza-accesso.md`; `docs/valutazione-sicurezza.md` | — | `tests/test_sast_security.py`, `test_dast_security.py`, `test_log_jsonl.py` verdi; `tests/test_confini.py` verde; `.env.example` aggiornato; step CI dei probe verde | ☑ |

### Corsia 1 · Nuovo artigiano e calendario (Gianluca)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T3-11 | Nuovo artigiano: `POST /artigiani` `{email, nome}` per l'operatore; password provvisoria generata e restituita una sola volta; account social come quelli del seed | plan §3; spec R-37; constitution §3 | — | CA-79; la password non compare nei log né in una seconda risposta | ☑ |
| T3-12 | Calendario della campagna: `GET /campagne/{id}/calendario` | plan §3; spec §4, R-45 | — | CA-56 | ☑ |

### Corsia 2 · Foto e invio (Silvia)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T3-21 | Sistemazione delle foto: una funzione locale con Pillow (rotazione, GPS tolto, ritaglio per canale, 1080 px, autocontrasto, JPEG) offerta da `campagne.service`; la usano anteprima e pubblicazione | spec R-21, R-42; constitution §1 | — | CA-81; il file originale non cambia | ☑ |
| T3-22 | Invio MVP: toglie il minimo di 4 foto (A5); dichiarazione obbligatoria, salvata nella fotografia del profilo; avviso `foto_poche` con il numero dei post che avranno un'immagine AI | plan §3; spec R-13, R-25, R-41 | T3-01 | CA-14, CA-54 | ☑ |
| T3-23 | Indirizzo pubblico della foto per Instagram: `GET /foto/{id}/pubblica` con firma a tempo, foto sistemata per il canale | plan §3; spec R-42; constitution §3 | T3-21 | firma scaduta o alterata → 404; nessun altro dato esposto | ☑ |

### Corsia 3 · AI vera (Giovanni)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T3-31 | Adattatore LiteLLM (`brief-ai.md`): `analizza_gruppo()`, `pianifica_campagna()`, `genera_post()` con risposte strutturate; errori nei cinque tipi; prompt versionati; uso restituito per il costo; tabella `chiamata_ai` (migrazione 012) | plan §2, §5; spec R-35, R-44 | — | traduzione degli errori provata con chiamate simulate; nessuna chiamata reale nei test; CA-82 per analisi, piano e testi | ☑ |
| T3-32 | Prova su 10 post e scelta del modello: comando di prova su una campagna del seed; qualità, costo, tempi e riscritture del piano | `perimetro-mvp.md` (A9, M2) | T3-31 | tabella dei risultati nella PR; modello scelto in `.env.example`; tetto di spesa impostato sul conto del provider | ☑ |
| T3-33 | Generazione MVP: post = frequenza; il codice passa all'AI solo le foto migliori per punteggio, fino ai post chiesti; post scoperti `immagine_ai`; un post = una foto; provider finto allineato (`brief-ai.md`) | spec §2.2, R-05, R-21, R-28; plan §4 | T3-01 | CA-17, CA-57 (senza immagini), CA-80 | ☑ |
| T3-34 | Immagini AI di rimpiazzo (`brief-ai.md`): `genera_immagine()` (finto e LiteLLM), tappa Immagini dopo il piano al posto delle cartoline, che si tolgono (A6), foto `creata_ai` quadrata 1:1, la stessa per l'uscita su entrambi i canali, dicitura nel testo, costo registrato | spec R-28, R-43, R-44; plan §4, §5 | T3-31, T3-33 | CA-57 con le immagini; CA-82 per le immagini | ☑ |

### Corsia 4 · Meta (Nilton)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T3-41 | Configurazione Meta (`brief-meta.md`): Pagina di prova, account Instagram professionale, app Business, permessi, token della Pagina, Page Publishing Authorization; un post pubblicato a mano su Facebook e su Instagram | `perimetro-mvp.md` (Meta in breve) | — | due post visibili sulla pagina di prova; variabili in `.env.example` con valori finti; procedura nel README del backend | ☑ |
| T3-42 | Adattatore Meta (`brief-meta.md`): `pubblica()` riceve anche il canale e gli indirizzi pubblici delle foto; Facebook e Instagram sulla sola pagina di prova di `.env`; `SOCIAL_PROVIDER` (finto o meta) | plan §5; spec R-01, R-21 | T3-41 | CA-83; CA-36…CA-38 ancora verdi con il finto | ☑ |
| T3-43 | Pubblicazione reale provata (`brief-meta.md`): tunnel di sola lettura per le foto, un post della demo pubblicato dal worker su entrambi i canali | `perimetro-mvp.md` (D1) | T3-42, T3-23 | post pubblicati dal tick; se Instagram non pubblica entro il 23/10 resta simulato e la PR lo dice | ☐ |

### Corsia 5 · Frontend (Angelo)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T3-51 | Vedi campagna MVP: solo approva, respingi, riprova, modifica a mano e rigenera; "Immagine AI" sui post; costo AI della campagna | spec §2.3, §4, R-44 | T3-01 | build e lint puliti; nella pagina nessuna azione congelata | ☑ |
| T3-52 | Pagina Campagna MVP: niente stella né gruppi `create_ai`, nessun minimo di foto, dichiarazione al passo 12, avviso dei post con immagine AI; passo 7 del profilo senza logo né archivio | spec §2.1, R-13, R-25, R-41 | T3-01 | CA-14 e CA-54 nella pagina; build e lint puliti | ☑ |
| T3-53 | Calendario: elenco per giorno in Vedi campagna e nella vista dell'artigiano | spec §4, R-45 | — | CA-56 nella pagina (dati di esempio finché T3-12 non è su `main`); build e lint puliti | ☑ |
| T3-54 | Nuovo artigiano: pagina dell'operatore con email e nome; password provvisoria mostrata una sola volta | spec R-37 | — | CA-79 nella pagina (dati di esempio finché T3-11 non è su `main`); build e lint puliti | ☑ |

### Corsia 6 · Interventi e richiesta all'artigiano (Giovanni)

Ogni task ha in `brief-interventi.md` i file da toccare e da non toccare, le firme, i messaggi d'errore, gli schemi e i nomi dei test: si legge la sezione del proprio task, non tutto il brief.

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T3-60 | **Preparazione della corsia 6** (ADR-116): regole in costituzione, perimetro, spec e plan; `brief-interventi.md`; i task; pagine statiche; valori nei `domain.py`. Giovanni con Claude | ADR-116; `perimetro-mvp.md` | — | documenti coerenti tra loro; comandi di converge §1 verdi; `tests/test_allinea.py` verde con la corsia 6 | ☑ |
| T3-61 | **Interventi sul post, backend**: `interventi_ammessi()` dalla tabella di `contenuti/domain.py`; modifica dopo l'approvazione con la sua approvazione; sposta; annulla il post con la nota; riprogramma, sospendi con la nota, riattiva e annulla scongelati; `interventi` in Vedi campagna | `brief-interventi.md` §1 e §T3-61; spec R-16, R-30, R-33, R-34, R-36 | T3-60 | CA-29, CA-32, CA-67, CA-72, CA-84, CA-85 verdi; comandi del backend verdi | ☑ |
| T3-62 | **Cambia foto, backend**: foto possibili e cambia foto, in revisione e dopo l'approvazione | `brief-interventi.md` §1 e §T3-62; spec R-16, R-36 | T3-61 | CA-71 verde; comandi del backend verdi | ☑ |
| T3-63 | **Richiesta all'artigiano, backend**: chiedi, carica la foto nuova, invia la risposta; la richiesta nel dettaglio, nell'elenco dell'artigiano e in Campagne da approvare | `brief-interventi.md` §1 e §T3-63; spec R-46, R-13, R-41 | T3-60 | CA-86…CA-90 verdi; CA-13 e CA-31 ancora verdi; comandi del backend verdi | ☑ |
| T3-64 | **Vedi campagna, interventi**: i pulsanti dagli `interventi` di ogni post (modifica, rigenera, cambia foto, sposta, annulla, riprogramma); sospendi, riattiva, annulla la campagna | `brief-interventi.md` §1 e §T3-64; `docs/pagine/AdFlow-operatore-campagna.html` | T3-60 | build e lint puliti; dati di esempio finché T3-61 e T3-62 non sono su `main`, poi API vere; screenshot nella PR | ☑ |
| T3-65 | **Richiesta all'artigiano, frontend**: finestra e riquadro dell'operatore, segno in Campagne da approvare, riquadro dell'artigiano nella pagina Campagna | `brief-interventi.md` §1 e §T3-65; `docs/pagine/AdFlow-operatore-campagna.html`; `docs/pagine/AdFlow-campagna-stati.html` | T3-60 | build e lint puliti; dati di esempio finché T3-63 non è su `main`, poi API vere; screenshot nella PR | ☑ |
| T3-66 | **Prova della corsia 6**: test di percorso e percorso a mano in due finestre, operatore e artigiano | `brief-interventi.md` §T3-66; converge §4 | T3-61, T3-62, T3-63, T3-64, T3-65 | CA-91 verde; passi 4, 6 e 9 di converge §4 senza errori; screenshot nella PR | ☑ |

### Corsia 7 · Pagine, archivio foto e calendario (Giovanni)

Ogni task ha in `brief-pagine.md` i file da toccare e da non toccare, le firme, i messaggi d'errore, gli schemi e i nomi dei test: si legge la sezione del proprio task, non tutto il brief.

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T3-70 | **Preparazione della corsia 7** (ADR-117): perimetro (blocco H, E1), spec, plan, `brief-pagine.md`, i task, pagine statiche; la PR #135 tolta da `main`. Giovanni con Claude | ADR-117; `perimetro-mvp.md` | — | documenti coerenti tra loro; comandi di converge §1 verdi; `tests/test_allinea.py` verde con la corsia 7 | ☑ |
| T3-71 | **Artigiani per l'operatore, backend**: `accesso.artigiani()`, `GET /artigiani` (revisione), `GET /artigiani/{id}` (artigiani), `GET /campagne?artigiano=` | `brief-pagine.md` §1 e §T3-71; spec R-38 | T3-70 | CA-92, CA-93, CA-94 verdi; CA-69 ancora verde; comandi del backend verdi | ☑ |
| T3-72 | **Archivio foto, backend**: `GET /archivio-foto`, in sola lettura, a blocchi per campagna | `brief-pagine.md` §1 e §T3-72; spec R-47 | T3-70 | CA-95, CA-96 verdi; comandi del backend verdi | ☑ |
| T3-73 | **Calendario settimanale, backend**: `GET /calendario?dal=` per artigiano e operatore | `brief-pagine.md` §1 e §T3-73; spec R-45, R-48 | T3-70 | CA-97, CA-98 verdi; CA-56 ancora verde; comandi del backend verdi | ☑ |
| T3-74 | **Ingresso e campagne dell'artigiano, frontend**: Ingresso, Campagne, barra, arrivo dopo l'accesso, pagina Campagna su una campagna scelta | `brief-pagine.md` §1 e §T3-74; `docs/pagine/AdFlow-ingresso.html`, `AdFlow-campagne.html` | T3-70 | build e lint puliti; l'artigiano arriva sull'Ingresso; screenshot nella PR | ☑ |
| T3-75 | **Artigiani per l'operatore, frontend**: elenco scorrevole, pagina dell'artigiano, campagne dell'artigiano | `brief-pagine.md` §1 e §T3-75; `docs/pagine/AdFlow-operatore-elenco.html`, `AdFlow-operatore-artigiano.html`, `AdFlow-operatore-artigiano-campagne.html` | T3-74 | build e lint puliti; dati di esempio finché T3-71 non è su `main`, poi API vere; screenshot nella PR | ☑ |
| T3-76 | **Archivio foto, frontend**: un componente per i due ruoli | `brief-pagine.md` §1 e §T3-76; `docs/pagine/AdFlow-archivio-foto.html` | T3-70 | build e lint puliti; dati di esempio finché T3-72 non è su `main`, poi API vere; screenshot nella PR | ☑ |
| T3-77 | **Calendario settimanale, frontend**: griglia fatta a mano per i due ruoli, Questa settimana nell'Ingresso | `brief-pagine.md` §1 e §T3-77; `docs/pagine/AdFlow-calendario.html` | T3-74 | build e lint puliti; dati di esempio finché T3-73 non è su `main`, poi API vere; screenshot nella PR | ☑ |
| T3-78 | **Prova della corsia 7**: test di percorso e percorso a mano in due finestre, operatore e artigiano | `brief-pagine.md` §T3-78; converge §4 | T3-71, T3-72, T3-73, T3-74, T3-75, T3-76, T3-77 | CA-99 verde; passi della demo di converge §4 senza errori; screenshot nella PR | ☑ |

### Corsia 8 · Interfaccia ed esperienza d'uso (da assegnare)

`brief-interfaccia.md` non decide colori, caratteri né scelte d'uso: guida chi sviluppa a farle, con la funzione di ogni scelta e possibilità reali già pronte. Il suo §1 dice che cosa non si tocca e vale per ogni task; poi si legge la sezione del proprio task. Nessun cambio di comportamento: rotte, campi, chiamate, stati e messaggi del backend restano quelli di prima.

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T3-80 | **Preparazione della corsia 8** (ADR-118): perimetro (riga H7 e blocco I), `brief-interfaccia.md`, i task, T3-79 tolto dalla corsia 7, `allinea.py` con la corsia 8. Il referente con Claude | ADR-118; `perimetro-mvp.md` | T3-78 | documenti coerenti tra loro; `tests/test_allinea.py` verde; `allinea.py 8` stampa T3-81 pronto | ☑ |
| T3-81 | **Scelte d'uso**: percorso della demo a 1280 e 375 px, poi modo d'uso per ruolo, schermi, gerarchia delle azioni e tono dei testi, scelti con la guida e scritti nel §4 | `brief-interfaccia.md` §2, §3 (S1, S2, S3, S8), §T3-81 | T3-80 | righe S1, S2, S3, S8 del §4 compilate e approvate dal referente; note e screenshot di oggi nella PR | ☑ |
| T3-82 | **Scelte visive**: stile, palette, caratteri e icone provati su due pagine statiche di prova, scelti con la guida e scritti nel §4 con i valori esatti | `brief-interfaccia.md` §2, §3 (S4–S7), §T3-82 | T3-81 | righe S4–S7 del §4 compilate e approvate; valori esatti scritti; screenshot e contrasti nella PR | ☑ |
| T3-83 | **Tema e componenti di base**: le scelte di S4–S7 nell'app e nelle pagine statiche insieme (assorbe T3-79) | `brief-interfaccia.md` §1, §T3-83; ADR-113 | T3-82 | app e pagine statiche con lo stesso stile; controllo del §1.5 senza risultati; build e lint puliti; screenshot prima e dopo di ogni pagina della mappa | ☑ |
| T3-84 | **Testi**: inventario e riscrittura dei testi visibili con il tono di S8, nell'app e nelle pagine statiche, senza i testi fissi | `brief-interfaccia.md` §1.4, §T3-84 | T3-81 | tabella prima → dopo nella PR; testi fissi invariati; controllo del §1.5 senza risultati; build e lint puliti | ☑ |
| T3-85 | **Layout e telefono**: le scelte di S1, S2 e S3 sulle pagine, prima il percorso della demo dell'artigiano | `brief-interfaccia.md` §1.2, §T3-85 | T3-83, T3-84 | percorso della demo dell'artigiano senza scorrimento orizzontale alle larghezze di S2; 1280 px come dopo T3-83; controllo del §1.5 senza risultati; screenshot nella PR | ☑ |
| T3-86 | **Prova con due persone** e correzioni piccole | `brief-interfaccia.md` §T3-86 | T3-85 | note della prova nella PR; correzioni solo di stile o testo, oppure in roadmap; controllo del §1.5 senza risultati | ☑ |
| T3-87 | **Prova della corsia 8**: percorso della demo in due finestre, operatore a 1280 px e artigiano alle larghezze di S2, e controllo del §1.5 su tutta la corsia | `brief-interfaccia.md` §1.5, §T3-87; converge §4 | T3-83, T3-84, T3-85, T3-86 | passi 1–9 di converge §4 senza errori; testi fissi invariati; screenshot prima e dopo di ogni pagina della demo | ☑ |

## Dopo l'MVP

Ciò che non entra nell'MVP (ritocco delle foto, ingresso dell'operatore, anagrafica, collegamento degli account, promemoria, metriche, immagini AI chieste dall'artigiano) è in `docs/ROADMAP.md`.

## Follow-up aperti

`allinea.py` li mostra finché la casella non è spuntata. Quelli chiusi sono in `docs/archivio/tasks-sprint-1-2.md`.

| Issue | Corsia | Task / fatto quando | Preparato |
|---|---|---|---|
| #17 | 0 | Configurazione proxy/cookie documentata e testata localmente con TLS; evidenza nello staging reale da allegare | ☐ |
