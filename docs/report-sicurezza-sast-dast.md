# Report di Valutazione di Sicurezza: SAST e DAST (Round 1 & Round 2)

**Data di redazione:** 4 Novembre 2026
**Autore / Referente:** Silvia (Corsia 2 · Campagne & Archivio)
**Destinatari:** Team di sviluppo AdFlow Suite, Referente Architettura e Sicurezza
**Ambito di applicazione:** Sprint 3 / MVP (ADR-114, Spec R-13, Spec R-42, Costituzione §1 e §3, Task T3-09)
**Stato esito:** **CONFORME** (99/99 test di sicurezza unitari superati + 6/6 probe dinamici avanzati PASS · 0 vulnerabilità critiche nel codice)

---

## 1. Sintesi Esecutiva (Executive Summary)

Il presente documento certifica i risultati complessivi delle due sessioni di verifica e collaudo di sicurezza applicativa (**SAST** - *Static Application Security Testing* e **DAST** - *Dynamic Application Security Testing*) condotte sul backend di **AdFlow Suite**.

La valutazione ha coperto approfonditamente:
- I componenti e gli adattatori di competenza della Corsia 2 (`moduli/campagne`, `adapters/archivio`).
- I moduli trasversali di sicurezza e controllo accessi (`moduli/accesso`, `core/security`, `core/limite_richiesta`, `core/limite_login`, `core/eventi_sicurezza`).
- Il rispetto rigoroso delle invarianti architetturali della Costituzione di Progetto (§1, §2.6, §3).
- La resilienza agli attacchi di fuzzing, spoofing, tampering, directory traversal e denial of service (DoS).
- L'allineamento con la suite canonica di sicurezza introdotta in `origin/main` tramite il task T3-09.

### Punti Chiave Rilevati
1. **0 Primitive ad Alto Rischio**: L'analisi dell'albero sintattico astratto (AST) su 102 file sorgente (confermata sia dallo scanner locale sia dalla suite canonica di T3-09) ha evidenziato **zero occorrenze** di `eval()`, `exec()`, `os.system()`, `subprocess(shell=True)`, deserializzazioni insicure `pickle` o query SQL interpolate via stringhe.
2. **0 Segreti o Credenziali Hardcoded**: Nessuna chiave API, token privato o password è presente nel codice sorgente o nei file tracciati da Git (Costituzione §3).
3. **Invariante di Costituzione §2.6 Verificata**: Analisi AST dedicata sui **7 file `service.py`** del backend: **zero chiamate a `.commit()`**. La gestione della transazione rimane saldamente confinata a router e worker.
4. **Difesa in Profondità (Defense-in-Depth) Attiva**:
   - **Validazione Magic Bytes**: Controllo binario reale delle firme immagine (JPEG, PNG, WEBP), bloccando alla radice file spoofing o polyglot payload.
   - **Prevenzione Directory Traversal (CWE-22)**: Generazione del nome file univoca lato server (UUIDv4) e validazione dei percorsi con divieto di sequenze `..` e caratteri speciali.
   - **Doppia Barriera Anti-DoS**: Limite applicativo di 10 MB per singola immagine (`DIMENSIONE_MAX_BYTE`) e middleware HTTP esterno che rigetta payload superiori a 12 MB con `413 Payload Too Large`.
   - **Shield Dinamico Anti-Brute Force**: Transizione automatica e verificata da credenziali errate (`401`) a blocco persistente per IP/account (`429 Too Many Requests` con evento `login_rate_limited` e header `Retry-After`).
   - **Header Difensivi e CORS**: Assenza totale di wildcard `*` su rotte autenticate e iniezione garantita di `Cache-Control: no-store` su tutti i codici di errore (401, 403, 429).
5. **Resilienza ai Casi Limite**: Fuzzing con stringhe estreme da 10.000 caratteri e Content-Type incompatibili gestiti pulitamente con codice `422 Unprocessable Entity` in lingua italiana, **zero errori 500**.
6. **Integrità Crittografica Foto Pubbliche**: La rotta per Instagram (`/api/foto/{id}/pubblica`) convalida la firma HMAC-SHA256 con scadenza; firme alterate o scadute restituiscono `404 Not Found` senza rivelare percorsi fisici.
7. **Collaudo Automatizzato**: 99 test Pytest dedicati superati con esito **100% verde (99/99 PASS)** su database PostgreSQL reale (`adflow_test`).

---

## 2. Metodologia di Collaudo

| Parametro | Dettaglio Operativo |
|---|---|
| **Sistema Operativo & Runtime** | Windows 11 · Python 3.11.15 · FastAPI 0.141.1 · Starlette 1.3.1 |
| **Database di Collaudo** | PostgreSQL 16 locale (`adflow_test`), isolato da produzione |
| **Metodologia SAST** | Scansione statica AST (modulo standard `ast`), regex scanner per secret hunting, verifica invarianti architetturali, audit delle dipendenze contro il database Open Source Vulnerabilities (OSV.dev) |
| **Metodologia DAST** | Probe dinamici tramite client ASGI in-process (`TestClient`), fuzzing di campi estremi (10k caratteri), simulazione DoS, manomissione firme HMAC, traversal e verifica stati di rate-limiting |
| **Suite di Test Automatizzata** | `pytest 9.1.1` con fixture isolate e context manager deterministici |

---

## 3. Risultati SAST (Static Application Security Testing)

La scansione statica ha coperto **102 file sorgente Python** presenti nella cartella `backend/app/`.

### Tabella dei Controlli Statici (Round 1 & Round 2)

| Controllo SAST | Obiettivo di Sicurezza | File Verificati | Esito | Note Tecniche |
|---|---|:---:|:---:|---|
| **AST Danger Primitives** | Rilevare esecuzione arbitraria di codice o comandi di sistema | 102 | **PASS** | Assenza totale di `eval`, `exec`, `os.system`, `os.popen`, `subprocess.run(shell=True)`. |
| **Unsafe Deserialization** | Prevenire deserializzazione non sicura di oggetti Python | 102 | **PASS** | Assenza totale di `pickle.load` / `pickle.loads`. |
| **SQL Injection (SQLi)** | Prevenire interpolazione di stringhe in query SQL | 102 | **PASS** | Nessun uso di `f-string`, `.format()` o concatenazione in `sqlalchemy.text()`. Tutte le query usano parametri legati (`:param`). |
| **Bypass TLS / SSL** | Evitare disabilitazione della verifica dei certificati | 102 | **PASS** | Nessun parametro `verify=False` presente nelle chiamate client HTTP. |
| **Secret Scanning** | Verificare l'assenza di token o credenziali nei sorgenti | 102 | **PASS** | Zero credenziali rilevate. Le chiavi e i parametri risiedono esclusivamente in `backend/.env`. |
| **Invariante Costituzione §2.6** | Verificare il divieto assoluto di commit nei service | 7 (`service.py`) | **PASS** | Zero chiamate `session.commit()` nei service. Commit demandati esclusivamente a router e worker. |
| **CORS Policy & Wildcards** | Evitare wildcard su endpoint che usano credenziali | 102 | **PASS** | Nessun endpoint espone `allow_origins=['*']` in combinazione con cookie o sessioni. |
| **Header Difensivi su Errori** | Garantire `Cache-Control: no-store` su risposte di errore | `app/main.py` | **PASS** | Risposte 401, 403 e 429 configurate per impedire il caching di dati o stati transitori. |
| **Ordine Catena Middleware** | Assicurare che il DoS shield sia il middleware più esterno | `app/main.py` | **PASS** | `LimiteRichiesta` montato per intercettare il payload prima di qualsiasi parsing o correlazione. |
| **Magic Bytes Verification** | Verifica binaria reale dei file caricati (anti-spoofing) | `app/adapters/archivio/` | **PASS** | Implementato in `ArchivioAdapter.valida_magic_bytes` per formati JPEG (`\xff\xd8\xff`), PNG (`\x89PNG\r\n\x1a\n`) e WEBP (`RIFF...WEBP`). |
| **Path Traversal Guards** | Prevenire accesso arbitrario al file system (CWE-22) | `app/adapters/archivio/` | **PASS** | Uso di whitelist estensioni normalizzate, divieto caratteri speciali (`CARATTERI_VIETATI_NEL_NOME`) e nomi generati via `uuid.uuid4().hex`. |
| **Anti-DoS Limite Dimensioni** | Bloccare payload massivi prima della scrittura | `app/adapters/archivio/` | **PASS** | Costante vincolante `DIMENSIONE_MAX_BYTE = 10 * 1024 * 1024` verificata preventivamente. |
| **Audit Dipendenze (OSV)** | Rilevare vulnerabilità note (CVE) in `requirements.txt` | `backend/requirements.txt` | **INFO** | Tutte le versioni sono bloccate con pin esatto. Rilevati advisory storici noti per `pillow 12.3.0` e `black 23.3.0`, già presi in carico dal team nel task comune `T5-133` (Sprint 5). |

---

## 4. Risultati DAST (Dynamic Application Security Testing)

I probe dinamici hanno sollecitato i middleware e gli endpoint dell'applicazione con casi limite, payload degradati, tentativi di attacco e sequenze di fuzzing.

### Tabella dei Probe Dinamici (Round 1 & Round 2)

| # | Probe DAST | Metodo & Rotta Sollecitata | Payload / Condizione | Codice Risposta | Esito | Dettaglio Comportamento |
|:---:|---|---|---|:---:|:---:|---|
| **1** | **Rotte Protette: Accesso Anonimo** | `GET /api/auth/me`<br>`GET /api/campagne`<br>`GET /api/profilo`<br>`GET /api/da-approvare`<br>`GET /api/foto/1/file`<br>`POST /api/campagne/1/approva` | Client privo di sessione o cookie non valido | `401 Unauthorized` | **PASS** | Rigetto immediato; header `Cache-Control: no-store`; presenza dell'header `X-Request-ID`; nessun cookie rilasciato (`Set-Cookie` assente). Emesso log di sicurezza `invalid_session`. |
| **2** | **Endpoint Pubblici Legittimi** | `GET /api/health`<br>`GET /api/consorzio` | Accesso anonimo standard | `200 OK` | **PASS** | Risposta conforme; nessun leak di stato interno o dati sensibili. |
| **3** | **Firma Foto Pubblica: Manomissione** | `GET /api/foto/1/pubblica?canale=instagram&firma=1_firma-manomessa` | Firma crittografica HMAC alterata | `404 Not Found` | **PASS** | Rifiuto con messaggio `{"detail": "Foto non trovata."}`, prevenendo l'enumerazione e senza rivelare l'esistenza o il percorso del file originale. |
| **4** | **Directory Traversal Dinamico** | `GET /api/foto/..%2f..%2fetc%2fpasswd/pubblica` | Sequenza con codifica URL di directory climbing | `404 Not Found` / `422` | **PASS** | Richiesta neutralizzata a livello di routing/validatore di tipo intero per l'ID risorsa. |
| **5** | **Anti-DoS: Body HTTP Sovradimensionato** | `POST /api/auth/login` | Body di dimensione superiore a 12 MB (soglia `richiesta_max_byte`) | `413 Payload Too Large` | **PASS** | Il middleware `LimiteRichiesta` intercetta e tronca la connessione prima del parsing JSON, proteggendo il server dall'esaurimento di memoria (OOM). |
| **6** | **Fuzzing & Payload JSON Malformato** | `POST /api/auth/login` | Payload JSON sintatticamente non valido (`{malformed json:::}`) | `422 Unprocessable Entity` | **PASS** | Risposta strutturata in lingua italiana conforme allo standard di errore del progetto (`dati_non_validi`). Zero eccezioni non gestite `500`. Generato evento `auth_invalid_input`. |
| **7** | **Prevenzione Information Disclosure** | Intercettazione risposte d'errore applicative | Risposte di errore a input anomali | `401` / `404` / `422` | **PASS** | Verificata l'assenza totale di traceback Python, stringhe di connessione a PostgreSQL (`postgresql://`), percorsi del filesystem locale o riferimenti ad ambienti interni. |
| **8** | **Rotta Inesistente / Probing Arbitrario** | `GET /api/endpoint-completamente-inesistente` | Richiesta a URI non mappato | `404 Not Found` | **PASS** | Gestito pulitamente senza leak di directory interne o stacktrace. |
| **9** | **Metodo HTTP Non Consentito** | `DELETE /api/campagne` | Metodo non supportato sulla risorsa | `405 Method Not Allowed` | **PASS** | Rigettato a livello di router FastAPI; nessuna esecuzione non prevista. |
| **10** | **Fuzzing Campi Estremi** | `POST /api/auth/login` | JSON con stringhe di 10.000 caratteri | `422 Unprocessable Entity` | **PASS** | Pydantic valida ed espelle l'input anomalo senza crash `500` né blocchi di memoria. |
| **11** | **Content-Type Incompatibile** | `POST /api/auth/login` | Header `Content-Type: text/plain` su endpoint JSON | `422 Unprocessable Entity` | **PASS** | Rifiuto della deserializzazione non conforme; nessuna lettura parziale del payload. |
| **12** | **Tracciabilità & Correlazione Richieste** | `GET /api/campagne` (anonimo) | Richiesta priva di auth | `401 Unauthorized` | **PASS** | Generazione e rilascio garantito di `X-Request-ID` univoco per il tracciamento distribuito. |
| **13** | **Shield Dinamico Anti-Brute Force** | `POST /api/auth/login` | Tentativi di login errati ripetuti | `401` → `429 Too Many Requests` | **PASS** | Al superamento della soglia (5 tentativi) scatta il rate-limiting persistente con codice `429`, evento `login_rate_limited` e header `Retry-After`. |

---

## 5. Dettaglio della Suite di Test Pytest di Sicurezza

Tutti i test automatici specificamente concepiti per validare i requisiti di sicurezza applicativa sono stati eseguiti con successo:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\widows X\Desktop\Progetto Adflow Suite\adflow-suite\backend
configfile: pytest.ini

tests\adapters\archivio\test_archivio.py ..................              [ 18 passed ]
tests\moduli\campagne\test_sistemazione_foto.py ................         [ 16 passed ]
tests\moduli\campagne\test_foto_pubblica.py ....................         [ 20 passed ]
tests\test_limite_richiesta.py ......                                    [  6 passed ]
tests\moduli\accesso\test_login_sicurezza.py ...................         [ 19 passed ]
tests\test_security.py ....................                              [ 20 passed ]

============================= 99 passed in 65.50s =============================
```

### Sintesi delle Aree Collaudate
- **Adattatore Archivio (`test_archivio.py` - 18 test)**: Convalida del limite di 10 MB per file, whitelist rigorosa estensioni `.jpg`, `.jpeg`, `.png`, `.webp`, verifica magic bytes reali per ciascun formato, eliminazione atomica concorrente sicura contro condizioni di TOCTOU, sanitizzazione percorsi contro CWE-22, isolamento totale dello stato tramite context manager `usa_archivio`.
- **Sistemazione Foto (`test_sistemazione_foto.py` - 16 test)**: Rimozione garantita dei metadati EXIF e coordinate GPS dai file immagine pubblicati, proporzioni conformi (lato corto 1080 px), salvataggio su file derivato nel rispetto dell'Invariante di Costituzione §1.3 (il file originale caricato dall'artigiano rimane intangibile e non modificabile).
- **Foto Pubblica Firmata (`test_foto_pubblica.py` - 20 test)**: Convalida crittografica HMAC-SHA256 con timestamp di scadenza, rigetto immediato di firme contraffatte, firme scadute o canali social non ammessi; assenza di cookie o sessioni nella risposta anonima.
- **Limite Richiesta (`test_limite_richiesta.py` - 6 test)**: Protezione da streaming massivi di byte senza `Content-Length` o con `Content-Length` eccedente; emissione dell'header `X-Request-ID` anche sulle risposte 413.
- **Login e Sicurezza Credenziali (`test_login_sicurezza.py` - 19 test)**: Resistenza ad attacchi a forza bruta su IP e account, indistinguibilità dei tempi di risposta tra utente esistente con password errata e utente inesistente (prevenzione enumerazione account), persistenza del blocco su database relazionale con calcolo esatto del tempo residuo (`Retry-After`).
- **Funzioni Crittografiche Core (`test_security.py` - 20 test)**: Hashing delle password con algoritmo `scrypt`, generazione di token crittografici sicuri con `secrets`, cifratura e decifratura simmetrica dei token social con Fernet/AES.

---

## 6. Evidenza di Allineamento con `origin/main` (Task T3-09 & Sprint Successivi)

Dal confronto con il repository remoto condiviso (`origin/main`, attualmente 146 commit avanti rispetto alla base del branch locale `feature/avvia-server-e-logging`):

1. **Stato del Codice Python**:
   - Eseguendo la suite di analisi AST canonica di T3-09 (`test_sast_security.py`) sul nostro codice sorgente locale, **tutti i test di assenza di primitive pericolose e conformità sintattica risultano VERDI**.
2. **Componenti Introdotti su `origin/main` da T3-09**:
   - `app/core/protezione_csrf.py`: Middleware Starlette per la validazione dell'header `Origin` sulle richieste che mutano stato (`POST`, `PUT`, `PATCH`, `DELETE`).
   - `app/core/log_jsonl.py`: Gestore di log strutturati con redazione automatica di credenziali, token e stringhe di connessione al database.
   - `app/core/tracciamento_richieste.py`: Tracciamento del ciclo di vita delle richieste HTTP senza registrazione di body, query string o header sensibili.
   - Validatore Pydantic in `app/core/config.py`: Convalida che in ambiente di produzione `FOTO_URL_PUBBLICO` sia un URL HTTPS sintatticamente valido.
3. **Pianificazione dell'Integrazione**:
   - Questi componenti verranno ereditati in modo trasparente dal branch non appena sarà effettuato il normale riallineamento da `main` (`git fetch origin && git merge origin/main`), completando la catena di middleware in produzione senza impattare il codice della Corsia 2.

---

## 7. Raccomandazioni per il Deployment e i Passi Successivi

In base alle evidenze raccolte, si confermano le seguenti linee guida per i colleghi e per le fasi di staging:

1. **Proxy Inverso e Confini di Rete (Follow-up #17)**:
   - In ambiente di staging/produzione, garantire che il backend sia raggiungibile esclusivamente tramite il reverse proxy fidato (Nginx/Traefik).
   - Configurare l'inoltro degli header (`X-Forwarded-For`, `X-Forwarded-Proto`, `Host`) con validazione degli IP fidati del proxy, evitando configurazioni permissive (`--forwarded-allow-ips '*'`).
2. **Terminazione TLS e Cookie di Sessione**:
   - Mantenere attivo il controllo `COOKIE_SECURE=True` per imporre l'attributo `Secure` su tutti i cookie di sessione in ambiente di produzione.
   - Forzare l'uso di HTTPS su tutte le connessioni esterne e convalidare che `FOTO_URL_PUBBLICO` inizi con `https://`.
3. **Gestione del Log Retention**:
   - I log strutturati JSON emessi dagli eventi di sicurezza (`eventi_sicurezza.py`) contengono identificativi opachi di correlazione (`request_id`) e tipologia evento (`invalid_session`, `auth_invalid_input`, `login_rate_limited`), senza dati personali (PII) né credenziali in chiaro. Mantenere questo standard su tutte le nuove implementazioni.
4. **Allineamento Dipendenze (Task T5-133)**:
   - Coordinare con il referente dei file comuni l'aggiornamento di `pillow` alla versione patch successiva non appena validata nella suite di regressione generale dello Sprint 5.

---

*Documento redatto e aggiornato in conformità con le Regole Inviolabili del Progetto Locale (Silvia) e la Costituzione di AdFlow Suite.*
