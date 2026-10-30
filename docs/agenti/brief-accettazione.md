# Brief · Corsia 10 · Simulazione di accettazione (T4-100…T4-108)

Per chi fa un task della corsia 10. Decisione: ADR-120. Leggi prima `constitution.md`, poi **solo** la sezione del tuo task qui sotto e le parti di `docs/accettazione-post-mvp.md` che cita. Dove il codice è diverso da come è descritto qui, è un rilievo, oppure fermati e chiedi.

**Decisioni prese con le domande** (30/10): vedi la tabella in testa a `accettazione-post-mvp.md` §12.

**Regole di lavoro per tutti i task.**
- **Branch.** Un branch `feature/T4-1xx-<breve>`, aperto dal branch della simulazione e unito lì. Fai solo il tuo task.
- **Codice dell'app.** Non si tocca (`backend/app/`, `frontend/src/`, `alembic/`). Si aggiungono test, script e report.
- **Difetti.** Un difetto trovato è un rilievo con il test in `@pytest.mark.xfail(strict=True, reason="RL-0xx: …")`, mai una correzione. `uv run pytest` resta verde.
- **Strumenti.** Gli strumenti si lanciano con `uvx`, con `uv run --with …` o con `npx`, senza entrare in `backend/requirements.txt`. Una libreria che serve ai test che restano nel repository (per esempio `hypothesis`) va in un `backend/requirements-accettazione.txt` separato, con nome, motivo e licenza nella PR.
- **Prove automatiche.** Nei test nessuna chiamata reale ad AI, Meta o email. Le uniche prove vere sono quelle a mano di T4-105 (Meta, pagina di prova) e di T4-107 (AI, tetto 2 €).
- **Database.** Le prove di carico e di guasto girano su un database dedicato (`adflow_accettazione`), mai su `adflow` o `adflow_test`.
- **Report.** In report, screenshot e log nessun segreto, token, cookie o dato personale vero. I report stanno in `docs/accettazione/report/T4-1xx-<nome>.md` (o `.json`, `.html`).
- **Registro.** Ogni task aggiunge le sue righe a `docs/accettazione/rilievi.md` nel formato di §1.2, con ID progressivi. Non modifica le righe degli altri.
- **Fatto quando.** Il «Fatto quando» del task, `uv run pytest` e `uv run black --check .` verdi, e la casella in `tasks.md`.

---

## T4-100 · Preparazione della corsia 10

**Stima**: 1 sessione · **Dipende da**: T3-07

**File e modifiche**:
- `docs/ADR.md`: riga 120 (§12.2).
- `docs/agenti/tasks.md`: sezione «Sprint 4 · Simulazione di accettazione dell'MVP» (§12.1) e riga 10 nella tabella delle aree.
- `docs/agenti/brief-accettazione.md`: nuovo, con il testo di §12.3.
- `docs/accettazione/rilievi.md`: nuovo, solo l'intestazione e la tabella vuota di §1.2.
- `docs/accettazione/report/.gitkeep`: nuovo.
- `allinea.py`: intestazione della corsia con più cifre (`### Corsia (\d+) · …`, riga 89); scelta della corsia da 0 a 10 (righe 378-379) e il docstring.
- `backend/tests/test_allinea.py`: un caso con lo sprint 4, la corsia 10 e un task `T4-100`.
- `docs/accettazione-post-mvp.md`: lo stato passa da «bozza» a «domande con risposta, corsia generata».

**Da non toccare**: codice dell'app; `AGENTS.md` (lo sprint corrente cambia solo quando lo decide il team).

**Fatto quando**: `uv run python allinea.py 10` mostra T4-101 tra i pronti; `tests/test_allinea.py` verde con la corsia 10; comandi di converge §1 verdi.

**Nota**: cambia `allinea.py`, un file comune: va scritto nella PR.

## T4-101 · Linea di base

**Stima**: 1–2 sessioni · **Dipende da**: T4-100 · **Copre**: §4.1, §4.2, §5.3, §6 (copertura) · R-05, R-06, R-07

**File e modifiche**:
- `docs/accettazione/report/T4-101-ricostruzione.md`: clone in una cartella pulita, `allinea.py`, migrazioni da vuoto, seed, test, build; tempi e passi non scritti.
- `docs/accettazione/report/T4-101-scansioni.md`, più i report grezzi: `pip-audit`, `npm audit --omit=dev`, `bandit -ll`, `semgrep`, `gitleaks` su tutta la storia, `mypy` su `domain.py` e `service.py`, `pip-licenses`.
- `docs/accettazione/report/T4-101-copertura.md`: `pytest --cov=app --cov-branch`, per file, confrontata con le soglie di §6.
- `docs/accettazione/strumenti/tracciabilita.py`: legge `spec.md` e i nomi dei test e produce `docs/accettazione/report/T4-101-tracciabilita.md`.
- `docs/accettazione/rilievi.md`: le righe del task.

**Da non toccare**: codice dell'app; `requirements.txt`; `.github/`.

**Fatto quando**: report salvati; tracciabilità generata; un rilievo per R-05, R-06 e R-07, e per ogni risultato alto o critico. Un segreto valido trovato da gitleaks va segnalato **subito** a Giovanni: è un blocco assoluto e non si scrive nel report.

## T4-102 · Permessi e superficie HTTP

**Stima**: 2 sessioni · **Dipende da**: T4-100 · **Copre**: §5.2, §5.4 punti 1–5 · R-01, R-02, R-12, R-15, R-16, R-17

**File e modifiche**:
- `backend/tests/accettazione/permessi/matrice.py`: l'esito atteso per operazione × ruolo (anonimo, artigiano A, artigiano B, operatore, admin), 57 operazioni, rotte congelate comprese. L'atteso viene da costituzione §3 e da `spec.md`, non dal comportamento attuale.
- `backend/tests/accettazione/permessi/test_matrice.py`: legge `app.openapi()`, prova ogni cella, fallisce se un'operazione non ha la sua riga.
- `backend/tests/accettazione/test_intestazioni.py`, `test_origine.py`, `test_upload_ostili.py`, `test_foto_pubblica_firma.py`, `test_bola_nuovi_endpoint.py` (Cambia foto da campagna e archivio, `foto-possibili`, storico AI), `test_limite_azioni_ai.py`.
- `docs/accettazione/report/T4-102-permessi.md`: la matrice con gli esiti.
- `docs/accettazione/rilievi.md`: le righe del task.

**Da non toccare**: codice dell'app; `campagne/archivio.py` (congelato, si prova soltanto).

**Fatto quando**: matrice completa e verde, con le differenze in `xfail(strict=True)`; un rilievo per ognuno di R-01, R-02, R-12, R-15, R-16, R-17, con esito confermato o smentito. Una lettura confermata dei dati di un altro artigiano è un **blocco assoluto**: va segnalata subito a Giovanni.

## T4-103 · Concorrenza

**Stima**: 1–2 sessioni · **Dipende da**: T4-100 · **Copre**: §7.3 · R-03, R-04

**File e modifiche**:
- `backend/tests/accettazione/concorrenza/conftest.py`: aiuto con `threading.Barrier`, una sessione e una connessione a PostgreSQL per thread. Il database di test è quello delle fixture di plan §7, con i commit veri che servono alla concorrenza.
- `backend/tests/accettazione/concorrenza/test_approvazione.py`, `test_interventi.py`, `test_invio.py`, `test_sovrapposte.py`, `test_voto.py`, `test_pubblicazione.py`: gli scenari di §7.3.
- `docs/accettazione/report/T4-103-concorrenza.md`: scenario, ripetizioni, esito, correzione proposta (blocco della riga, vincolo unico o aggiornamento condizionale), senza applicarla.
- `docs/accettazione/rilievi.md`: le righe del task.

**Da non toccare**: codice dell'app; `alembic/`.

**Fatto quando**: ogni scenario ha un test. I verdi sono ripetuti 50 volte senza fallire. Un difetto si rende deterministico quando si può (per esempio fermando il primo thread dopo il controllo e prima della scrittura) e allora va in `xfail(strict=True)`. Se resta intermittente va in `xfail(strict=False)`, con il rilievo e la percentuale di fallimenti su 50 ripetizioni. R-03 e R-04 sono confermati o smentiti.

## T4-104 · Invarianti e proprietà

**Stima**: 2 sessioni · **Dipende da**: T4-100 · **Copre**: §4.3, §6 (mutazioni, macchine a stati, fuzzing)

**File e modifiche**:
- `backend/requirements-accettazione.txt`: nuovo; `hypothesis` (MPL-2.0), con nome, motivo e licenza nella PR. `schemathesis` e `mutmut` si lanciano con `uvx`.
- `backend/tests/accettazione/invarianti/`: un file per invariante di costituzione §1, con gli attacchi di §4.3.
- `backend/tests/accettazione/proprieta/test_macchina_campagna.py`, `test_macchina_post.py`: `RuleBasedStateMachine` con gli invarianti come controlli; saltati se `hypothesis` non è installato.
- `docs/accettazione/report/T4-104-proprieta.md`: hypothesis (10 000 sequenze, lanciato a parte), schemathesis con i due ruoli, mutmut su `domain.py`, `interventi.py`, `validatore.py`, `foto_pubblica.py` con i mutanti sopravvissuti analizzati.
- `docs/accettazione/rilievi.md`: le righe del task.

**Da non toccare**: codice dell'app; `test_confini.py` (il controllo su `.stato` di §1.8 va in `tests/accettazione/invarianti/`).

**Fatto quando**: ogni invariante con almeno un test che prova a violarlo; report dei tre strumenti; ogni controesempio, 500 o mutante significativo è un rilievo.

## T4-105 · Esercizio, guasti e carico

**Stima**: 2 sessioni · **Dipende da**: T4-100 · **Copre**: §6 (backup, documentazione operativa), §7.1, §7.2, §7.4, §7.5 · R-09, R-10, R-11, R-15

**File e modifiche**:
- `backend/tests/accettazione/guasti/`: un test per ogni riga di §7.4, con `monkeypatch` sugli adattatori finti e l'orologio iniettato; il timeout dopo la pubblicazione (D-07) documentato così com'è oggi.
- `docs/accettazione/carico/locustfile.py` e `README.md`: dati dalle `fabbrica.py` su `adflow_accettazione`; `locust` lanciato con `uvx`.
- `docs/accettazione/report/T4-105-carico.md`: i numeri ipotizzati (dichiarati come tali), carico, picco, durata (2–8 ore), upload, worker, storico AI con 100 000 chiamate.
- `docs/accettazione/report/T4-105-esercizio.md`: avvio su processi locali (API, worker, proxy TLS temporaneo come `test_proxy_http_reale.py`), ZAP baseline su quel proxy, backup e ripristino di database e foto cronometrati, che cosa si vede oggi di latenza, coda, ritardo di pubblicazione e spesa AI.
- `docs/accettazione/report/T4-105-meta-prova.md`: **una** pubblicazione a mano sulla pagina Meta di prova di un post approvato del seed, con l'esito e i tempi, senza token né id veri nel report.
- `docs/accettazione/rilievi.md`: le righe del task.

**Da non toccare**: codice dell'app; `adflow` e `adflow_test`; la pagina Meta vera, salvo quella di prova.

**Fatto quando**: test dei guasti presenti, con le differenze in `xfail(strict=True)`; report di carico ed esercizio; ripristino riuscito o rilievo; un rilievo per R-09, R-10, R-11 e per ogni misura che manca.

## T4-106 · Frontend

**Stima**: 2 sessioni · **Dipende da**: T4-100 · **Copre**: §4.4, §6 (frontend, E2E, accessibilità, contratto) · R-08

**File e modifiche**:
- `frontend/e2e/percorso-demo.spec.ts` e `frontend/playwright.config.ts`: il percorso della demo di converge §4 a due ruoli, da database vuoto, con `@axe-core/playwright`.
- `frontend/package.json`: script `test:e2e`; devDependencies `@playwright/test` (Apache-2.0), `@axe-core/playwright` (MPL-2.0), con nome, motivo e licenza nella PR.
- `docs/accettazione/report/T4-106-frontend.md`: esito del percorso, violazioni di axe, differenze tra i tipi generati con `npx openapi-typescript` e `src/api/*.ts` (il file generato non resta nel repository).
- `docs/accettazione/rilievi.md`: le righe del task.

**Da non toccare**: `frontend/src/`; `.github/`.

**Fatto quando**: lo script E2E gira in locale con video e traccia nel report; report di axe e del contratto; un rilievo per R-08 e per ogni passo che fallisce; `npm run build` e `npm run lint` puliti.

## T4-107 · Analisi a tavolino

**Stima**: 2 sessioni · **Dipende da**: T4-100 · **Copre**: §5.1, §5.2, §5.4 punti 6–8, §5.5 · R-13, R-14, R-16

**File e modifiche**:
- `docs/accettazione/report/T4-107-minacce.md`: flusso dei dati, confini di fiducia, STRIDE di §5.2; per ogni minaccia una difesa che esiste (con il file) o un rilievo.
- `backend/tests/accettazione/test_prompt_injection.py`: con l'adattatore finto, testi ostili nel profilo, nei nomi e nel testo di partenza; il validatore e l'approvazione fermano ogni uscita.
- `docs/accettazione/report/T4-107-ai-vera.md`: **una** prova a mano con l'AI vera su una campagna di prova con profilo ostile; tetto di **2 €**, fermarsi prima di superarlo; costo letto dallo storico AI; nessun post approvato né pubblicato.
- `docs/accettazione/report/T4-107-log-segreti.md`: ricerca di email, password e token riconoscibili in stderr e nello storico AI; permessi di `.env`; `--forwarded-allow-ips`; effetto della rotazione di `login_limite_segreto` (R-13).
- `docs/accettazione/report/T4-107-dati-personali.md`: analisi delle lacune GDPR (artt. 17, 28, 30, 35, capo V) e AI Act art. 50, con lo storico AI (R-16) e la cifratura dei token futuri (R-14).
- `docs/accettazione/report/T4-107-asvs-l2.md`: checklist ASVS 5.0 L2, con requisito, prova (file, test o report) ed esito; ciò che non si può provare in locale è `non provato`.
- `docs/accettazione/rilievi.md`: le righe del task.

**Da non toccare**: codice dell'app; nessuna firma, informativa o ADR «approvato»: sono proposte.

**Fatto quando**: i sei report; ogni minaccia e ogni requisito ASVS con una prova o un rilievo; costo della prova con l'AI vera registrato e sotto i 2 €.

## T4-108 · Sintesi

**Stima**: 1 sessione · **Dipende da**: tutti i task dello sprint · **Copre**: §8

**File e modifiche**:
- `docs/accettazione/sintesi.md`: ogni casella di §8 con un esito (soddisfatto, non soddisfatto, non provato) e i rilievi che la giustificano; i blocchi assoluti in cima; i limiti dell'MVP in parole semplici, da usare con il cliente; i task di correzione proposti, in ordine di gravità, ognuno con il rilievo e il test `xfail` che lo chiude.
- `docs/accettazione/rilievi.md`: classe di ogni rilievo (`correggere`, `limite MVP`, `roadmap`, `proposta`).
- `docs/accettazione-post-mvp.md`: nuova versione con ciò che la simulazione ha insegnato (stime, strumenti che non sono serviti, rischi mancati).

**Da non toccare**: codice dell'app; `tasks.md` oltre alla propria casella (i task di correzione sono proposte, li inserisce il team).

**Fatto quando**: nessun rilievo senza classe; nessuna casella di §8 senza esito; sintesi rivista da Giovanni.
