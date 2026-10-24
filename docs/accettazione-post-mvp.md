# Accettazione, sicurezza e affidabilità dopo l'MVP

> **⚠️ DOCUMENTO PRELIMINARE, DA VALUTARE.**
> È una bozza di proposta, non è approvata e non fa testo. Non cambia il perimetro dell'MVP, i task di `docs/agenti/tasks.md` né le regole di `docs/agenti/`: dove qualcosa non torna valgono quei documenti. Nessun punto va eseguito finché il team non l'ha discusso e trasformato in task con il loro brief. Stime, ordine e priorità sono indicativi.

**Stato:** bozza da discutere · **Data:** 24/10/2026 · **Base:** `main` a `6a8e2ed` · **Vale da:** dopo la consegna del 6/11

Che cosa controllare, con quali strumenti e con quali soglie prima di autorizzare lo sviluppo completo, più un piano d'azione da dettagliare nei prossimi task. I riferimenti a file e righe valgono per il commit `6a8e2ed`.

## Come si procede

Questo documento si usa in due passi, prima di leggere il resto.

1. **Domande.** Chi lo apre risponde alle nove domande qui sotto. Un agente le fa alla persona **una alla volta**, propone la risposta predefinita e non decide al posto suo; se una risposta manca si ferma e chiede, come vuole `AGENTS.md`.
2. **Corsia.** Con le risposte si genera la **corsia 9** dello sprint 4, task da T4-90 a T4-99: la tabella per `docs/agenti/tasks.md`, il brief `docs/agenti/brief-accettazione.md` e la riga ADR-119. La [pagina interattiva](https://claude.ai/artifact/8zNobVKA66gNF2TeE9reRY) (si apre solo se è stata condivisa con te) fa le domande appena la apri e genera tutto da sola. Senza la pagina si parte dalla corsia del [§12](#12-corsia-9-con-le-risposte-predefinite), generata con le risposte predefinite, e si applica la colonna «Che cosa cambia».
3. **Nulla va su `main` finché il documento è una bozza.** La corsia entra nel repository con il task T4-90, dopo l'approvazione del team.

**Perché la corsia 9.** La corsia 8 è già proposta per l'interfaccia (branch `feature/proposta-corsia-8-interfaccia`, sprint 3, ADR-118). Se quella proposta non passa, questa può diventare la 8: si rinumerano i task e gli ADR.

### Le nove domande

| # | Domanda | Risposte possibili (in grassetto la predefinita) | Che cosa cambia |
|---|---|---|---|
| 1 | Quanto del piano volete fare? | **Tutto il piano**; L'essenziale per la produzione | Con l'essenziale T4-95 e T4-96 perdono copertura, mutazioni, test dei componenti e contratto dei tipi. |
| 2 | Chi lavora alla corsia 9? | **Giovanni**; **Gianluca**; **Silvia**; **Nilton**; **Angelo** (più di una) | Cambia il «Chi» di ogni task e l'intestazione della corsia. |
| 3 | Quanto tempo a settimana dà ogni persona alla corsia? | Tempo pieno; **Metà tempo**; Un giorno a settimana | Cambia le date di ogni task e la fine della corsia. |
| 4 | Da quando si parte? | una data; **lunedì 9/11/2026** | Sposta tutte le date. |
| 5 | L'hosting è già deciso? | Sì, è deciso; **Non ancora**; Per ora solo in locale | Cambia T4-97, T4-98 e T4-99; con «Non ancora» resta aperta la decisione D-02. |
| 6 | C'è budget per verifiche esterne? | Pentest e consulente privacy; **Solo il consulente privacy**; Nessuno per ora | Cambia T4-93 e T4-99, e quanto durano. |
| 7 | Conoscete i numeri attesi di utilizzo? | Sì, li conosciamo; **Da definire con il cliente** | Cambia il «Fatto quando» di T4-98. |
| 8 | La doppia approvazione (R-03): quando la verifichiamo? | **Subito, prima della consegna**; Nel piano, in T4-94 | Con «Subito» compare un passo fuori dalla corsia, prima del 6/11. |
| 9 | Le rotte congelate /api/archivio… restano esposte? | **Restano montate**; Toglierle dalla composizione | Cambia T4-92 e la riga dell'ADR-119. |

## Indice

- [Come si procede](#come-si-procede)

0. [Sintesi](#0-sintesi)
1. [Metodo](#1-metodo)
2. [Correzioni rispetto alla prima versione](#2-correzioni-rispetto-alla-prima-versione)
3. [Stato verificato oggi](#3-stato-verificato-oggi)
4. [Fase 1 · Conformità alle specifiche](#4-fase-1--conformità-alle-specifiche)
5. [Fase 2 · Sicurezza](#5-fase-2--sicurezza)
6. [Fase 3 · Qualità in tutte le parti](#6-fase-3--qualità-in-tutte-le-parti)
7. [Fase 4 · Stress, concorrenza e guasti](#7-fase-4--stress-concorrenza-e-guasti)
8. [Fase 5 · Criteri di accettazione](#8-fase-5--criteri-di-accettazione)
9. [Piano d'azione](#9-piano-dazione)
10. [Decisioni aperte](#10-decisioni-aperte)
11. [Appendice](#11-appendice)
12. [Corsia 9 con le risposte predefinite](#12-corsia-9-con-le-risposte-predefinite)

---

## 0. Sintesi

L'MVP ha basi solide: 1070 test su PostgreSQL vero, confini tra moduli controllati da un test, password con scrypt, token di sessione salvati solo come hash, firme confrontate a tempo costante, upload controllati sui byte reali. Per l'MVP e la demo va bene così.

Per autorizzare lo sviluppo completo mancano ancora cinque cose:

- **la prova che il sistema regge in produzione**: rilascio, proxy, header, issue #17;
- **la prova che regge la concorrenza**: per esempio due approvazioni nello stesso istante;
- **controlli di sicurezza automatici in CI**;
- **test del frontend**;
- **decisioni su GDPR e AI Act**.

Il piano proposto ha 17 pacchetti di lavoro su circa 6 settimane, dal 9/11 al 18/12, per un totale indicativo di 55 persona-giorni più due interventi esterni (consulente privacy e pentest). Alla fine c'è una decisione esplicita, con criteri scritti in anticipo: si va avanti o no.

**Due cose da guardare prima del blocco del 30/10**, senza aspettare questo piano:

- **Cambio d'ora domenica 25/10/2026**: Europe/Rome passa da +02:00 a +01:00. Slot dei post e scadenze sono in ora di Roma, quindi conviene un test sugli slot tra il 24 e il 26/10 con l'orologio iniettato (`core/orologio.py`). La demo si svolge dopo il cambio.
- **Doppia approvazione** ([R-03](#3-stato-verificato-oggi)): se un test con due richieste parallele la conferma, la correzione è piccola e rientra tra quelle ammesse dal 2 al 6/11.

## 1. Metodo

Il criterio è uno solo: **si accetta ciò che si può dimostrare di nuovo**. Ogni affermazione ("è sicuro", "regge il carico", "rispetta la specifica") deve portare con sé un comando, un report o un artefatto che chiunque del team può rifare. "Sulla mia macchina funziona" e "i test passano" non bastano da soli.

Il lavoro è diviso in cinque fasi. Ognuna ha una **soglia di uscita**: finché non è raggiunta non si passa alla fase dopo, oppure si scrive perché si fa un'eccezione e chi la firma.

| Fase | Domanda | Prova che chiude la fase |
|---|---|---|
| F1 | Il software fa ciò che dice la specifica? | Matrice requisiti → CA → test completa; invarianti attaccati da test |
| F2 | È sicuro quanto serve a un'app con dati personali e token di terzi? | Checklist ASVS 5.0 livello 2, scansioni in CI pulite, pentest con correzioni |
| F3 | Ogni parte (backend, frontend, migrazioni, build) è verificata? | Copertura dei rami, test di mutazione, E2E, contratto API, build riproducibile |
| F4 | Come si comporta sotto carico, in concorrenza e con i guasti? | Report di carico, durata e guasti, con obiettivi scritti prima |
| F5 | Si autorizza lo sviluppo completo? | Tutte le caselle dei criteri spuntate, o eccezioni firmate |

Gravità usata nel documento:
- **Alta**: blocca la produzione.
- **Media**: va risolta prima dello sviluppo completo.
- **Bassa**: si pianifica.
- **Da verificare**: ipotesi fondata sul codice, da confermare con un test prima di correggere.

## 2. Correzioni rispetto alla prima versione

Le raccomandazioni date in chat sono state ricontrollate sul codice. Quattro erano imprecise e sono corrette qui; sei punti sono nuovi.

| Prima | Ora |
|---|---|
| `httpx2` dichiarato in `requirements.txt` ma mai usato. | `httpx2` serve: lo usa il `TestClient` di Starlette (`import httpx2 as httpx`). Il problema vero è l'opposto: `adapters/social/meta.py` importa `httpx`, che non è dichiarato e arriva solo tramite litellm e openai. |
| 33 endpoint che cambiano stato. | Lo schema OpenAPI ne conta **52** in tutto, di cui **34** cambiano stato: 27 POST, 2 PUT, 1 PATCH, 4 DELETE. |
| Verificare che il token Meta sia cifrato nel database. | Nell'MVP il token della pagina di prova sta solo in `backend/.env` e nel codice non c'è cifratura. È coerente con il perimetro, perché il collegamento degli account è in roadmap. Per lo sviluppo completo la cifratura dei token degli artigiani va progettata prima di scrivere codice (R-14). |
| Il CSRF ha gravità media; due tick del worker possono pubblicare due volte. | Il CSRF scende a **bassa o media**: il cookie ha `SameSite=Lax` esplicito e nessun GET cambia stato. Il controllo di `Origin` resta come seconda difesa. Il tick è già serializzato con `lock` e `queueing_lock` di Procrastinate (`worker.py:31`), e un indice unico parziale garantisce al massimo un `ok` per post. Il rischio di concorrenza vero è altrove: approvazione e interventi. |

**Punti nuovi:**
- doppia approvazione possibile (R-03);
- dipendenze dei test installate anche in produzione (R-06);
- foto su disco locale, da includere nei backup (R-11);
- rotte congelate ancora esposte (R-12);
- obblighi di trasparenza dell'AI Act per le immagini generate (§5.5);
- nessun limite di frequenza sulle azioni che costano chiamate AI (R-15).

I permessi hanno già molti test per modulo: in 30 file di test compaiono 403 o `role_denied`. La matrice dei permessi resta tra le raccomandazioni, ma cambia lo scopo: renderla **esaustiva e generata dallo schema**, così un endpoint nuovo senza controllo fa fallire la CI.

## 3. Stato verificato oggi

Punti trovati leggendo `main`, senza modifiche. Ogni riga indica dove guardare.

| ID | Che cosa | Dove | Gravità | Pacchetto |
|---|---|---|---|---|
| R-01 | L'app non imposta header di sicurezza (CSP, HSTS, `X-Frame-Options` o `frame-ancestors`, `X-Content-Type-Options`, `Referrer-Policy`). Nemmeno l'esempio Nginx di `sicurezza-accesso.md` li aggiunge. | `app/main.py`; `docs/sicurezza-accesso.md` | Alta in prod. | PA-04 |
| R-02 | Nessun controllo di `Origin` o `Sec-Fetch-Site` sulle 34 operazioni che cambiano stato. Protegge solo `SameSite=Lax`, che non copre le richieste da sottodomini dello stesso sito. | `accesso/router.py:72-79` | Bassa/Media | PA-04 |
| R-03 | `revisione.approva()` legge la campagna senza bloccare la riga, controlla `in_revisione` e poi scrive. La tabella `Approvazione` non ha vincoli unici. Con due richieste parallele (doppio clic, due operatori) entrambe possono passare il controllo e registrare approvazioni e decisioni doppie. | `revisione/service.py:155-184`; `revisione/models.py` | Da verificare | PA-05 |
| R-04 | Il contatore delle rigenerazioni si incrementa in Python (`+= 1`) e i moduli `contenuti` e `revisione` non bloccano mai le righe. Il limite `MAX_RIGENERAZIONI = 3` e gli interventi in parallelo vanno provati con richieste concorrenti. | `contenuti/interventi.py:45,68,452` | Da verificare | PA-05 |
| R-05 | `httpx` è importato dal codice ma non dichiarato: un aggiornamento di litellm può cambiarne la versione senza che nessuno se ne accorga. | `adapters/social/meta.py:25` | Media | PA-01 |
| R-06 | Niente lockfile né hash: le dipendenze indirette non sono fissate. `pytest`, `httpx2`, `black`, `pre-commit` e `cryptography` (usata solo nei test) stanno nello stesso file del runtime e finirebbero in produzione. | `backend/requirements.txt` | Media | PA-01 |
| R-07 | La CI esegue test, black, lint e build. Mancano analisi delle dipendenze, analisi statica di sicurezza, ricerca dei segreti, controllo dei tipi Python, copertura ed E2E. | `.github/workflows/` | Media | PA-02 |
| R-08 | Il frontend non ha test: gli script sono `dev`, `build`, `lint` e `preview`. | `frontend/package.json` | Media | PA-07 |
| R-09 | Nel repository non c'è nulla per il rilascio: niente container, compose, configurazione completa del proxy o procedura di rollback. | radice del repo | Alta in prod. | PA-08 |
| R-10 | La issue #17 (TLS, cookie e proxy provati nell'ambiente reale) è ancora aperta. | `docs/sicurezza-accesso.md` | Alta in prod. | PA-08 |
| R-11 | Le foto stanno su disco locale (`ARCHIVIO_FOTO_DIR`, predefinito `./archivio_foto`). Un `pg_dump` da solo non basta come backup, e due istanze dell'API non vedono gli stessi file. | `core/config.py:43`; `adapters/archivio/disco.py` | Media in prod. | PA-12, PA-17 |
| R-12 | Le rotte congelate `/api/archivio…` (5 operazioni, tra cui 2 DELETE) restano montate ed esposte, anche se nessuno ci lavora. | `campagne/router.py`; `campagne/archivio.py` | Bassa | Decisione D-06 |
| R-13 | `LOGIN_LIMITE_SEGRETO` firma sia i contatori del login sia gli indirizzi pubblici delle foto. Le chiavi sono separate per dominio, quindi la crittografia va bene; ma cambiarlo invalida le foto di una pubblicazione in corso. | `core/limite_login.py`; `campagne/foto_pubblica.py` | Bassa | PA-08 |
| R-14 | La costituzione §3 chiede "permessi social cifrati". Nell'MVP non servono, ma con il collegamento degli account andranno cifrati i token di molti artigiani: servono gestione delle chiavi, rotazione e revoca. | `docs/agenti/constitution.md` §3 | Prerequisito | PA-17 |
| R-15 | Il limite di frequenza esiste solo sul login. Invio della campagna e rigenerazione fanno partire chiamate AI a pagamento: un account compromesso o un errore del frontend possono far crescere la spesa. C'è un tetto sul conto del provider (T3-32), ma non nell'applicazione. | `core/limite_login.py`; `contenuti/interventi.py` | Media | PA-09 |

### Punti di forza verificati

- Password con scrypt e salt da `secrets`.
- Token di sessione con `secrets.token_urlsafe(32)`; nel database solo l'hash.
- Firme confrontate con `hmac.compare_digest`.
- Cookie httpOnly, `SameSite=Lax`, Secure obbligatorio in produzione.
- Limite dei tentativi di accesso su PostgreSQL, per IP e per account.
- Upload: estensioni ammesse, magic bytes, 10 MB per file, 12 MB per richiesta.
- Percorsi dei file risolti dentro la radice dell'archivio.
- Foto sistemata senza EXIF e GPS, con un tetto di 36 milioni di pixel.
- Pubblicazione: tentativo registrato prima della chiamata; indice unico parziale su `ok`.
- Tick del worker serializzato con il lock di Procrastinate.
- Log di sicurezza in JSON senza dati personali; `X-Request-ID` generato dal server.
- Nessun `dangerouslySetInnerHTML` nel frontend.
- 1070 test su PostgreSQL reale; `test_confini.py` per gli import tra moduli.

## 4. Fase 1 · Conformità alle specifiche

Obiettivo: dimostrare che ciò che è stato consegnato coincide con ciò che era stato promesso in `spec.md`, `perimetro-mvp.md` e `constitution.md`.

### 4.1 Ricostruzione da zero

Su una macchina pulita, meglio un container senza nulla di preinstallato: clone, `allinea.py`, migrazioni da database vuoto, seed, test, build, percorso della demo (converge §4). Si cronometra e si annota ogni passo che richiede una conoscenza non scritta. Ogni annotazione diventa una riga di README o un task.

### 4.2 Matrice di tracciabilità

Uno script legge gli R-xx e i CA-xx di `spec.md` e i nomi dei test (`test_caNN_…`) e produce una tabella requisito → CA → test → pagina. Si cercano:

- CA senza test, o con un test che non verifica davvero ciò che il CA dice (lo si controlla a mano, a campione);
- test senza CA, cioè comportamenti nati fuori dalla specifica;
- requisiti del perimetro MVP senza CA.

### 4.3 Gli invarianti attaccati, uno per uno

Gli 11 invarianti di `constitution.md` §1 sono il cuore del prodotto. Per ognuno ci vuole almeno un test che **prova a violarlo**, non solo uno che lo osserva nel caso normale.

| Invariante | Attacco da provare |
|---|---|
| §1.1 | Approvare con un post `da_rivedere`; pubblicare un post non approvato forzando lo stato; approvare due volte in parallelo (R-03). |
| §1.2 | Le 4 DELETE (`/foto/{id}`, gruppi, archivio): verificare che agiscano solo in bozza e mai su foto già usate in una versione di post. Cercare `db.delete` e `DELETE` su tabelle con storico. |
| §1.3 | Dopo sistemazione, pubblicazione e cambia foto, l'hash del file originale resta identico. |
| §1.4 | Cambiare il profilo dopo l'invio e rigenerare: il testo usa ancora `profilo_snapshot`. |
| §1.5 | Intervento a 15:01 e a 14:59 dall'uscita; nei giorni del cambio d'ora (25/10/2026, 28/03/2027); su campagna `sospesa`; nessuna AI dopo l'approvazione. |
| §1.6 | Modifica a mano con un blocco del validatore: non si salva. Testo generato con istruzioni ostili (vedi §5.4). |
| §1.7 | Worker ucciso dopo la risposta di Meta e prima del commit; riprogramma dopo un `ok`; due worker sullo stesso database. |
| §1.8 | Ricerca automatica di assegnazioni a `.stato` fuori da `cambia_stato()` e da `contenuti.service`: si può aggiungere a `test_confini.py` con `ast`. |
| §1.9 | Cambia foto e sposta combinati per far uscire due volte la stessa foto sullo stesso canale. |
| §1.10 | Campagne con 0 foto, 1 foto, più foto che post; verificare il numero esatto di post per canale. |
| §1.11 | Ogni azione di revisione: il numero dei post non cala, se non nei tre casi ammessi. |

### 4.4 Architettura e contratti

- `test_confini.py` verde; in più una ricerca di logica nei router, di `commit` nei service e di `relationship()` tra moduli.
- **Contratto backend ↔ frontend**: generare i tipi TypeScript dallo schema OpenAPI (per esempio con `openapi-typescript`) e confrontarli in CI con quelli di `src/api/*.ts`. Oggi si allineano a mano (costituzione §4).
- **Pagine statiche ↔ app**: per ogni pagina di `docs/pagine/`, screenshot affiancato della schermata reale. Le differenze diventano task o note della roadmap.

> **Soglia di uscita F1.** Ogni CA del perimetro ha un test che lo verifica davvero; ogni invariante ha almeno un test che prova a violarlo; la ricostruzione da zero riesce seguendo solo i documenti.

## 5. Fase 2 · Sicurezza

### 5.1 Che cosa si può certificare

Un software, da solo, non si certifica "sicuro". Si possono ottenere quattro cose diverse, da non confondere quando se ne parla con il cliente:

| Cosa | Chi lo fa | Che cosa dimostra | Per noi |
|---|---|---|---|
| **Verifica OWASP ASVS 5.0, livello 2** | Il team, con prove per ogni requisito | Che i controlli di un'app web con dati personali ci sono e funzionano | Sì, è l'obiettivo principale |
| **Penetration test** | Una persona o una ditta esterna | Che un attaccante competente, in un tempo dato, non trova falle gravi | Sì, prima della produzione con clienti veri |
| **Conformità normativa** (GDPR, AI Act) | Il titolare del trattamento, con un consulente | Che il trattamento dei dati e l'uso dell'AI rispettano la legge | Sì, obbligatoria |
| **ISO/IEC 27001, SOC 2** | Un ente di certificazione | Che l'organizzazione gestisce la sicurezza con un sistema di processi | No: riguarda l'azienda che esercisce il servizio, non il codice |

Come riferimento per le API conviene usare anche l'**OWASP API Security Top 10 (2023)**. Il primo rischio della lista, l'accesso a oggetti di altri utenti (BOLA), è proprio il rischio principale di AdFlow: un artigiano che legge i dati di un altro.

### 5.2 Modello delle minacce

Prima di ogni prova si disegna il flusso dei dati con i confini di fiducia e per ognuno si applica STRIDE: falsificazione, manomissione, ripudio, fuga di informazioni, negazione del servizio, aumento dei privilegi.

| Confine | Rischi specifici del progetto |
|---|---|
| Browser → API | Furto della sessione; CSRF (R-02); clickjacking senza `frame-ancestors` (R-01); un artigiano che legge le risorse di un altro cambiando un id |
| Artigiano ↔ operatore | Aumento dei privilegi; letture trasversali tramite `/archivio-foto`, `/calendario?dal=`, `/campagne?artigiano=`, `/post/{id}/foto-possibili` |
| Upload → disco | File poliglotti, bombe di decompressione, EXIF enormi, nomi di file costruiti ad arte, disco pieno |
| Internet → `/foto/{id}/pubblica` | Endpoint pubblico per Instagram: firma indovinata o riusata, enumerazione degli id, differenze di tempo di risposta |
| Profilo e foto → LLM | **Prompt injection**: istruzioni nel profilo o testo dentro una foto fanno scrivere all'AI contenuti non voluti, che poi possono arrivare su Meta |
| LLM → database | Risposte malformate o troppo lunghe; contenuti che passano il validatore ma non andrebbero pubblicati |
| Backend → Meta | Fuga del token; pubblicazione sulla pagina sbagliata; limiti di Meta superati |
| Worker ↔ database | Job ripetuti o a metà; accodamenti doppi; stato incoerente dopo un guasto |
| Segreti e log | `.env` leggibile da altri utenti; dati personali o token finiti in stderr |

### 5.3 Controlli automatici in CI

| Controllo | Strumento | Soglia | Quando |
|---|---|---|---|
| Vulnerabilità note nelle dipendenze Python | `pip-audit` | Nessuna alta o critica senza eccezione scritta | A ogni PR e ogni notte |
| Vulnerabilità note nelle dipendenze frontend | `npm audit --omit=dev` oppure `osv-scanner` | Come sopra | A ogni PR e ogni notte |
| Analisi statica di sicurezza | `bandit` sul backend; `semgrep` con `p/python`, `p/owasp-top-ten`, `p/typescript`, `p/react` | Nessun risultato alto non giustificato | A ogni PR |
| Segreti in git | `gitleaks` | Zero; un segreto trovato si considera compromesso e si cambia | Una volta su tutta la storia, poi a ogni PR |
| Tipi Python | `mypy`, prima su `domain.py` e `service.py` | Nessun errore nuovo | A ogni PR |
| Componenti e licenze | `cyclonedx-py`, `@cyclonedx/cyclonedx-npm`, `pip-licenses` | SBOM salvato; nessuna licenza incompatibile | A ogni rilascio |
| Aggiornamenti delle dipendenze | Dependabot o Renovate | PR settimanali, unite solo con la CI verde | Ogni settimana |
| Scansione dinamica | ZAP, baseline e poi scansione completa autenticata con i due ruoli | Nessun risultato alto | Sullo staging, ogni settimana |

### 5.4 Verifiche a mano mirate

1. **Matrice dei permessi esaustiva.** Ogni operazione dello schema OpenAPI (52) × {anonimo, artigiano A, artigiano B, operatore, admin}, con l'esito atteso 200, 401, 403 o 404 (costituzione §3). Diventa un test parametrizzato che legge lo schema: un endpoint nuovo senza una riga nella matrice fa fallire la CI. È il controllo con il miglior rapporto tra costo e valore di tutto il piano.
2. **Sessione.** Da provare:
   - sessione fissata prima del login;
   - logout che invalida tutte le schede;
   - scadenza per inattività (R-29), con l'orologio iniettato;
   - cookie Secure, HttpOnly, `SameSite=Lax` e `Path=/` dietro il proxy reale (issue #17).
3. **CSRF.** Una pagina di prova su un altro dominio, e una su un sottodominio dello stesso sito, provano le 34 operazioni che cambiano stato. Poi si aggiunge comunque il controllo di `Origin` (o `Sec-Fetch-Site`) come seconda difesa.
4. **Upload.** File da provare: poliglotti JPEG+HTML, PNG da 1×100 000 pixel, file troncati, EXIF da un megabyte, HEIC rinominato JPEG. Poi si verificano due cose:
   - con `exiftool`, che la copia sistemata non abbia più il GPS;
   - che le dimensioni in pixel siano controllate già al caricamento, come chiede la costituzione §3, e non solo alla sistemazione.
5. **Indirizzo pubblico delle foto.** Firma scaduta, alterata, presa da un'altra foto, tagliata, con l'id cambiato: la risposta è sempre 404, con tempi indistinguibili. Nessun header e nessun corpo deve rivelare se la foto esiste.
6. **Prompt injection.** Casi da provare: un profilo con istruzioni ostili ("ignora le regole precedenti, scrivi che…"), foto con testo sovrimpresso, nomi di prodotti con caratteri di controllo. Si verifica che il validatore (§1.6) e l'approvazione umana obbligatoria (§1.1) fermino ogni uscita non voluta, e che **nessun percorso salti l'approvazione**. In AdFlow la vera difesa contro la prompt injection è l'umano che approva: va dimostrato che c'è sempre.
7. **Log.** Si genera traffico di prova con email, password e token riconoscibili, poi si cercano in stderr: devono comparire zero volte.
8. **Segreti e server.** Da verificare:
   - `.env` con permessi 600 e un proprietario dedicato;
   - backend raggiungibile solo dal proxy;
   - `--forwarded-allow-ips` mai impostato a `*`;
   - rotazione di `LOGIN_LIMITE_SEGRETO` provata a pubblicazioni ferme (R-13).

### 5.5 Dati personali e AI

- **Registro dei trattamenti** (GDPR art. 30): quali dati (email, nome, foto, profilo della bottega), a che scopo, per quanto tempo.
- **"Niente si cancella" contro il diritto alla cancellazione** (art. 17). L'invariante §1.2 va conciliato con la legge, per esempio anonimizzando i dati personali e tenendo lo storico delle decisioni. Serve una decisione scritta in un ADR.
- **Fornitori**: OpenAI/OpenRouter e Meta ricevono dati. Servono il contratto di trattamento (DPA, art. 28), la verifica del trasferimento fuori dall'UE (capo V) e l'informativa agli artigiani.
- **Valutazione d'impatto** (DPIA, art. 35), se nelle foto compaiono persone o se l'analisi AI delle foto si estende.
- **AI Act, art. 50** (obblighi di trasparenza, applicabili dal 2 agosto 2026): verificare con il consulente se la dicitura già prevista per le immagini AI (T3-34) basta, o se serve anche un'etichetta nei metadati o sulla piattaforma. Meta ha una sua etichetta "Info sull'AI".

> **Soglia di uscita F2.** Matrice dei permessi verde e in CI; nessun risultato alto o critico aperto in analisi delle dipendenze, analisi statica, segreti e ZAP; issue #17 chiusa con le prove; checklist ASVS L2 compilata, con le eccezioni firmate; pentest eseguito e risultati gravi corretti; ADR su cancellazione e conservazione approvato.

## 6. Fase 3 · Qualità in tutte le parti

| Parte | Che cosa | Strumento | Soglia |
|---|---|---|---|
| Backend, unità e integrazione | Copertura dei **rami**, non delle righe | `pytest-cov` con `--cov-branch` | ≥ 85 % su `service.py` e `domain.py`; 100 % su transizioni e `interventi_ammessi()` |
| Qualità dei test | I test si accorgono quando il codice sbaglia? | `mutmut` su `domain.py`, `interventi.py`, `validatore.py`, `foto_pubblica.py` | Ogni mutante sopravvissuto analizzato: nuovo test o motivo scritto |
| Macchine a stati | Sequenze casuali di azioni non violano gli invarianti | `hypothesis`, test con stato (`RuleBasedStateMachine`) su campagna e post | Nessun controesempio su almeno 10 000 sequenze |
| API | Input generati dallo schema: niente 500, risposte conformi | `schemathesis` autenticato con i due ruoli | Zero 500; zero risposte fuori schema |
| Frontend, componenti | Logica delle pagine e dei moduli | `vitest` e Testing Library | Flussi critici coperti: invio, revisione, interventi, richiesta all'artigiano |
| End-to-end | Il percorso della demo, a due ruoli, da database vuoto | Playwright | Verde in CI, con video e traccia come artefatti |
| Accessibilità | Contrasto, tastiera, etichette, focus | `@axe-core/playwright` dentro gli E2E | Nessuna violazione grave o critica; obiettivo WCAG 2.2 AA |
| Contratto API | Tipi TS uguali allo schema | Tipi generati dallo schema e confrontati in CI | Nessuna differenza |
| Migrazioni | Vuoto → head; head → una indietro → head; upgrade su una copia anonimizzata di dati realistici | Alembic, in CI | Nessun errore, nessun dato perso |
| Backup | Database **e** archivio foto (R-11), con ripristino provato | `pg_dump`/`pg_restore` e copia dei file | RPO e RTO scritti e misurati |
| Build | Stesso commit, stesso risultato | Container con dipendenze bloccate | Stesso digest, o differenze spiegate |
| Adattatori esterni | Il finto e il vero si comportano allo stesso modo | Risposte vere registrate una volta (cassette) per LiteLLM e Meta, rilette nei test | Stessi esiti per i cinque tipi d'errore |
| Documentazione operativa | Chi non l'ha scritta riesce a seguirla | Prova "a mani nuove" | Installazione, rilascio e ripristino riusciti senza aiuto |

> **Soglia di uscita F3.** Tutte le righe della tabella con la soglia raggiunta e il report salvato come artefatto della CI o allegato a un ADR.

## 7. Fase 4 · Stress, concorrenza e guasti

### 7.1 Prima: obiettivi scritti

Un test di carico senza obiettivi non dice niente. Prima di farlo si scrivono i numeri attesi a 12 mesi (decisione D-01): quanti consorzi, artigiani e operatori, quante campagne al mese, post al giorno, foto per campagna. Poi gli obiettivi di servizio, per esempio p95 sotto i 300 ms per le letture e sotto 1 s per le scritture, errori sotto lo 0,1 %, ritardo di pubblicazione sotto i 2 minuti.

### 7.2 Carico

| Prova | Come | Che cosa si guarda |
|---|---|---|
| **Carico normale** | Il carico atteso per 30 minuti, con utenti misti (artigiani e operatori) | p50, p95 e p99 per endpoint; errori; connessioni al database; CPU e memoria |
| **Picco** | 10 volte il carico per 2 minuti | Code, timeout; risposte 503 ordinate invece di 500 |
| **Durata** | 8–24 ore al carico normale | Memoria che cresce; connessioni perse; crescita delle tabelle `limite_login`, `chiamata_ai` e di Procrastinate |
| **Upload** | 50 caricamenti in parallelo da 10 MB | Memoria di Pillow; limite di 12 MB per richiesta (413); disco |
| **Worker** | 1000 post in uscita nello stesso minuto, con Meta finto lento | Tempo per smaltirli; il tick serializzato tiene il passo? |

Strumenti: `locust` (scritto in Python, come il backend) oppure `k6`. I dati di prova si creano con le `fabbrica.py` dei moduli, su un database dedicato, mai su `adflow` o `adflow_test`.

### 7.3 Concorrenza

Sono i problemi che i test normali, una richiesta alla volta, non trovano. Tecnica: pytest con un `ThreadPoolExecutor` e una `threading.Barrier` che fa partire tutte le richieste nello stesso istante, ognuna con la sua connessione a PostgreSQL.

- Due operatori approvano la stessa campagna (R-03): atteso un solo esito, l'altro riceve 409.
- Approva e respingi in parallelo; approva e "richiesta all'artigiano" in parallelo.
- Quattro rigenerazioni dello stesso post in parallelo, con il limite a 3 (R-04).
- Cambia foto su due post della stessa campagna con la stessa foto (§1.9).
- Annulla o sposta un post mentre il tick lo sta pubblicando.
- Invio della stessa campagna da due schede.
- 20 accessi paralleli sullo stesso account: il limite deve restare esattamente 5. È già provato nei test esistenti; va rifatto sotto carico.

Correzioni tipiche, se un test fallisce:
- `SELECT … FOR UPDATE` sulla campagna o sul post all'inizio dell'operazione, come già fa `campagne.service`;
- vincoli unici sul database, per esempio una sola decisione `approvata` per campagna;
- aggiornamenti condizionali (`UPDATE … WHERE stato = 'in_revisione'`), controllando quante righe sono state toccate.

### 7.4 Guasti provocati

| Guasto | Comportamento atteso |
|---|---|
| PostgreSQL fermo per 30 s | 503 senza dati incoerenti; il login dà 503 (già previsto); il worker riparte da solo |
| AI: timeout, 429, JSON malformato, risposta vuota, risposta lunghissima | Uno dei cinque tipi d'errore; nessuna campagna bloccata a metà; costo registrato in `chiamata_ai` anche quando fallisce |
| Meta: 5xx, codice 190 (token non valido), 368 (contenuto bloccato), 4/17/32/613 (limiti), contenitore Instagram in errore o scaduto | Nessun doppio post (§1.7); errore temporaneo riprovato fino a `TENTATIVI_MAX`; errore definitivo → `fallito`, riprogrammabile, operatori avvisati |
| Timeout **dopo** che Meta ha pubblicato | Il caso più insidioso: va deciso come riconciliare (lettura del post esterno prima di riprovare) per non pubblicare due volte |
| Worker ucciso con `kill -9` durante una pubblicazione | Alla ripartenza il tentativo `in_corso` si riusa; nessun doppio `ok` |
| Disco pieno durante un upload | Errore chiaro; nessun file a metà; originale intatto (§1.3) |
| Email non consegnabile | Nessun blocco del flusso principale; riprova dei job di `notifiche` |
| Orologio: cambio d'ora (25/10/2026, 28/03/2027), fine anno, 29/02/2028 | Slot e scadenze in Europe/Rome giusti; nessun post saltato o doppio nell'ora che si ripete |

Strumenti: `toxiproxy` tra l'app e PostgreSQL per latenze e cadute. Per AI e Meta bastano gli adattatori finti con una modalità "guasto" configurabile, nello stile del progetto (costituzione §2.9).

### 7.5 Osservabilità, prima dello stress

Senza misure i test di stress non si possono leggere. Servono:
- latenza ed errori per endpoint;
- lunghezza della coda e job falliti di Procrastinate;
- ritardo di pubblicazione;
- costo AI al giorno e per campagna, da `chiamata_ai`;
- allarmi su ogni `login_limiter_unavailable` e sugli aumenti di `auth_failure` e `login_rate_limited`, che il logger `adflow.sicurezza` produce già.

> **Soglia di uscita F4.** Obiettivi di servizio rispettati nelle prove di carico e picco; nessuna perdita di risorse nella prova di durata; ogni scenario di concorrenza e di guasto con l'esito atteso, provato da un test ripetibile.

## 8. Fase 5 · Criteri di accettazione

Lo sviluppo completo si autorizza quando tutte le caselle sono spuntate, oppure quando ogni casella vuota ha un'eccezione scritta, con un responsabile e una data.

**Prodotto**
- [ ] Ogni CA del perimetro tracciato e verde
- [ ] Gli 11 invarianti con test che provano a violarli
- [ ] Test con stato senza controesempi
- [ ] Demo da database vuoto automatica in CI

**Sicurezza**
- [ ] Matrice dei permessi esaustiva, in CI
- [ ] Dipendenze, analisi statica, segreti e ZAP senza risultati alti aperti
- [ ] Header di sicurezza e controllo di `Origin`
- [ ] Issue #17 chiusa con le prove
- [ ] ASVS 5.0 L2 compilata; pentest con correzioni
- [ ] ADR su cancellazione, conservazione e AI Act

**Affidabilità**
- [ ] Obiettivi di servizio scritti e rispettati
- [ ] Prova di durata senza perdite
- [ ] Scenari di concorrenza e guasto verdi
- [ ] Backup e ripristino di database e foto provati
- [ ] Allarmi attivi su sicurezza, coda e spesa AI

**Processo e manutenzione**
- [ ] Dipendenze bloccate con hash; runtime e test separati
- [ ] SBOM e licenze a ogni rilascio
- [ ] Rilascio riproducibile e rollback provato
- [ ] Ogni parte del sistema conosciuta da almeno due persone
- [ ] Documentazione seguita con successo da chi non l'ha scritta

**Blocchi assoluti, senza eccezioni:**
- Un artigiano vede o modifica i dati di un altro artigiano.
- Un post viene pubblicato senza approvazione.
- Lo stesso post viene pubblicato due volte su Meta.
- Un segreto valido è presente nella storia di git.
- La foto originale di un artigiano viene modificata o persa.
- Dati personali o token compaiono nei log.

## 9. Piano d'azione

Una proposta da trasformare in task, ognuno con il suo brief, come per gli sprint. Le stime sono in persona-giorni e indicative: si correggono dopo la prima settimana. Le date partono da lunedì 9/11, dopo la consegna del 6/11; martedì 8/12 è festivo. Il calendario qui sotto è quello di partenza; quello con le vostre persone, il vostro tempo e le vostre scelte esce dalle domande di [Come si procede](#come-si-procede), che raccolgono i 17 pacchetti in 10 task della corsia 9 ([§12](#12-corsia-9-con-le-risposte-predefinite)).

### Calendario

| Pacchetto | S1 · 9–13/11 | S2 · 16–20/11 | S3 · 23–27/11 | S4 · 30/11–4/12 | S5 · 7–11/12 | S6 · 14–18/12 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| PA-01 Dipendenze (2 g) | ■ | | | | | |
| PA-02 CI di sicurezza (2 g) | ■ | | | | | |
| PA-03 Matrice dei permessi (3 g) | ■ | ■ | | | | |
| PA-04 Difese HTTP (2 g) | | ■ | | | | |
| PA-05 Concorrenza (4 g) | ■ | ■ | | | | |
| PA-06 Macchine a stati e fuzzing (4 g) | | ■ | ■ | | | |
| PA-07 Test frontend ed E2E (6 g) | | ■ | ■ | | | |
| PA-08 Rilascio e staging (5 g) | | ■ | ■ | | | |
| PA-09 Osservabilità (3 g) | | | ■ | | | |
| PA-10 Minacce e pentest interno (4 g) | | | ■ | ■ | | |
| PA-11 Carico e guasti (5 g) | | | | ■ | ■ | |
| PA-12 Backup e ripristino (2 g) | | | | ■ | | |
| PA-13 GDPR e AI Act (3 g + consulente) | ■ | ■ | ■ | ■ | | |
| PA-14 ASVS, pentest esterno, decisione (3 g + esterno) | | | | | ■ | ■ |
| PA-15 Copertura e mutazioni (3 g) | | | ■ | ■ | | |
| PA-16 Contratto API (2 g) | | | ■ | | | |
| PA-17 Prerequisiti sviluppo completo (progetto, 2 g) | | | | ■ | ■ | ■ |

Totale indicativo: circa 55 persona-giorni, più il consulente privacy e il pentest esterno. Con cinque persone a tempo parziale le 6 settimane sono realistiche. Con meno persone si tolgono prima PA-15 e PA-16, che sono miglioramenti e non blocchi.

### Pacchetti di lavoro

#### PA-01 · Igiene delle dipendenze (2 g · S1 · chiude R-05, R-06)
- Dichiarare `httpx` fra le dipendenze del runtime.
- Dividere in `requirements.in` (runtime) e `requirements-dev.in` (pytest, httpx2, black, pre-commit, cryptography), poi bloccare con `uv pip compile --generate-hashes`.
- Aggiornare CI, `allinea.py` e README per installare i due file.
- **Fatto quando:** installazione con `--require-hashes` riuscita in CI; l'immagine di produzione non contiene pytest; `pip-audit` pulito.
- **Nota:** tocca `requirements.txt` e `allinea.py`, quindi lo rivede il referente dei file comuni.

#### PA-02 · CI di sicurezza (2 g · S1 · chiude R-07 in parte)
- Un workflow `sicurezza.yml` con `pip-audit`, `npm audit`, `bandit`, `semgrep`, `gitleaks`.
- Una scansione di `gitleaks` su tutta la storia, una volta sola: ogni segreto trovato si cambia.
- Dependabot o Renovate; SBOM a ogni rilascio.
- **Fatto quando:** il workflow è obbligatorio per unire una PR; i risultati iniziali sono corretti o hanno un'eccezione scritta.

#### PA-03 · Matrice dei permessi esaustiva (3 g · S1–S2)
- Un file di dati con l'esito atteso per ogni operazione × ruolo (anonimo, artigiano A, artigiano B, operatore, admin).
- Un test parametrizzato che legge lo schema OpenAPI e fallisce se un'operazione non ha la sua riga.
- **Fatto quando:** le 52 operazioni sono coperte; un endpoint nuovo senza riga fa fallire la CI.

#### PA-04 · Difese HTTP (2 g · S2 · chiude R-01, R-02)
- Header di sicurezza sul proxy (HSTS, CSP per il frontend) e sulle risposte dell'API (`X-Content-Type-Options: nosniff`, `frame-ancestors 'none'`, `Referrer-Policy`).
- Un middleware che rifiuta le operazioni che cambiano stato con `Origin` o `Sec-Fetch-Site` non attesi e registra un evento di sicurezza.
- **Fatto quando:** ci sono test sugli header e sul rifiuto cross-site; l'esempio Nginx in `sicurezza-accesso.md` è aggiornato; ZAP baseline non dà avvisi sugli header.
- **Nota:** tocca la composizione e `core/`, quindi lo rivede il referente dei file comuni.

#### PA-05 · Concorrenza (4 g · S1–S2 · verifica R-03, R-04)
- Test con barriera per gli scenari di §7.3, a cominciare dall'approvazione.
- Per ogni test che fallisce: blocco della riga, vincolo unico o aggiornamento condizionale, ognuno in una PR separata.
- **Fatto quando:** tutti gli scenari di §7.3 sono verdi e superano 50 ripetizioni senza fallire.

#### PA-06 · Macchine a stati e fuzzing dell'API (4 g · S2–S3)
- `hypothesis` con `RuleBasedStateMachine` su campagna e post, con gli invarianti di §1 come controlli.
- `schemathesis` autenticato con i due ruoli, prima in locale e poi nella CI notturna.
- **Fatto quando:** zero controesempi su 10 000 sequenze; zero 500 dal fuzzing.

#### PA-07 · Test del frontend ed E2E (6 g · S2–S3 · chiude R-08)
- `vitest` e Testing Library per i flussi critici.
- Playwright per il percorso della demo a due ruoli, da database vuoto, con `@axe-core/playwright`.
- Si riprende lo script Playwright della PR #119 (vedi `brief-sistemazione.md`, punto 7).
- **Fatto quando:** E2E verde in CI con il video come artefatto; nessuna violazione di accessibilità grave.
- **Nota:** per ogni libreria nuova del frontend la PR indica nome, motivo e licenza.

#### PA-08 · Rilascio e staging (5 g · S2–S3 · chiude R-09, R-10, R-13)
- Container per API e worker; compose con PostgreSQL e proxy; configurazione del proxy con TLS e header.
- Ambiente di staging che replica la produzione; procedure di rilascio e di rollback provate.
- Prove della issue #17 allegate; procedura di rotazione dei segreti.
- **Fatto quando:** lo staging si installa da zero seguendo solo i documenti; #17 è chiusa; il rollback è stato eseguito almeno una volta.
- **Dipende da:** D-02 (hosting).

#### PA-09 · Osservabilità e tetto di spesa (3 g · S3 · chiude R-15)
- Metriche di §7.5 e allarmi; cruscotto di coda, errori e costo AI.
- Limite per utente sulle azioni che costano chiamate AI e tetto di spesa giornaliero nell'applicazione.
- **Fatto quando:** un allarme di prova arriva alla persona giusta; superato il tetto, le chiamate AI si fermano con un messaggio chiaro.

#### PA-10 · Modello delle minacce e pentest interno (4 g · S3–S4)
- Diagramma del flusso dei dati e analisi STRIDE di §5.2, scritti in `docs/`.
- Verifiche a mano di §5.4, compresa la prompt injection.
- **Fatto quando:** ogni minaccia ha una difesa o un rischio accettato e firmato; i risultati diventano task.

#### PA-11 · Carico, durata e guasti (5 g · S4–S5)
- Script `locust` o `k6` per le prove di §7.2 sullo staging.
- Guasti di §7.4 con `toxiproxy` e con gli adattatori finti in modalità guasto.
- **Fatto quando:** c'è un report con i numeri confrontati con gli obiettivi di D-01; ogni scenario di guasto ha l'esito atteso.
- **Dipende da:** PA-08, PA-09, D-01.

#### PA-12 · Backup e ripristino (2 g · S4 · chiude R-11 per l'MVP)
- Backup pianificato di database e archivio foto, cifrato e conservato fuori dal server.
- Ripristino completo su una macchina nuova, cronometrato.
- **Fatto quando:** RPO e RTO sono scritti e misurati; il ripristino si prova una volta al mese.

#### PA-13 · GDPR e AI Act (3 g + consulente · S1–S4)
- Registro dei trattamenti, informativa, DPA con i fornitori, verifica dei trasferimenti.
- ADR su cancellazione e conservazione rispetto all'invariante §1.2.
- DPIA se serve; verifica della trasparenza per le immagini AI (art. 50).
- **Fatto quando:** i documenti sono firmati dal titolare; l'ADR è approvato; le eventuali modifiche al prodotto sono scritte come task.

#### PA-14 · ASVS L2, pentest esterno e decisione (3 g + esterno · S5–S6)
- Checklist ASVS 5.0 L2 compilata, con una prova per ogni requisito.
- Pentest esterno sullo staging; correzione dei risultati gravi.
- Riunione di decisione con i criteri di §8.
- **Fatto quando:** c'è il verbale della decisione, con le eccezioni firmate.

#### PA-15 · Copertura dei rami e test di mutazione (3 g · S3–S4)
- `pytest-cov` con i rami in CI e soglie per file.
- `mutmut` su `domain.py`, `interventi.py`, `validatore.py`, `foto_pubblica.py`.
- **Fatto quando:** le soglie di §6 sono raggiunte e i mutanti sopravvissuti sono analizzati.

#### PA-16 · Contratto tra backend e frontend (2 g · S3)
- Tipi generati dallo schema OpenAPI e confrontati in CI con `src/api/*.ts`.
- Confronto dello schema prima e dopo a ogni PR, come già si fa in T3-08.
- **Fatto quando:** una differenza tra schema e tipi fa fallire la CI.

#### PA-17 · Prerequisiti per lo sviluppo completo (progetto, 2 g · S4–S6 · R-11, R-14)
- Progetto (un ADR, non codice) per la cifratura dei token social degli artigiani: chiave fuori dal database, rotazione, revoca.
- Archivio foto su object storage, per poter avere più istanze e backup più semplici.
- Più istanze dell'API: sessioni e limiti sono già su PostgreSQL; il resto va verificato.
- **Fatto quando:** gli ADR sono approvati e pronti per diventare task della roadmap.

## 10. Decisioni aperte

Da prendere nella prima riunione dopo il 6/11: senza queste alcuni pacchetti non possono partire.

| ID | Decisione | Serve a | Chi |
|---|---|---|---|
| D-01 | Numeri attesi a 12 mesi e obiettivi di servizio | PA-11 | Team con il cliente |
| D-02 | Hosting e fornitore (anche nella proposta tecnica §3.5) | PA-08, PA-12 | Team |
| D-03 | Referente per la sicurezza e referente privacy | PA-10, PA-13, PA-14 | Team |
| D-04 | Budget per il pentest esterno e il consulente privacy | PA-13, PA-14 | Team e tutor |
| D-05 | Politica di cancellazione e conservazione rispetto a §1.2 | PA-13 | Titolare con il consulente |
| D-06 | Rotte congelate `/api/archivio…`: lasciarle montate o toglierle dalla composizione fino allo sviluppo (R-12) | Superficie d'attacco | Referente dei file comuni, con un ADR |
| D-07 | Cosa fare se Meta va in timeout dopo aver pubblicato: riconciliare prima di riprovare? | §7.4, PA-11 | Area Meta |
| D-08 | Ordine dei pacchetti se le persone disponibili sono meno di cinque | Tutto il piano | Team |

## 11. Appendice

### Comandi di partenza

Esempi per provare gli strumenti in locale, dalla radice del repository. Non cambiano il codice. Le versioni si fissano quando gli strumenti entrano in CI.

```bash
# Vulnerabilità note nelle dipendenze Python
uvx pip-audit -r backend/requirements.txt

# Analisi statica di sicurezza del backend (solo media e alta)
uvx bandit -r backend/app -ll

# Regole semgrep per Python, OWASP e React
uvx semgrep scan --config p/python --config p/owasp-top-ten --config p/react backend/app frontend/src

# Segreti in tutta la storia di git (gitleaks 8.19 o successivo)
gitleaks git --log-opts="--all" .

# Vulnerabilità note nel frontend, senza le dipendenze di sviluppo
npm --prefix frontend audit --omit=dev

# Copertura dei rami del backend (da backend/)
uv run --with pytest-cov pytest --cov=app --cov-branch --cov-report=term-missing

# Fuzzing dell'API guidato dallo schema (API avviata in locale)
uvx schemathesis run http://localhost:8000/openapi.json --header "Cookie: adflow_sessione=<token di prova>"

# Scansione di base con ZAP sullo staging
docker run -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t https://staging.esempio.it
```

### Riferimenti

- OWASP Application Security Verification Standard 5.0 (livelli 1–3).
- OWASP API Security Top 10, edizione 2023.
- Regolamento (UE) 2016/679 (GDPR), artt. 17, 28, 30, 35 e capo V.
- Regolamento (UE) 2024/1689 (AI Act), art. 50.
- Documenti del progetto: `docs/agenti/constitution.md`, `perimetro-mvp.md`, `spec.md`, `converge.md`, `docs/sicurezza-accesso.md`, `docs/ROADMAP.md`.

### Glossario

| Termine | Significato |
|---|---|
| **BOLA / IDOR** | Accesso a un oggetto di un altro utente cambiando l'identificativo nella richiesta. |
| **CSRF** | Un altro sito fa partire una richiesta dal browser dell'utente, e la richiesta porta con sé il suo cookie. |
| **CSP, HSTS** | Header che dicono al browser da dove può caricare risorse (CSP) e di usare sempre HTTPS (HSTS). |
| **SBOM** | Elenco di tutti i componenti software di un rilascio, con versioni e licenze. |
| **Test di mutazione** | Si introducono piccoli errori nel codice: se i test passano lo stesso, non stanno controllando abbastanza. |
| **Test con stato** | Lo strumento genera sequenze casuali di azioni e controlla gli invarianti dopo ognuna. |
| **RPO / RTO** | Quanti dati si possono perdere al massimo (RPO) e in quanto tempo si torna in servizio (RTO). |
| **STRIDE** | Sei categorie di minacce: falsificazione, manomissione, ripudio, fuga di informazioni, negazione del servizio, aumento dei privilegi. |

## 12. Corsia 9 con le risposte predefinite

Generata il 24/10/2026 con le risposte in grassetto della tabella delle domande. È un esempio: con risposte diverse cambiano persone, date, stime e alcune modifiche (colonna «Che cosa cambia»). Le date contano metà tempo a persona e i festivi.

### 12.1 Prima della consegna, fuori dalla corsia

- **Doppia approvazione (R-03).** Un test con due richieste parallele su `revisione.approva()`. Se passano entrambe, blocco della riga della campagna e vincolo sulla decisione `approvata`. Branch `feature/fix-approvazione-concorrente`, PR rivista dal referente dei file comuni: rientra tra le correzioni ammesse fino al 6/11.
- **Cambio d'ora del 25/10/2026.** Un test sugli slot dei post tra il 24 e il 26/10 con l'orologio iniettato (`core/orologio.py`): nessun post saltato o doppio. La demo si svolge dopo il cambio.

### 12.2 Blocco per `docs/agenti/tasks.md`

Va in fondo agli sprint; `allinea.py` lo legge così com'è, dopo che T4-90 gli fa accettare la corsia 9.

```markdown
## Sprint 4 · Accettazione dopo l'MVP (sicurezza, qualità, esercizio)

Lo sprint 4 verifica l'MVP prima di autorizzare lo sviluppo completo (ADR-119, `docs/accettazione-post-mvp.md`). Non aggiunge funzioni: prove, difese, esercizio e conformità.

**Ordine.** T4-90 apre la corsia dopo la chiusura dello sprint 3 (T3-07). Poi, senza aspettarsi tra loro, T4-91, T4-92, T4-93, T4-94 e T4-96; gli altri quando ciò che sta in "Dipende da" è su `main`. T4-99 chiude la corsia con la decisione.

**Date.** Dal lunedì 9 novembre 2026 a circa giovedì 4 febbraio 2027, con metà tempo a persona. Stime indicative, da rivedere dopo la prima settimana.

### Corsia 9 · Accettazione e sicurezza (tutto il team)

Ogni task ha in `brief-accettazione.md` i file da toccare e da non toccare e il suo "Fatto quando": si legge la sezione del proprio task, non tutto il brief.

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T4-90 | **Preparazione della corsia 9**: ADR-119, `brief-accettazione.md`, corsia 9 in questa pagina, `allinea.py` che accetta la corsia 9; il documento di accettazione passa da bozza ad approvato con le risposte alle domande. Giovanni | `docs/accettazione-post-mvp.md`; ADR-114; `perimetro-mvp.md` | T3-07 | documenti coerenti tra loro; `uv run python allinea.py 9` mostra T4-91 tra i pronti; `tests/test_allinea.py` verde con la corsia 9; comandi di converge §1 verdi | ☐ |
| T4-91 | **Dipendenze bloccate e CI di sicurezza**: runtime e test in due file con gli hash, `httpx` dichiarato, workflow di sicurezza obbligatorio, Dependabot, SBOM a ogni rilascio. Nilton | `brief-accettazione.md` §T4-91; `accettazione-post-mvp.md` §5.3; converge §1 | T4-90 | la CI installa con `--require-hashes`; nell'ambiente di produzione non c'è pytest; `sicurezza.yml` è obbligatorio per unire; i risultati iniziali sono corretti o hanno un'eccezione scritta; gitleaks su tutta la storia senza segreti validi | ☐ |
| T4-92 | **Permessi e difese HTTP**: matrice dei permessi su tutte le operazioni, header di sicurezza, controllo dell'origine, pixel delle foto al caricamento, limite delle azioni che costano chiamate AI. Gianluca | `brief-accettazione.md` §T4-92; `accettazione-post-mvp.md` §5.4; constitution §3; `docs/sicurezza-accesso.md` | T4-90 | ogni operazione dello schema ha la sua riga e un'operazione nuova senza riga fa fallire la CI; test degli header e del rifiuto cross-site; foto oltre il limite di pixel rifiutata al caricamento; oltre il limite delle azioni risposta 429; ZAP baseline senza avvisi sugli header | ☐ |
| T4-93 | **Dati personali e AI Act**: registro dei trattamenti, informativa, contratti con i fornitori, cancellazione e conservazione, trasparenza delle immagini AI. Silvia | `brief-accettazione.md` §T4-93; `accettazione-post-mvp.md` §5.5; constitution §1.2 | T4-90 | registro e informativa firmati dal titolare; DPA con i fornitori verificati; ADR 120 e 121 approvati; le modifiche al prodotto che ne escono sono task nuovi | ☐ |
| T4-94 | **Concorrenza**: richieste parallele su approvazione, interventi, rigenerazione, invio e pubblicazione; correzioni dove un test fallisce (l'approvazione è già stata verificata prima del 6/11). Giovanni | `brief-accettazione.md` §T4-94; `accettazione-post-mvp.md` §7.3; constitution §1 e §2; plan §6 | T4-90 | gli scenari di §7.3 verdi e ripetuti 50 volte senza fallire; ogni correzione con il suo test | ☐ |
| T4-95 | **Invarianti, fuzzing, copertura e mutazioni**: test con stato sulle macchine a stati, attacchi agli 11 invarianti, fuzzing dell'API dallo schema, copertura dei rami e test di mutazione. Gianluca | `brief-accettazione.md` §T4-95; `accettazione-post-mvp.md` §4.3 e §6 | T4-91, T4-94 | nessun controesempio su 10 000 sequenze; ogni invariante con un test che prova a violarlo; zero 500 dal fuzzing; soglie di copertura di §6 in CI; mutanti sopravvissuti analizzati | ☐ |
| T4-96 | **Frontend: test, E2E, accessibilità e contratto API**: test dei componenti, percorso della demo in Playwright a due ruoli, controllo di accessibilità, tipi generati dallo schema OpenAPI. Angelo | `brief-accettazione.md` §T4-96; `accettazione-post-mvp.md` §6; converge §4; `brief-sistemazione.md` punto 7 | T4-90 | E2E verde in CI da database vuoto, con il video come artefatto; nessuna violazione di accessibilità grave o critica; una differenza tra schema e tipi fa fallire la CI; build e lint puliti | ☐ |
| T4-97 | **Rilascio, staging, osservabilità e backup**: container, compose e proxy, staging sul fornitore che si sceglierà, backup e ripristino, metriche e allarmi. Nilton | `brief-accettazione.md` §T4-97; `accettazione-post-mvp.md` §6 e §7.5; `docs/sicurezza-accesso.md`; decisione D-02 | T4-91 | staging installato da zero seguendo solo i documenti; issue #17 chiusa con le prove; rilascio, rollback e ripristino eseguiti e cronometrati; RPO e RTO scritti; un allarme di prova arriva alla persona giusta | ☐ |
| T4-98 | **Minacce, carico e guasti**: modello delle minacce, verifiche a mano di §5.4 compresa la prompt injection, prove di carico e guasti provocati sullo staging. Silvia | `brief-accettazione.md` §T4-98; `accettazione-post-mvp.md` §5.2, §5.4 e §7; decisione D-01 | T4-92, T4-94, T4-97 | ogni minaccia di §5.2 ha una difesa o un rischio accettato e firmato; ogni guasto di §7.4 ha l'esito atteso; i difetti trovati sono task nuovi; report di carico, picco e durata confrontato con gli obiettivi decisi in D-01 | ☐ |
| T4-99 | **Verifica ASVS, pentest e decisione**: checklist ASVS 5.0 livello 2 con le prove, pentest, ADR dei prerequisiti per lo sviluppo completo, riunione di decisione con i criteri di §8. Giovanni | `brief-accettazione.md` §T4-99; `accettazione-post-mvp.md` §5.1 e §8 | tutti i task dello sprint | checklist ASVS 5.0 L2 compilata con una prova per requisito; ADR dei prerequisiti approvati; verbale della decisione con le eccezioni firmate; pentest interno approfondito sullo staging, risultati gravi corretti e rischio di non avere un pentest esterno accettato per iscritto | ☐ |

Riga da aggiungere alla tabella delle aree, in cima a questa pagina:

| 9 · Accettazione e sicurezza | tutto il team | ADR-119: verifiche di sicurezza, concorrenza, qualità ed esercizio prima dello sviluppo completo (`brief-accettazione.md`) |
```

### 12.3 Riga per `docs/ADR.md`

```markdown
| 119 | 24/10 | **Sprint 4 · accettazione dopo l'MVP** (corsia 9, T4-90…T4-99, `brief-accettazione.md`). Prima dello sviluppo completo si verificano sicurezza, concorrenza, qualità ed esercizio con i criteri di `docs/accettazione-post-mvp.md` §8. Ambito: tutto il piano; persone: tutto il team; hosting: da decidere; verifiche esterne: solo il consulente privacy; rotte congelate `/api/archivio…`: restano montate. | Servono prove ripetibili prima di aggiungere funzioni; i punti R-01…R-15 del documento bloccano la produzione o lo sviluppo completo | Passare subito allo sviluppo completo; affidarsi solo a un pentest esterno senza prove interne |  |
```

### 12.4 Brief della corsia, per `docs/agenti/brief-accettazione.md`

#### Brief · Corsia 9 · Accettazione e sicurezza (T4-90…T4-99)

Per chi fa un task della corsia 9. Decisione: ADR-119. Leggi prima `constitution.md`, poi **solo** la sezione del tuo task qui sotto e le parti di `docs/accettazione-post-mvp.md` che cita. Dove il codice di `main` è diverso da come è descritto qui, fermati e chiedi.

**Decisioni prese con le domande** (24/10):

- Ambito: Tutto il piano.
- Persone: Giovanni, Gianluca, Silvia, Nilton, Angelo.
- Tempo a settimana: Metà tempo.
- Inizio: lunedì 9 novembre 2026.
- Hosting: da decidere.
- Verifiche esterne: Solo il consulente privacy.
- Numeri di utilizzo: Da definire con il cliente.
- Doppia approvazione: Subito, prima della consegna.
- Rotte congelate: Restano montate.

**Regole di lavoro per tutti i task.**
- Un branch `feature/<id>-<breve>` da `main`; fai solo il tuo task; tocca i file elencati e i loro test. Se ti serve un file che non è nell'elenco, fermati e chiedi.
- Nessun cambio di comportamento che il task non chiede. Ogni difetto trovato è una PR a parte, con il suo test e il riferimento al task che l'ha trovato.
- Gli strumenti di verifica stanno nei `requirements` di sviluppo o in CI, mai nel runtime; ogni libreria nuova ha nome, motivo e licenza nella PR.
- Nei test nessuna chiamata reale ad AI, Meta o email; sullo staging solo la pagina Meta di prova.
- In report, screenshot e log allegati nessun segreto, token, cookie o dato personale vero.
- Fatto quando, per ogni task: il suo "Fatto quando" qui sotto, i comandi di converge §1 verdi e la casella in `tasks.md`.

---

##### T4-90 · Preparazione della corsia 9

**Chi**: Giovanni · **Stima**: 2 giorni · **Dipende da**: T3-07 · **Copre**: —

**Leggi**: `docs/accettazione-post-mvp.md`; ADR-114; `perimetro-mvp.md`.

**File e modifiche**:
- `docs/ADR.md`: riga 119 con le decisioni prese con le domande (testo generato con le domande).
- `docs/accettazione-post-mvp.md`: via l'avviso di bozza; risposte alle domande in §10; stato «approvato».
- `docs/agenti/tasks.md`: sezione «Sprint 4 · Accettazione dopo l'MVP» con la corsia 9 (testo generato con le domande) e riga 9 nella tabella delle aree.
- `docs/agenti/brief-accettazione.md`: nuovo, una sezione per task (testo generato con le domande).
- `docs/agenti/constitution.md` §4: 429 anche per il limite delle azioni che costano chiamate AI (serve a T4-92).
- `allinea.py`: la scelta della corsia accetta `9` (oggi `"01234567"`, riga 377; la 8 la aggiunge la corsia dell'interfaccia, se approvata) e il messaggio dice «da 0 a 9».
- `backend/tests/test_allinea.py`: un caso con lo sprint 4 e la corsia 9.
- `.vscode/tasks.json`: le voci mancanti fino alla 9 nell'elenco delle corsie (oggi si ferma alla 6).
- `AGENTS.md`: lo sprint corrente, dopo la chiusura dello sprint 3.

**Da non toccare**: codice dell'app: il task cambia solo documenti, `allinea.py` e il suo test.

**Fatto quando**: documenti coerenti tra loro; `uv run python allinea.py 9` mostra T4-91 tra i pronti; `tests/test_allinea.py` verde con la corsia 9; comandi di converge §1 verdi.

**Nota**: Cambia `allinea.py`: lo rivede il referente dei file comuni.

##### T4-91 · Dipendenze bloccate e CI di sicurezza

**Chi**: Nilton · **Stima**: 4 giorni · **Dipende da**: T4-90 · **Copre**: PA-01, PA-02 · R-05, R-06, R-07

**Leggi**: `brief-accettazione.md` §T4-91; `accettazione-post-mvp.md` §5.3; converge §1.

**File e modifiche**:
- `backend/requirements.in`: dipendenze del runtime, con `httpx` dichiarato (oggi arriva solo tramite litellm).
- `backend/requirements-dev.in`: pytest, httpx2, black, pre-commit, cryptography.
- `backend/requirements.txt` e `backend/requirements-dev.txt`: generati con `uv pip compile --generate-hashes`.
- `.github/workflows/backend.yml`: installa i due file con `--require-hashes`.
- `allinea.py` e `backend/README.md`: installano i due file.
- `.github/workflows/sicurezza.yml`: nuovo; pip-audit, `npm audit --omit=dev`, bandit, semgrep, gitleaks, SBOM con cyclonedx.
- `.github/dependabot.yml`: nuovo; pip, npm e GitHub Actions, una volta a settimana.
- `docs/agenti/converge.md` §1: i controlli nuovi.

**Da non toccare**: codice dell'app; gli strumenti di analisi stanno solo in CI, non nei `requirements`.

**Fatto quando**: la CI installa con `--require-hashes`; nell'ambiente di produzione non c'è pytest; `sicurezza.yml` è obbligatorio per unire; i risultati iniziali sono corretti o hanno un'eccezione scritta; gitleaks su tutta la storia senza segreti validi.

**Nota**: Cambia `requirements.txt` e `allinea.py`: lo rivede il referente dei file comuni. Un segreto trovato si considera compromesso e si cambia prima di unire.

##### T4-92 · Permessi e difese HTTP

**Chi**: Gianluca · **Stima**: 7 giorni · **Dipende da**: T4-90 · **Copre**: PA-03, PA-04 · R-01, R-02, R-15

**Leggi**: `brief-accettazione.md` §T4-92; `accettazione-post-mvp.md` §5.4; constitution §3; `docs/sicurezza-accesso.md`.

**File e modifiche**:
- `backend/tests/permessi/matrice.py`: esito atteso per operazione × ruolo (anonimo, artigiano A, artigiano B, operatore, admin), 52 operazioni.
- `backend/tests/permessi/test_matrice_permessi.py`: legge `app.openapi()`, prova ogni cella e fallisce se un'operazione non ha la sua riga.
- `backend/app/core/intestazioni.py`: nuovo middleware; `X-Content-Type-Options: nosniff`, `Content-Security-Policy: frame-ancestors 'none'`, `Referrer-Policy`, `Cache-Control: no-store` sulle risposte con dati personali.
- `backend/app/core/origine.py`: nuovo; POST, PUT, PATCH e DELETE con `Origin` o `Sec-Fetch-Site` non ammessi → 403 ed evento `cross_site_rejected`.
- `backend/app/core/limite_azioni.py`: nuovo; contatore per utente su PostgreSQL, come `limite_login`, per invio della campagna e rigenerazione (429).
- `backend/alembic/versions/`: tabella del contatore delle azioni.
- `backend/app/core/config.py` e `backend/.env.example`: `ORIGINI_AMMESSE` e il limite delle azioni per utente e per ora.
- `backend/app/main.py`: registra i middleware.
- `backend/app/adapters/archivio/base.py`: controllo dei pixel già al caricamento, come chiede la costituzione §3, se manca.
- `docs/sicurezza-accesso.md`: esempio Nginx con HSTS e CSP; gli eventi nuovi.

**Da non toccare**: `campagne/archivio.py` (congelato); messaggi e codici esistenti.

**Fatto quando**: ogni operazione dello schema ha la sua riga e un'operazione nuova senza riga fa fallire la CI; test degli header e del rifiuto cross-site; foto oltre il limite di pixel rifiutata al caricamento; oltre il limite delle azioni risposta 429; ZAP baseline senza avvisi sugli header.

**Nota**: Cambia `core/`, la composizione e `alembic/`: lo rivede il referente dei file comuni. Ogni differenza tra matrice e comportamento è un difetto: PR a parte con il suo test.

##### T4-93 · Dati personali e AI Act

**Chi**: Silvia · **Stima**: 3 giorni · **Dipende da**: T4-90 · **Copre**: PA-13

**Leggi**: `brief-accettazione.md` §T4-93; `accettazione-post-mvp.md` §5.5; constitution §1.2.

**File e modifiche**:
- `docs/conformita/registro-trattamenti.md`: nuovo (GDPR art. 30).
- `docs/conformita/informativa-artigiani.md`: nuovo.
- `docs/conformita/fornitori.md`: nuovo; DPA con OpenAI/OpenRouter e Meta, trasferimenti fuori dall'UE.
- `docs/ADR.md`: riga 120, cancellazione e conservazione rispetto all'invariante §1.2 (per esempio anonimizzare invece di cancellare).
- `docs/ADR.md`: riga 121, trasparenza delle immagini AI (AI Act art. 50) rispetto alla dicitura di T3-34.
- `docs/conformita/dpia.md`: solo se la valutazione dice che serve.

**Da non toccare**: codice: le modifiche al prodotto diventano task a parte.

**Fatto quando**: registro e informativa firmati dal titolare; DPA con i fornitori verificati; ADR 120 e 121 approvati; le modifiche al prodotto che ne escono sono task nuovi.

**Nota**: Con il consulente privacy: il lavoro del team è di circa 3 giorni, ma servono circa 4 settimane di calendario.

##### T4-94 · Concorrenza

**Chi**: Giovanni · **Stima**: 3 giorni · **Dipende da**: T4-90 · **Copre**: PA-05 · R-03, R-04

**Leggi**: `brief-accettazione.md` §T4-94; `accettazione-post-mvp.md` §7.3; constitution §1 e §2; plan §6.

**File e modifiche**:
- `backend/tests/concorrenza/conftest.py`: aiuto con `threading.Barrier`, una connessione a PostgreSQL per richiesta.
- `backend/tests/concorrenza/test_approvazione.py`, `test_interventi.py`, `test_invio.py`, `test_pubblicazione.py`: gli scenari di §7.3.
- `backend/app/moduli/campagne/service.py`: funzione che legge la campagna con il blocco della riga (`with_for_update`), scritta in plan §6.
- `backend/app/moduli/revisione/service.py`: `approva()` e `respingi()` usano la lettura con il blocco.
- `backend/app/moduli/contenuti/interventi.py`: blocco del post prima di controllare e incrementare `n_rigenerazioni_testo`.
- `backend/alembic/versions/`: vincoli unici dove servono (per esempio una sola decisione `approvata` per campagna).
- `docs/agenti/plan.md` §6: la funzione nuova.

**Da non toccare**: transizioni, messaggi e codice congelato.

**Fatto quando**: gli scenari di §7.3 verdi e ripetuti 50 volte senza fallire; ogni correzione con il suo test.

**Nota**: Può cambiare `alembic/` e un `service.py` di un altro modulo: lo rivede il referente dei file comuni. Se la correzione dell'approvazione è già su `main`, qui resta solo il test di regressione.

##### T4-95 · Invarianti, fuzzing, copertura e mutazioni

**Chi**: Gianluca · **Stima**: 6 giorni · **Dipende da**: T4-91, T4-94 · **Copre**: PA-06, PA-15 · F1 §4.3

**Leggi**: `brief-accettazione.md` §T4-95; `accettazione-post-mvp.md` §4.3 e §6.

**File e modifiche**:
- `backend/requirements-dev.in`: hypothesis (MPL-2.0) e schemathesis (MIT), pytest-cov (MIT) e mutmut (BSD-3-Clause), con nome, motivo e licenza nella PR.
- `backend/tests/proprieta/test_macchina_campagna.py` e `test_macchina_post.py`: `RuleBasedStateMachine`, con gli invarianti come controlli.
- `backend/tests/invarianti/`: un file per invariante di §1, con gli attacchi di §4.3.
- `backend/tests/test_confini.py`: assegnazioni a `.stato` fuori dal modulo proprietario (§1.8).
- `.github/workflows/notte.yml`: nuovo; schemathesis autenticato con i due ruoli e mutmut, ogni notte.
- `backend/.coveragerc`: copertura dei rami e soglie per file (`fail_under`).
- Analisi dei mutanti sopravvissuti su `domain.py`, `interventi.py`, `validatore.py`, `foto_pubblica.py`.

**Da non toccare**: codice dell'app, salvo correzioni dei difetti trovati, ognuna in una PR sua.

**Fatto quando**: nessun controesempio su 10 000 sequenze; ogni invariante con un test che prova a violarlo; zero 500 dal fuzzing; soglie di copertura di §6 in CI; mutanti sopravvissuti analizzati.

**Nota**: Cambia i `requirements` di sviluppo: nome, motivo e licenza nella PR.

##### T4-96 · Frontend: test, E2E, accessibilità e contratto API

**Chi**: Angelo · **Stima**: 8 giorni · **Dipende da**: T4-90 · **Copre**: PA-07, PA-16 · R-08

**Leggi**: `brief-accettazione.md` §T4-96; `accettazione-post-mvp.md` §6; converge §4; `brief-sistemazione.md` punto 7.

**File e modifiche**:
- `frontend/package.json`: script `test`, `test:e2e`, `tipi:api`; devDependencies vitest (MIT), @testing-library/react (MIT), @playwright/test (Apache-2.0), @axe-core/playwright (MPL-2.0), openapi-typescript (MIT).
- `frontend/src/**/*.test.tsx`: invio, revisione, interventi, richiesta all'artigiano.
- `frontend/e2e/percorso-demo.spec.ts`: percorso della demo a due ruoli, dallo script della PR #119.
- `frontend/src/api/schema.d.ts`: generato dallo schema OpenAPI; i tipi di `src/api/*.ts` si confrontano con questo.
- `.github/workflows/frontend.yml`: lavori `test` ed `e2e` (con PostgreSQL e backend) e controllo dei tipi generati.
- `frontend/README.md`: come si lanciano.

**Da non toccare**: stile e comportamento delle pagine.

**Fatto quando**: E2E verde in CI da database vuoto, con il video come artefatto; nessuna violazione di accessibilità grave o critica; una differenza tra schema e tipi fa fallire la CI; build e lint puliti.

**Nota**: Librerie nuove nel frontend: nome, motivo e licenza nella PR.

##### T4-97 · Rilascio, staging, osservabilità e backup

**Chi**: Nilton · **Stima**: 9 giorni · **Dipende da**: T4-91 · **Copre**: PA-08, PA-09, PA-12 · R-09, R-10, R-11, R-13

**Leggi**: `brief-accettazione.md` §T4-97; `accettazione-post-mvp.md` §6 e §7.5; `docs/sicurezza-accesso.md`; decisione D-02.

**File e modifiche**:
- `backend/Dockerfile`: API e worker dalla stessa immagine, utente non root, solo `requirements.txt`.
- `deploy/compose.yaml`: api, worker, PostgreSQL 16, proxy; segreti da file, mai nell'immagine.
- `deploy/nginx.conf`: TLS, HSTS, CSP, frontend statico, `/api/` verso l'API, header inoltrati sovrascritti.
- `deploy/backup.sh`: `pg_dump` e copia di `ARCHIVIO_FOTO_DIR`, cifrati e fuori dal server.
- `deploy/README.md`: rilascio, rollback, rotazione dei segreti (R-13), backup e ripristino.
- Metriche e allarmi: latenza, errori, coda di Procrastinate, ritardo di pubblicazione, costo AI al giorno, eventi di `adflow.sicurezza`.
- `docs/sicurezza-accesso.md`: rimando a `deploy/` e prove della issue #17.

**Da non toccare**: comportamento dell'app; i valori di `.env` veri non entrano nel repository.

**Fatto quando**: staging installato da zero seguendo solo i documenti; issue #17 chiusa con le prove; rilascio, rollback e ripristino eseguiti e cronometrati; RPO e RTO scritti; un allarme di prova arriva alla persona giusta.

**Nota**: Cambia la composizione: lo rivede il referente dei file comuni. Parte dopo la decisione D-02 sull'hosting.

##### T4-98 · Minacce, carico e guasti

**Chi**: Silvia · **Stima**: 9 giorni · **Dipende da**: T4-92, T4-94, T4-97 · **Copre**: PA-10, PA-11

**Leggi**: `brief-accettazione.md` §T4-98; `accettazione-post-mvp.md` §5.2, §5.4 e §7; decisione D-01.

**File e modifiche**:
- `docs/sicurezza-minacce.md`: nuovo; flusso dei dati, confini di fiducia, STRIDE.
- `backend/app/adapters/ai/finto.py` e l'adattatore social finto: modalità guasto configurabile, rifiutata in produzione.
- `backend/tests/guasti/`: un test per ogni riga di §7.4.
- `carico/locustfile.py` e `carico/README.md`: nuovi, fuori da `backend/`; dati dalle `fabbrica.py`, su un database dedicato.
- `deploy/compose.yaml`: toxiproxy, solo per le prove.
- `docs/report/`: report di carico e di guasti, con la data.

**Da non toccare**: database `adflow` e `adflow_test`; la pagina Meta vera, salvo quella di prova.

**Fatto quando**: ogni minaccia di §5.2 ha una difesa o un rischio accettato e firmato; ogni guasto di §7.4 ha l'esito atteso; i difetti trovati sono task nuovi; report di carico, picco e durata confrontato con gli obiettivi decisi in D-01.

**Nota**: Le correzioni dei difetti trovati sono PR a parte, con il loro test.

##### T4-99 · Verifica ASVS, pentest e decisione

**Chi**: Giovanni · **Stima**: 6 giorni · **Dipende da**: tutti i task dello sprint · **Copre**: PA-14, PA-17

**Leggi**: `brief-accettazione.md` §T4-99; `accettazione-post-mvp.md` §5.1 e §8.

**File e modifiche**:
- `docs/asvs-l2.md`: nuovo; requisito, prova, esito.
- `docs/report/pentest-interno.md`: metodo, perimetro, risultati.
- `docs/ADR.md`: riga 122, cifratura dei token social degli artigiani (R-14); riga 123, archivio foto su object storage (R-11); riga 124, più istanze dell'API.
- `docs/accettazione-post-mvp.md` §8: caselle spuntate, verbale e firma.
- `docs/ROADMAP.md`: i prerequisiti accanto alle voci che ne dipendono.

**Da non toccare**: codice dell'app: i difetti trovati diventano task.

**Fatto quando**: checklist ASVS 5.0 L2 compilata con una prova per requisito; ADR dei prerequisiti approvati; verbale della decisione con le eccezioni firmate; pentest interno approfondito sullo staging, risultati gravi corretti e rischio di non avere un pentest esterno accettato per iscritto.

**Nota**: Senza pentest esterno questa non è una verifica indipendente: il verbale lo dice in chiaro.

---

##### Ordine di lavoro

| Task | Chi | Dal | Al |
|---|---|---|---|
| T4-90 Preparazione della corsia 9 | Giovanni | 9/11 | 12/11 |
| T4-91 Dipendenze bloccate e CI di sicurezza | Nilton | 13/11 | 24/11 |
| T4-92 Permessi e difese HTTP | Gianluca | 13/11 | 2/12 |
| T4-93 Dati personali e AI Act | Silvia | 13/11 | 11/12 |
| T4-94 Concorrenza | Giovanni | 13/11 | 20/11 |
| T4-95 Invarianti, fuzzing, copertura e mutazioni | Gianluca | 3/12 | 21/12 |
| T4-96 Frontend: test, E2E, accessibilità e contratto API | Angelo | 13/11 | 4/12 |
| T4-97 Rilascio, staging, osservabilità e backup | Nilton | 25/11 | 21/12 |
| T4-98 Minacce, carico e guasti | Silvia | 22/12 | 19/1 |
| T4-99 Verifica ASVS, pentest e decisione | Giovanni | 20/1 | 4/2 |

##### Decisioni ancora aperte

- **D-01** Numeri attesi a 12 mesi e obiettivi di servizio (serve a T4-98; Team con il cliente).
- **D-02** Hosting e fornitore dello staging e della produzione (serve a T4-97, T4-98; Team).
- **D-03** Referente per la sicurezza e referente privacy (serve a T4-93, T4-98, T4-99; Team).
- **D-04** Budget per un pentest esterno prima della produzione con clienti veri (serve a T4-99; Team e tutor).
- **D-07** Cosa fare se Meta va in timeout dopo aver pubblicato: riconciliare prima di riprovare? (serve a T4-98; Area Meta).

---

*Documento preliminare, da valutare. Preparato il 24/10/2026 leggendo `main` a `6a8e2ed`, senza modifiche al codice. È una proposta: stime e ordine si decidono insieme e diventano task con il loro brief.*
