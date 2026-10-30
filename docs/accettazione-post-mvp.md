# Simulazione di accettazione dell'MVP

> **⚠️ DOCUMENTO PRELIMINARE, DA VALUTARE.**
> È una bozza, non è approvata e non fa testo. Non cambia il perimetro dell'MVP, i task di `docs/agenti/tasks.md` né le regole di `docs/agenti/`: dove qualcosa non torna valgono quei documenti. Nessun punto va eseguito finché le domande qui sotto non hanno una risposta e la corsia 10 non è stata generata.

**Stato:** bozza da discutere · **Prima versione:** 24/10/2026 su `6a8e2ed` · **Questa versione:** 30/10/2026 su `main` a `8c01e2b` (sprint 3 chiuso, corsie 8 e 9 comprese) · **Corsia:** 10 · **ADR:** 120 · **Task:** T4-100…T4-108

I riferimenti a file e righe valgono per il commit `8c01e2b`.

## Che cosa è e che cosa non è

È una **simulazione di accettazione**. Si fa finta di dover autorizzare la produzione e lo sviluppo completo, e si mette l'MVP alla prova come farebbe chi deve firmare: sicurezza, permessi, concorrenza, invarianti, guasti, carico, frontend, dati personali.

Lo scopo **non è correggere**. Lo scopo è:

1. **trovare** i problemi e renderli ripetibili (un test, un comando, un report);
2. **classificarli**: da correggere, limite dell'MVP accettato, o lezione che migliora questa proposta;
3. **conoscere i limiti dell'MVP** prima di promettere qualcosa al cliente.

Le correzioni vengono dopo, come task a parte decisi sul registro dei rilievi (T4-108). La simulazione la eseguono **agenti AI guidati da Giovanni, un task alla volta, in sequenza**. Ciò che richiede persone o soldi esterni (consulente privacy, pentest esterno, hosting, numeri del cliente) si **simula** e il rilievo lo dice in chiaro.

## Come si procede

1. **Domande.** L'agente fa a Giovanni le nove domande qui sotto, **una alla volta**, propone la risposta predefinita e non decide al posto suo.
2. **Corsia.** Con le risposte si genera la corsia 10 (§12): il blocco per `docs/agenti/tasks.md`, il brief `docs/agenti/brief-accettazione.md` e la riga ADR-120.
3. **Esecuzione.** Un task alla volta, ognuno su un branch `feature/T4-1xx-<breve>`. Ogni task aggiunge righe al registro dei rilievi (§1.2).
4. **Sintesi.** T4-108 classifica i rilievi, propone i task di correzione e riscrive questa proposta con ciò che si è imparato.

**Perché corsia 10 e ADR-120.** La corsia 9 e l'ADR-119 sono già usati dalle «Richieste dopo la prova» (T3-900…T3-927). La numerazione dei task segue quella della corsia 9: T4-100, T4-101, …

### Le nove domande

| # | Domanda | Risposte possibili (in grassetto la predefinita) | Che cosa cambia |
|---|---|---|---|
| 1 | Quanto della simulazione volete fare? | **Tutta**; Solo il nucleo (permessi, concorrenza, invarianti) | Con il nucleo spariscono T4-105, T4-106 e T4-107; T4-108 lo scrive tra i limiti. |
| 2 | Che cosa si fa quando un test trova un difetto? | **Solo il rilievo, con il test in `xfail(strict=True)`**; Correzioni piccole ammesse nello stesso task | Con le correzioni ammesse, ogni task può cambiare il codice dell'app, in una PR separata. |
| 3 | Gli strumenti di verifica entrano in CI? | **No, solo in locale con i report salvati**; Sì, in un workflow non bloccante; Sì, bloccante | Cambia T4-101 e i file `.github/workflows/` toccati. |
| 4 | Dove gira lo «staging»? | **Processi locali** (API, worker e proxy TLS temporaneo, come la prova della issue #17); `docker compose` in locale; Un hosting vero | Cambia T4-105 e T4-107; con il compose T4-101 scrive anche `deploy/`. |
| 5 | Da dove vengono i numeri di carico? | **Ipotizzati nel task e dichiarati come ipotesi**; Li do io | Cambia il «Fatto quando» di T4-105. |
| 6 | La prompt injection si prova con l'AI vera? | **No, solo con l'adattatore finto e il validatore**; Una prova a mano con l'AI vera e un tetto di spesa | Con l'AI vera T4-107 ha una prova a mano, fuori dai test, con il costo registrato. |
| 7 | Meta si tocca? | **No, solo l'adattatore finto**; Sì, la pagina di prova | Cambia i guasti di T4-105. |
| 8 | Le rotte congelate `/api/archivio…` entrano nelle prove? | **Sì, nella matrice e negli attacchi, senza modificarle**; No, si escludono | Cambia T4-102; un difetto lì diventa un rilievo «roadmap». |
| 9 | Quando e dove si lavora? | **Da subito, su branch da `integrazione-166-167`; niente su `main` prima della consegna del 6/11**; Dopo il 6/11, da `main` | Cambia la base dei branch e la data di inizio. |

## Indice

0. [Sintesi](#0-sintesi)
1. [Metodo e registro dei rilievi](#1-metodo-e-registro-dei-rilievi)
2. [Che cosa è cambiato dalla prima versione](#2-che-cosa-è-cambiato-dalla-prima-versione)
3. [Stato verificato oggi](#3-stato-verificato-oggi)
4. [Fase 1 · Conformità alle specifiche](#4-fase-1--conformità-alle-specifiche)
5. [Fase 2 · Sicurezza](#5-fase-2--sicurezza)
6. [Fase 3 · Qualità in tutte le parti](#6-fase-3--qualità-in-tutte-le-parti)
7. [Fase 4 · Stress, concorrenza e guasti](#7-fase-4--stress-concorrenza-e-guasti)
8. [Fase 5 · Criteri di giudizio](#8-fase-5--criteri-di-giudizio)
9. [Piano della simulazione](#9-piano-della-simulazione)
10. [Ipotesi e decisioni aperte](#10-ipotesi-e-decisioni-aperte)
11. [Appendice](#11-appendice)
12. [Corsia 10](#12-corsia-10)

---

## 0. Sintesi

L'MVP ha basi solide:
- 1997 test su PostgreSQL vero;
- confini tra moduli controllati da un test;
- password con scrypt e token di sessione salvati solo come hash;
- firme confrontate a tempo costante;
- upload controllati sui byte reali.

Per la demo basta. La simulazione serve a sapere **quanto manca** per la produzione e per lo sviluppo completo, con prove e non con impressioni.

Le domande a cui risponde:
- **Permessi:** un artigiano può leggere o toccare i dati di un altro? La matrice va provata su tutte le 57 operazioni.
- **Concorrenza:** due operatori che approvano insieme, rigenerazioni in parallelo, campagne sovrapposte.
- **Invarianti:** gli 11 invarianti della costituzione resistono a chi prova a violarli?
- **Guasti:** che cosa succede se il database, l'AI o Meta si fermano a metà?
- **Esercizio:** l'MVP si installa, si rilascia e si ripristina seguendo solo i documenti?
- **Dati personali e AI Act:** quali lacune ci sono? Lo storico AI ora conserva prompt e risposte.

Il prodotto della simulazione è il **registro dei rilievi** (§1.2), più una nuova versione di questa proposta.

## 1. Metodo e registro dei rilievi

### 1.1 Metodo

Il criterio è uno solo: **conta ciò che si può dimostrare di nuovo**. Ogni affermazione («è sicuro», «regge», «rispetta la specifica») porta con sé un test, un comando o un report che chiunque del team può rifare.

| Fase | Domanda | Prova |
|---|---|---|
| F1 | Il software fa ciò che dice la specifica? | Matrice requisiti → CA → test; invarianti attaccati da test |
| F2 | È sicuro quanto serve a un'app con dati personali e token di terzi? | Matrice dei permessi, scansioni, attacchi mirati, checklist ASVS L2 |
| F3 | Ogni parte è verificata? | Copertura dei rami, mutazioni, E2E, contratto API, migrazioni |
| F4 | Come si comporta sotto carico, in concorrenza e con i guasti? | Test con barriera, guasti provocati, report di carico |
| F5 | Che cosa direbbe chi deve firmare? | Criteri di §8 valutati uno per uno sul registro |

Gravità:
- **Alta**: bloccherebbe la produzione.
- **Media**: va risolta prima dello sviluppo completo.
- **Bassa**: si pianifica.
- **Da verificare**: ipotesi fondata sul codice, da confermare con un test.

### 1.2 Registro dei rilievi

File: `docs/accettazione/rilievi.md`, creato da T4-100. Ogni task aggiunge le sue righe; nessuno cancella le righe degli altri.

| Colonna | Contenuto |
|---|---|
| ID | `RL-001`, `RL-002`, … in ordine di scoperta |
| Task | Il task che l'ha trovato (T4-1xx) |
| Rischio | Il R-xx di §3 o l'invariante, se c'è |
| Che cosa | Una frase: che cosa succede e perché è un problema |
| Come si riproduce | Il test (`percorso::nome`) o il comando, e il report in `docs/accettazione/report/` |
| Gravità | Alta, Media, Bassa |
| Esito | `confermato`, `smentito` (l'ipotesi di §3 non regge), `non provato` (con il motivo) |
| Classe | `correggere`, `limite MVP`, `roadmap`, `proposta` (migliora questo documento) |

**Regole per i test che trovano un difetto.**
- Il test resta nel repository con `@pytest.mark.xfail(strict=True, reason="RL-0xx: …")`. Così la CI resta verde, il difetto resta documentato, e il giorno in cui qualcuno lo corregge il test passa e obbliga a togliere il marcatore.
- Anche un'ipotesi smentita ha un rilievo, con esito `smentito`: è un'informazione utile quanto un difetto.
- Nei report non ci sono segreti, token, cookie o dati personali veri.

## 2. Che cosa è cambiato dalla prima versione

La prima versione (24/10, `6a8e2ed`) era un piano di sviluppo di 6 settimane per cinque persone, con consulente, pentest esterno e staging su un hosting da scegliere. Questa versione:

- **Scopo:** da piano di accettazione a simulazione. I task producono rilievi, non correzioni.
- **Esecutori:** agenti AI in sequenza; le parti esterne si simulano.
- **Base:** `main` a `8c01e2b`. La corsia 9 ha aggiunto lo storico AI con voto, Rigenera immagine, Cambia foto da gruppo, campagna e archivio, le campagne sovrapposte, gli orari occupati, le proporzioni vere e la migrazione 013. Le operazioni dell'API passano da 52 a **57**, di cui **36** cambiano stato (29 POST, 2 PUT, 1 PATCH, 4 DELETE). I test passano da 1070 a **1997**.
- **Issue #17:** la parte locale è chiusa (`tests/moduli/accesso/test_proxy_http_reale.py`, `qa/issue-17/README.md`), ma la issue resta aperta per il proxy di uno staging pubblico.
- **Superati:** la sezione «prima della consegna» (doppia approvazione e cambio d'ora del 25/10) e il riferimento alla corsia 8 «proposta». La doppia approvazione (R-03) resta nel piano come scenario di T4-103; il cambio d'ora si prova sul prossimo, il 28/03/2027.
- **Rischi nuovi:** R-16 e R-17 (§3), dalla superficie della corsia 9.

Le correzioni già fatte nella prima versione restano valide:
- `httpx2` serve al `TestClient`, mentre `httpx` è importato e non dichiarato;
- il CSRF è di gravità bassa o media grazie a `SameSite=Lax`;
- il tick del worker è serializzato;
- il token Meta non è cifrato, coerente con il perimetro.

## 3. Stato verificato oggi

Ipotesi trovate leggendo `main` a `8c01e2b`, senza modifiche. Ogni riga dice dove guardare e quale task la prova. Gli «Da verificare» diventano rilievi `confermato` o `smentito`.

| ID | Che cosa | Dove | Gravità | Task |
|---|---|---|---|---|
| R-01 | L'app non imposta header di sicurezza globali (CSP, HSTS, `frame-ancestors`, `Referrer-Policy`). `X-Content-Type-Options: nosniff` c'è solo sulle risposte con i file delle foto. Anche l'esempio Nginx di `sicurezza-accesso.md` non aggiunge gli header di sicurezza. | `app/main.py`; `moduli/campagne/router.py:236,283`; `docs/sicurezza-accesso.md:35-45` | Alta in prod. | T4-102 |
| R-02 | Nessun controllo di `Origin` o `Sec-Fetch-Site` sulle 36 operazioni che cambiano stato; protegge solo `SameSite=Lax`, che non copre i sottodomini dello stesso sito. | `moduli/accesso/router.py:71-79`; `moduli/accesso/service.py:163-169` | Bassa/Media | T4-102 |
| R-03 | `revisione.approva()` legge la campagna senza bloccare la riga, controlla `in_revisione` e poi scrive. `Approvazione` non ha vincoli unici. Due richieste parallele possono passare entrambe. | `moduli/revisione/service.py:155-184`; `moduli/revisione/models.py:9` | Da verificare | T4-103 |
| R-04 | `n_rigenerazioni_testo` si incrementa in Python e `contenuti` non blocca le righe: i limiti `MAX_RIGENERAZIONI = 3` e `MAX_RIGENERAZIONI_IMMAGINE = 3` vanno provati in parallelo. Solo `accesso`, `campagne/service.py` e `campagne/archivio.py` usano `with_for_update`. | `moduli/contenuti/interventi.py:56,77-79,509,809`; `moduli/contenuti/domain.py:79` | Da verificare | T4-103 |
| R-05 | `httpx` è importato ma non dichiarato in `requirements.txt`: arriva tramite litellm. | `adapters/social/meta.py:25` | Media | T4-101 |
| R-06 | Niente lockfile né hash; `pytest`, `httpx2`, `black`, `pre-commit` e `cryptography` stanno nello stesso file del runtime. | `backend/requirements.txt` | Media | T4-101 |
| R-07 | La CI fa test, black, lint e build (`backend.yml`, `frontend.yml`). Mancano analisi delle dipendenze, analisi statica di sicurezza, ricerca dei segreti, controllo dei tipi Python, copertura ed E2E. | `.github/workflows/` | Media | T4-101 |
| R-08 | Il frontend non ha test: gli script sono `dev`, `build`, `lint`, `preview`. | `frontend/package.json:6-11` | Media | T4-106 |
| R-09 | Nel repository non c'è nulla per il rilascio: niente container, compose, configurazione completa del proxy o rollback. | radice del repo | Alta in prod. | T4-105 |
| R-10 | Issue #17: la parte locale è chiusa, ma la verifica sul proxy di uno staging pubblico manca e la issue è aperta. | `docs/sicurezza-accesso.md:47`; `qa/issue-17/` | Alta in prod. | T4-105 |
| R-11 | Le foto stanno su disco locale (`archivio_foto_dir`, predefinito `./archivio_foto`): un `pg_dump` da solo non è un backup, e due istanze non vedono gli stessi file. | `core/config.py:67`; `adapters/archivio/disco.py` | Media in prod. | T4-105 |
| R-12 | Le rotte congelate `/api/archivio…` (5 operazioni, tra cui 2 DELETE) restano montate. | `moduli/campagne/router.py:316-384`; `moduli/campagne/archivio.py` | Bassa | T4-102 |
| R-13 | `login_limite_segreto` firma sia i contatori del login sia gli indirizzi pubblici delle foto: cambiarlo invalida le foto di una pubblicazione in corso. | `core/limite_login.py:32`; `moduli/campagne/foto_pubblica.py:29` | Bassa | T4-107 |
| R-14 | La costituzione §3 chiede «permessi social cifrati»: non servono nell'MVP, ma con il collegamento degli account sì (chiavi, rotazione, revoca). | `docs/agenti/constitution.md` §3 | Prerequisito | T4-107 |
| R-15 | Il limite di frequenza esiste solo sul login. Invio, Rigenera testo, Rigenera immagine e Rifai il post fanno partire chiamate AI a pagamento senza un limite nell'applicazione. | `core/limite_login.py`; `moduli/contenuti/interventi.py` | Media | T4-102, T4-105 |
| R-16 | **Nuovo.** Lo storico AI (migrazione 013) conserva prompt e risposta di ogni chiamata, quindi anche il profilo della bottega e i testi. È visibile agli operatori. Non c'è una regola di conservazione e la tabella cresce senza limite. | `alembic/versions/013_storico_ai.py`; `moduli/contenuti/models.py:208-210`; `moduli/contenuti/router.py:54-126` | Media | T4-102, T4-107 |
| R-17 | **Nuovo.** Cambia foto da campagna e archivio e `/post/{id}/foto-possibili` leggono foto oltre la campagna del post: va provato che non escano mai foto di un'altra bottega (BOLA). | `moduli/contenuti/router.py`; `moduli/campagne/router.py:210` | Da verificare | T4-102 |

### Punti di forza verificati

- Password con scrypt e salt da `secrets`.
- Token di sessione con `secrets.token_urlsafe(32)`; nel database solo l'hash.
- Firme confrontate con `hmac.compare_digest`.
- Cookie httpOnly, `SameSite=Lax`, Secure obbligatorio in produzione, provati dietro un proxy TLS locale (#17).
- Limite dei tentativi di accesso su PostgreSQL, per IP e per account.
- Upload: estensioni ammesse, magic bytes, 10 MB per file, 12 MB per richiesta.
- Foto sistemata senza EXIF e GPS, con un tetto di pixel.
- Pubblicazione: tentativo registrato prima della chiamata; indice unico parziale su `ok`.
- Tick del worker serializzato con il lock di Procrastinate.
- Log di sicurezza in JSON senza dati personali; `X-Request-ID` generato dal server.
- Storico AI e voto riservati agli operatori (`richiede_ruolo("operatore")`).
- 1997 test su PostgreSQL reale; `test_confini.py` per gli import tra moduli.

## 4. Fase 1 · Conformità alle specifiche

### 4.1 Ricostruzione da zero

Su una cartella pulita (meglio un container senza nulla di preinstallato) si fanno:
1. clone e `allinea.py`;
2. migrazioni da database vuoto, seed, test e build;
3. il percorso della demo (converge §4).

Si cronometra e si annota ogni passo che richiede una conoscenza non scritta: ogni annotazione è un rilievo.

### 4.2 Matrice di tracciabilità

Uno script legge gli R-xx e i CA-xx di `spec.md` e i nomi dei test, e produce la tabella requisito → CA → test. Cerca tre cose:
- CA senza test, o con un test che non verifica ciò che il CA dice (controllo a campione);
- test senza CA;
- requisiti del perimetro senza CA, compresi quelli nuovi della corsia 9 (R-41…R-50).

### 4.3 Gli invarianti attaccati, uno per uno

| Invariante | Attacco da provare |
|---|---|
| §1.1 | Approvare con un post `da_rivedere`; pubblicare un post non approvato forzando lo stato; approvare due volte in parallelo (R-03). |
| §1.2 | Le 4 DELETE (`/foto/{id}`, gruppi, archivio): solo in bozza, mai su foto già usate in una versione. Cercare `db.delete` e `DELETE` su tabelle con storico. |
| §1.3 | Dopo sistemazione, ritaglio sul soggetto, proporzioni vere, pubblicazione e Cambia foto, l'hash del file originale resta identico. |
| §1.4 | Cambiare il profilo dopo l'invio, poi Rigenera testo e Rigenera immagine: si usa ancora `profilo_snapshot`. |
| §1.5 | Intervento a 15:01 e a 14:59 dall'uscita; nei giorni del cambio d'ora (28/03/2027, 31/10/2027); su campagna `sospesa`; nessuna AI dopo l'approvazione, compresa Rigenera immagine. |
| §1.6 | Modifica a mano con un blocco del validatore: non si salva. Testo generato con istruzioni ostili (§5.4). |
| §1.7 | Worker ucciso dopo la risposta di Meta e prima del commit; riprogramma dopo un `ok`; due worker sullo stesso database. |
| §1.8 | Assegnazioni a `.stato` fuori da `cambia_stato()` e da `contenuti.service`, cercate con `ast` in `test_confini.py`. |
| §1.9 | Cambia foto (da gruppo, campagna, archivio) e Sposta combinati per far uscire due volte la stessa foto sullo stesso canale. |
| §1.10 | Campagne con 0 foto, 1 foto, più foto che post, campagne sovrapposte: il numero esatto di post per canale. |
| §1.11 | Ogni azione di revisione e ogni intervento: il numero dei post non cala, se non nei casi ammessi. |

### 4.4 Architettura e contratti

- **Confini:** `test_confini.py` verde, più una ricerca di logica nei router, di `commit` nei service e di `relationship()` tra moduli.
- **Contratto backend ↔ frontend:** tipi TypeScript generati dallo schema OpenAPI e confrontati con `src/api/*.ts`. Le differenze diventano rilievi.
- **Pagine statiche ↔ app:** per ogni pagina di `docs/pagine/`, uno screenshot affiancato della schermata reale.

## 5. Fase 2 · Sicurezza

### 5.1 Che cosa si può e non si può simulare

| Cosa | Nella simulazione |
|---|---|
| **OWASP ASVS 5.0, livello 2** | Sì: checklist compilata con una prova per requisito (T4-107) |
| **Penetration test** | Solo interno, fatto dagli agenti con ZAP e verifiche a mano. Il rapporto dice in chiaro che non è una verifica indipendente. |
| **Conformità GDPR e AI Act** | Solo analisi delle lacune; nessuna firma del titolare e nessun consulente |
| **ISO/IEC 27001, SOC 2** | No: riguardano l'organizzazione, non il codice |

Riferimento per le API: **OWASP API Security Top 10 (2023)**. Il primo rischio, BOLA, è il principale di AdFlow: un artigiano che legge i dati di un altro.

### 5.2 Modello delle minacce

Flusso dei dati con i confini di fiducia e analisi STRIDE per ognuno.

| Confine | Rischi specifici |
|---|---|
| Browser → API | Furto della sessione; CSRF (R-02); clickjacking (R-01); id cambiati nelle richieste |
| Artigiano ↔ operatore | Aumento dei privilegi; letture trasversali tramite `/archivio-foto`, `/calendario?dal=`, `/campagne?artigiano=`, `/post/{id}/foto-possibili`, Cambia foto da archivio (R-17) |
| Upload → disco | File poliglotti, bombe di decompressione, EXIF enormi, nomi di file costruiti ad arte, disco pieno |
| Internet → `/foto/{id}/pubblica` | Firma indovinata o riusata, enumerazione degli id, differenze di tempo |
| Profilo e foto → LLM | Prompt injection dal profilo o da testo dentro una foto |
| LLM → database e storico AI | Risposte malformate o enormi; contenuti che passano il validatore; dati personali conservati nello storico (R-16) |
| Backend → Meta | Fuga del token; pagina sbagliata; limiti di Meta |
| Worker ↔ database | Job ripetuti o a metà; accodamenti doppi; stato incoerente dopo un guasto |
| Segreti e log | `.env` leggibile; dati personali o token in stderr |

### 5.3 Controlli automatici

In locale, con i report salvati (domanda 3 per la CI).

| Controllo | Strumento | Soglia per il rilievo |
|---|---|---|
| Dipendenze Python | `pip-audit` | Ogni vulnerabilità alta o critica è un rilievo |
| Dipendenze frontend | `npm audit --omit=dev` o `osv-scanner` | Come sopra |
| Analisi statica | `bandit`; `semgrep` con `p/python`, `p/owasp-top-ten`, `p/typescript`, `p/react` | Ogni risultato alto non giustificato |
| Segreti in git | `gitleaks` su tutta la storia | Zero; un segreto valido è un blocco assoluto |
| Tipi Python | `mypy` su `domain.py` e `service.py` | Report degli errori, senza correzioni |
| Componenti e licenze | `cyclonedx-py`, `pip-licenses` | Licenze incompatibili |
| Scansione dinamica | ZAP baseline, poi autenticata con i due ruoli | Ogni risultato alto |

### 5.4 Verifiche a mano mirate

1. **Matrice dei permessi esaustiva.** Ogni operazione dello schema OpenAPI (57) × {anonimo, artigiano A, artigiano B, operatore, admin}, con l'esito atteso 200, 401, 403 o 404 (costituzione §3). È un test parametrizzato che legge lo schema, quindi un'operazione senza riga fa fallire il test.
2. **Sessione.** Da provare:
   - sessione fissata prima del login;
   - logout che invalida tutte le schede;
   - scadenza per inattività (R-29) con l'orologio iniettato.
3. **CSRF.** Richieste con `Origin` di un altro dominio e di un sottodominio sulle 36 operazioni che cambiano stato. L'esito atteso oggi è che passino, e il rilievo dice che manca la seconda difesa.
4. **Upload.** File da provare: poliglotti JPEG+HTML, PNG da 1×100 000 pixel, file troncati, EXIF da 1 MB, HEIC rinominato JPEG. Poi due verifiche: la copia sistemata e ritagliata non ha più il GPS; le dimensioni in pixel sono controllate già al caricamento (costituzione §3).
5. **Indirizzo pubblico delle foto.** Firma scaduta, alterata, presa da un'altra foto, tagliata, con l'id cambiato: sempre 404, con tempi indistinguibili.
6. **Prompt injection.** Casi da provare:
   - un profilo con istruzioni ostili;
   - nomi di prodotti con caratteri di controllo;
   - un «testo di partenza» ostile in Rigenera testo.

   Si verifica che il validatore (§1.6) e l'approvazione umana (§1.1) fermino ogni uscita non voluta, e che **nessun percorso salti l'approvazione**.
7. **Log.** Traffico con email, password e token riconoscibili, poi ricerca in stderr e nello storico AI: zero occorrenze dei segreti.
8. **Segreti e server.** Da verificare:
   - permessi di `.env`;
   - `--forwarded-allow-ips` mai a `*`;
   - rotazione di `login_limite_segreto` a pubblicazioni ferme (R-13).

### 5.5 Dati personali e AI

È un'analisi delle lacune. Ogni lacuna è un rilievo con classe `roadmap` o `correggere`.

- **Registro dei trattamenti** (GDPR art. 30): quali dati, a che scopo, per quanto tempo. Va compreso lo storico AI (R-16).
- **«Niente si cancella» contro il diritto alla cancellazione** (art. 17): proposta di conciliazione, per esempio anonimizzare.
- **Fornitori**: OpenAI/OpenRouter e Meta ricevono dati. Servono DPA (art. 28), verifica dei trasferimenti fuori dall'UE (capo V) e informativa.
- **DPIA** (art. 35): serve?
- **AI Act, art. 50** (in vigore dal 2/8/2026): basta la dicitura delle immagini AI, o serve un'etichetta nei metadati?

## 6. Fase 3 · Qualità in tutte le parti

| Parte | Che cosa | Strumento | Soglia per il rilievo |
|---|---|---|---|
| Backend | Copertura dei **rami** | `pytest-cov --cov-branch` | Sotto l'85 % su `service.py` e `domain.py`; sotto il 100 % su transizioni e `interventi_ammessi()` |
| Qualità dei test | I test si accorgono degli errori? | `mutmut` su `domain.py`, `interventi.py`, `validatore.py`, `foto_pubblica.py` | Ogni mutante sopravvissuto analizzato |
| Macchine a stati | Sequenze casuali non violano gli invarianti | `hypothesis`, `RuleBasedStateMachine` su campagna e post | Ogni controesempio su 10 000 sequenze |
| API | Input generati dallo schema | `schemathesis` autenticato con i due ruoli | Ogni 500 e ogni risposta fuori schema |
| Frontend | Logica delle pagine | `vitest` e Testing Library | Flussi critici senza test |
| End-to-end | Percorso della demo a due ruoli, da database vuoto | Playwright | Ogni passo che fallisce |
| Accessibilità | Contrasto, tastiera, etichette, focus | `@axe-core/playwright` | Violazioni gravi o critiche (WCAG 2.2 AA) |
| Contratto API | Tipi TS uguali allo schema | `openapi-typescript` | Ogni differenza |
| Migrazioni | Vuoto → head; head → una indietro → head (compresa la 013) | Alembic | Errori o dati persi |
| Backup | Database **e** archivio foto (R-11) | `pg_dump`/`pg_restore` e copia dei file | Ripristino non riuscito o non misurato |
| Documentazione operativa | Chi non l'ha scritta riesce a seguirla? | Prova «a mani nuove» fatta da un agente senza contesto | Ogni passo non scritto |

## 7. Fase 4 · Stress, concorrenza e guasti

### 7.1 Prima: obiettivi scritti

Numeri a 12 mesi (D-01), ipotizzati e dichiarati come tali se non arrivano da Giovanni: consorzi, artigiani, operatori, campagne al mese, post al giorno, foto per campagna. Obiettivi di servizio di partenza:
- p95 sotto i 300 ms per le letture e sotto 1 s per le scritture;
- errori sotto lo 0,1 %;
- ritardo di pubblicazione sotto i 2 minuti.

### 7.2 Carico

Sui processi locali o sul compose (domanda 4), su un database dedicato, mai su `adflow` o `adflow_test`.

| Prova | Come | Che cosa si guarda |
|---|---|---|
| Carico normale | Il carico ipotizzato per 30 minuti, con utenti misti | p50, p95, p99 per endpoint; errori; connessioni al database |
| Picco | 10 volte il carico per 2 minuti | 503 ordinati invece di 500 |
| Durata | 2–8 ore | Memoria; connessioni; crescita di `limite_login`, `chiamata_ai`, `valutazione_ai` e delle tabelle di Procrastinate |
| Upload | 50 caricamenti paralleli da 10 MB | Memoria di Pillow; 413 oltre i 12 MB; disco |
| Worker | 1000 post nello stesso minuto, con Meta finto lento | Tempo di smaltimento |
| Storico AI | Elenco e numeri con 100 000 chiamate | Tempi della pagina degli operatori |

Strumento: `locust`. I dati si creano con le `fabbrica.py` dei moduli.

### 7.3 Concorrenza

Pytest con un `ThreadPoolExecutor` e una `threading.Barrier`, una connessione a PostgreSQL per richiesta.

- Due operatori approvano la stessa campagna (R-03): atteso un solo esito, l'altro 409.
- Approva e respingi in parallelo; approva e richiesta all'artigiano in parallelo.
- Quattro Rigenera testo dello stesso post in parallelo, con il limite a 3 (R-04); lo stesso per Rigenera immagine.
- Cambia foto su due post della stessa campagna con la stessa foto (§1.9).
- Annulla o sposta un post mentre il tick lo pubblica.
- Invio della stessa campagna da due schede.
- Due campagne sovrapposte della stessa bottega inviate insieme: orari occupati rispettati.
- Voto sulla stessa chiamata AI da due operatori.
- 20 accessi paralleli sullo stesso account: il limite resta 5.

Se un test fallisce si scrive il rilievo, con la correzione tipica proposta: `with_for_update`, un vincolo unico o un `UPDATE … WHERE stato = …`.

### 7.4 Guasti provocati

Con `monkeypatch` sugli adattatori finti dentro i test, senza modificare l'app. `toxiproxy` solo se c'è il compose.

| Guasto | Comportamento atteso |
|---|---|
| PostgreSQL fermo per 30 s | 503 senza dati incoerenti; il worker riparte |
| AI: timeout, 429, JSON malformato, vuota, lunghissima | Uno dei cinque tipi d'errore; nessuna campagna bloccata a metà; chiamata registrata nello storico anche se fallisce |
| Meta: 5xx, 190, 368, 4/17/32/613, contenitore in errore | Nessun doppio post (§1.7); riprova fino a `TENTATIVI_MAX`; poi `fallito`, riprogrammabile |
| Timeout **dopo** che Meta ha pubblicato | Il caso più insidioso (D-07): oggi che cosa succede? |
| Worker ucciso durante una pubblicazione | Il tentativo `in_corso` si riusa; nessun doppio `ok` |
| Disco pieno durante un upload | Errore chiaro; nessun file a metà; originale intatto |
| Email non consegnabile | Il flusso principale non si blocca |
| Orologio: cambio d'ora 28/03/2027, fine anno, 29/02/2028 | Slot e scadenze in Europe/Rome giusti |

### 7.5 Osservabilità

Che cosa si vede oggi di latenza, coda di Procrastinate, ritardo di pubblicazione, costo AI (storico AI) ed eventi di `adflow.sicurezza`? Ogni misura che manca è un rilievo.

## 8. Fase 5 · Criteri di giudizio

Alla fine (T4-108) ogni casella prende un esito: **soddisfatto**, **non soddisfatto** (con i rilievi) o **non provato** (con il motivo).

**Prodotto**
- [ ] Ogni CA del perimetro tracciato e verde
- [ ] Gli 11 invarianti con test che provano a violarli
- [ ] Test con stato senza controesempi
- [ ] Demo da database vuoto automatica

**Sicurezza**
- [ ] Matrice dei permessi esaustiva
- [ ] Dipendenze, analisi statica, segreti e ZAP senza risultati alti
- [ ] Header di sicurezza e controllo di `Origin`
- [ ] Issue #17 verificata su un proxy di staging
- [ ] Checklist ASVS 5.0 L2 compilata
- [ ] Lacune GDPR e AI Act elencate, con una proposta per ognuna

**Affidabilità**
- [ ] Obiettivi di servizio (ipotizzati) rispettati
- [ ] Prova di durata senza perdite
- [ ] Scenari di concorrenza e guasto con l'esito atteso
- [ ] Backup e ripristino di database e foto provati
- [ ] Misure e allarmi su sicurezza, coda e spesa AI

**Processo**
- [ ] Dipendenze bloccate; runtime e test separati
- [ ] Rilascio riproducibile e rollback descritti
- [ ] Documentazione seguita da chi non l'ha scritta

**Blocchi assoluti.** Se uno di questi è confermato, il rilievo è Alto e la sintesi lo mette in cima:
- un artigiano vede o modifica i dati di un altro artigiano;
- un post viene pubblicato senza approvazione;
- lo stesso post viene pubblicato due volte su Meta;
- un segreto valido è nella storia di git;
- la foto originale di un artigiano viene modificata o persa;
- dati personali o token compaiono nei log.

## 9. Piano della simulazione

Nove task in sequenza, uno alla volta, eseguiti da agenti. Le stime sono in sessioni di lavoro e indicative.

| Task | Che cosa | Copre | Stima |
|---|---|---|---|
| T4-100 | Preparazione: ADR-120, brief, corsia 10 in `tasks.md`, `allinea.py` con la corsia 10, registro dei rilievi vuoto | — | 1 |
| T4-101 | Linea di base: ricostruzione da zero, scansioni, dipendenze, copertura dei rami, tracciabilità | §4.1, §4.2, §5.3, §6 (copertura); R-05, R-06, R-07 | 1–2 |
| T4-102 | Permessi e superficie HTTP: matrice 57 × 5, header, origine, upload, foto pubblica, BOLA sui nuovi endpoint, limite delle azioni AI | §5.4 punti 1–5; R-01, R-02, R-12, R-15, R-16, R-17 | 2 |
| T4-103 | Concorrenza: gli scenari di §7.3 | §7.3; R-03, R-04 | 1–2 |
| T4-104 | Invarianti e proprietà: attacchi di §4.3, macchine a stati, fuzzing dallo schema, mutazioni | §4.3, §6 | 2 |
| T4-105 | Esercizio, guasti e carico: guasti di §7.4, carico di §7.2, backup e ripristino, osservabilità | §6 (backup), §7.1, §7.2, §7.4, §7.5; R-09, R-10, R-11, R-15 | 2 |
| T4-106 | Frontend: percorso della demo in Playwright a due ruoli, accessibilità, contratto dei tipi | §4.4, §6; R-08 | 2 |
| T4-107 | Analisi a tavolino: minacce STRIDE, prompt injection, log, dati personali e AI Act, ASVS L2 | §5.1, §5.2, §5.4 punti 6–8, §5.5; R-13, R-14, R-16 | 2 |
| T4-108 | Sintesi: criteri di §8 valutati, rilievi classificati, task di correzione proposti, limiti dell'MVP, nuova versione di questa proposta | §8 | 1 |

I 17 pacchetti della prima versione (PA-01…PA-17) sono confluiti qui: le correzioni e le infrastrutture (lockfile, CI bloccante, middleware, container, staging) non sono più nei task. Diventano proposte nel registro.

## 10. Ipotesi e decisioni aperte

| ID | Decisione | Nella simulazione |
|---|---|---|
| D-01 | Numeri attesi a 12 mesi e obiettivi di servizio | Domanda 5 |
| D-02 | Hosting | Domanda 4 |
| D-03 | Referente per la sicurezza e per la privacy | Giovanni, per la simulazione |
| D-04 | Budget per pentest e consulente | Nessuno: si simula (§5.1) |
| D-05 | Cancellazione e conservazione rispetto a §1.2, compreso lo storico AI | Proposta in T4-107, decisione dopo |
| D-06 | Rotte congelate `/api/archivio…` | Domanda 8 |
| D-07 | Timeout di Meta dopo la pubblicazione | Comportamento attuale osservato in T4-105, decisione dopo |

## 11. Appendice

### Comandi di partenza

Dalla radice; non cambiano il codice.

```bash
# Dipendenze Python
uvx pip-audit -r backend/requirements.txt

# Analisi statica del backend (media e alta)
uvx bandit -r backend/app -ll

# Regole semgrep
uvx semgrep scan --config p/python --config p/owasp-top-ten --config p/react backend/app frontend/src

# Segreti in tutta la storia (gitleaks 8.19 o successivo)
gitleaks git --log-opts="--all" .

# Dipendenze del frontend
npm --prefix frontend audit --omit=dev

# Copertura dei rami (da backend/)
uv run --with pytest-cov pytest --cov=app --cov-branch --cov-report=term-missing

# Operazioni dello schema (da backend/)
uv run python -c "from app.main import app; print(sum(len([m for m in o if m in ('get','post','put','patch','delete')]) for o in app.openapi()['paths'].values()))"

# Fuzzing dallo schema (API avviata in locale)
uvx schemathesis run http://localhost:8000/openapi.json --header "Cookie: adflow_sessione=<token di prova>"
```

### Riferimenti

- OWASP ASVS 5.0; OWASP API Security Top 10 (2023).
- GDPR, artt. 17, 28, 30, 35 e capo V; AI Act, art. 50.
- `docs/agenti/constitution.md`, `perimetro-mvp.md`, `spec.md`, `converge.md`, `docs/sicurezza-accesso.md`, `qa/issue-17/`, `docs/ROADMAP.md`.

### Glossario

| Termine | Significato |
|---|---|
| **BOLA / IDOR** | Accesso a un oggetto di un altro utente cambiando l'identificativo nella richiesta. |
| **CSRF** | Un altro sito fa partire una richiesta dal browser dell'utente, con il suo cookie. |
| **CSP, HSTS** | Header che dicono al browser da dove caricare risorse e di usare sempre HTTPS. |
| **SBOM** | Elenco dei componenti di un rilascio, con versioni e licenze. |
| **Test di mutazione** | Si introducono piccoli errori nel codice: se i test passano lo stesso, non controllano abbastanza. |
| **Test con stato** | Lo strumento genera sequenze casuali di azioni e controlla gli invarianti dopo ognuna. |
| **xfail strict** | Test che documenta un difetto: deve fallire; se un giorno passa, pytest lo segnala. |
| **RPO / RTO** | Quanti dati si possono perdere al massimo, e in quanto tempo si torna in servizio. |
| **STRIDE** | Falsificazione, manomissione, ripudio, fuga di informazioni, negazione del servizio, aumento dei privilegi. |

## 12. Corsia 10

*Da generare con le risposte alle nove domande:*
- *12.1, il blocco per `docs/agenti/tasks.md`;*
- *12.2, la riga ADR-120;*
- *12.3, il brief `docs/agenti/brief-accettazione.md`, con file da toccare, file da non toccare e «Fatto quando» di ogni task.*

**Nota per T4-100.** `allinea.py` accetta una sola cifra (`"0123456789"`, `allinea.py:378`): la corsia 10 richiede di accettare due cifre e di aggiornare `backend/tests/test_allinea.py`. È un file comune, quindi lo rivede il referente.

---

*Documento preliminare, da valutare. Prima versione del 24/10/2026 su `6a8e2ed`; riscritto il 30/10/2026 come simulazione su `main` a `8c01e2b`, senza modifiche al codice.*
