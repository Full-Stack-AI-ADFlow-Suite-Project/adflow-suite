# T4-107 · Checklist OWASP ASVS 5.0, livello 2

Requisiti rappresentativi per i capitoli che riguardano l'MVP, con la prova
(file, test o report) e l'esito. Ciò che in locale non si può provare è
`non provato`, con il motivo. L'elenco completo dell'ASVS è più ampio: questa
è la parte selezionata per l'app e le sue superfici (API + frontend + worker).

Legenda: ✅ soddisfatto · ❌ non soddisfatto (rilievo) · ❔ non provato.

## V1 · Codifica e sanitizzazione

| Requisito (sostanza) | Prova | Esito |
|---|---|---|
| Output codificato secondo il contesto (HTML/JSON) | React/Mantine con escaping predefinito; nessun `dangerouslySetInnerHTML` in `frontend/src` (ricerca) | ✅ |
| Nessuna esecuzione di codice dinamico (eval, pickle, shell) | `bandit -ll` 0 risultati (T4-101); test SAST sul sorgente (`test_sast_security.py`) | ✅ |
| Sanitizzazione dei parametri SQL | SQLAlchemy con parametri; nessuna SQL interpolata (`test_sast_security.py` cerca le interpolazioni) | ✅ |

## V2 · Validazione e logica di business

| Requisito | Prova | Esito |
|---|---|---|
| Validazione sul server di tutti gli input | 57 operazioni della matrice, 422 sui dati invalidi (T4-102) | ✅ |
| Limiti di grandezza e di formato | upload 10 MB/lato corto 1080 px, richiesta 12 MB, validatore R-09 (T4-102) | ✅ |
| Protezione dalla logica forzata (stati) | macchine a stati e invarianti (T4-104) | ✅ |
| Input estremi respinti con 4xx | input oltre `int4` e `tipo` non ammesso danno **500** | ❌ RL-026 |

## V3 · Sicurezza del frontend

| Requisito | Prova | Esito |
|---|---|---|
| Intestazioni di sicurezza (CSP, nosniff, referrer) | solo `nosniff` sui file foto | ❌ RL-015 |
| Nessun segreto nel bundle | ricerca nel build: nessuna chiave; il frontend chiama solo `/api` | ✅ |
| Accessibilità e contrasto (WCAG AA) | axe: 4 violazioni serie (T4-106) | ❌ RL-035 |

## V4 · API e servizi web

| Requisito | Prova | Esito |
|---|---|---|
| Schema documentato | OpenAPI generato; contratto TypeScript verificato (T4-106) | ✅ |
| Autorizzazione per operazione | matrice 57 × 5 (T4-102) | ✅ |
| Limite di frequenza sulle operazioni sensibili | solo il login (`limite_login`); le azioni AI no | ❌ RL-018 |
| Errori senza dettagli interni | `{"detail": "…"}` in italiano; 500 dal gestore generico in casi estremi | ❌ RL-026 (parziale) |

## V5 · Gestione dei file

| Requisito | Prova | Esito |
|---|---|---|
| Tipo reale controllato (non l'estensione) | magic bytes; HEIC rinominato → 422 (T4-102) | ✅ |
| Limiti di peso e dimensioni | 10 MB, lato corto ≥ 1080 px; bombe → 422 | ✅ |
| Nome del file generato dal server | `uuid` lato server; il nome originale non arriva al disco | ✅ |
| Metadati rimossi dalle copie pubbliche | EXIF e GPS tolte dalla copia sistemata; originale intatto (T4-104) | ✅ |
| File serviti con tipo corretto e nosniff | `image/jpeg` + `nosniff` sui file foto | ✅ |

## V6 · Autenticazione

| Requisito | Prova | Esito |
|---|---|---|
| Password con hashing lento e salt | scrypt e salt da `secrets` | ✅ |
| Limite dei tentativi | `limite_login` su PostgreSQL, per account e IP | ✅ |
| Nessun recupero insicuro della password | nessun recupero per email; password provvisoria (R-37) | ✅ |
| Errori di accesso indistinguibili | `CA-02` | ✅ |

## V7 · Gestione delle sessioni

| Requisito | Prova | Esito |
|---|---|---|
| Cookie httpOnly, Secure in produzione, SameSite | test login reale e proxy TLS (`test_auth_http_reale.py`, `test_proxy_http_reale.py`) | ✅ |
| Scadenza per inattività | R-29, `CA-62` | ✅ |
| Logout che invalida la sessione | `test_auth_http_reale.py` | ✅ |
| Protezione CSRF sulle operazioni con stato | `ProtezioneCSRF` in produzione; `test_origine.py` | ✅ (solo in produzione, RL-016) |

## V8 · Autorizzazione

| Requisito | Prova | Esito |
|---|---|---|
| Autorizzazione sul server a ogni richiesta | matrice completa (T4-102) | ✅ |
| Nessun accesso a oggetti di un altro utente (BOLA) | 404 su tutte le operazioni con id; test BOLA (T4-102) | ✅ |
| Ruoli senza escalation | admin = operatore, mai artigiano | ✅ |

## V11 · Crittografia

| Requisito | Prova | Esito |
|---|---|---|
| Primitive standard, nessuna invenzione | `hashlib`/`hmac`, `compare_digest`, scrypt | ✅ |
| Firma a tempo con confronto a tempo costante | `foto_pubblica` (T4-102) | ✅ |
| Segreti da configurazione, non dal codice | `.env` 600, `.env.example` finto | ✅ |

## V12 · Comunicazione sicura

| Requisito | Prova | Esito |
|---|---|---|
| HTTPS e HSTS | il proxy TLS è provato in locale; HSTS manca; staging pubblico non provato | ❌ RL-015 / ❔ RL-033 |
| `--forwarded-allow-ips` non a `*` | `docs/sicurezza-accesso.md` (127.0.0.1), test proxy | ✅ |

## V13 · Configurazione

| Requisito | Prova | Esito |
|---|---|---|
| Nessuna credenziale predefinita | seed chiede la password; `.env.example` con valori finti | ✅ |
| Configurazione di produzione validata | `Impostazioni` rifiuta segreti deboli, orologio spostato, foto URL non https | ✅ |
| Intestazioni e metodi non necessari spenti | TRACE → 405 (schemathesis) | ✅ |

## V14 · Protezione dei dati

| Requisito | Prova | Esito |
|---|---|---|
| Dati personali solo dove servono | storico AI con prompt e risposte, senza conservazione | ❌ RL-019 |
| Cancellazione/anonimizzazione possibile | «niente si cancella» senza procedura | ❌ RL-041 |
| Dati sensibili cifrati | permessi social non cifrati (fuori MVP; prerequisito) | ❔ RL-039 |

## V15 · Codice sicuro e architettura

| Requisito | Prova | Esito |
|---|---|---|
| Confini tra moduli controllati | `test_confini.py` | ✅ |
| Dipendenze note e aggiornate | pip-audit: pillow 39 vulnerabilità (3 critiche) | ❌ RL-004 |
| Librerie dichiarate | `httpx` non dichiarato | ❌ RL-001 |
| Mutazioni coperte | 323/396 mutanti uccisi; 56 sopravvissuti analizzati | ❌ RL-030 (qualità dei test) |
| Analisi statica | bandit 0; semgrep 0; mypy 83 errori | ✅ (mypy: RL-008) |

## V16 · Log e gestione degli errori

| Requisito | Prova | Esito |
|---|---|---|
| Nessun dato personale o segreto nei log | prova con valori riconoscibili (T4-107-log-segreti) | ✅ |
| Eventi di sicurezza | `adflow.sicurezza` con tipi definiti | ✅ |
| Errori senza stack trace al client | gestore errori con `{"detail"}`; 500 generico senza dettagli | ✅ |
| Log resistenti alla manomissione e conservati | file su stderr, rotazione non definita | ❔ |

## V17 · Altro

| Requisito | Prova | Esito |
|---|---|---|
| Upload senza elaborazione pericolosa (immagini) | Pillow con limiti di pixel; vulnerabilità note del decodificatore | ❌ RL-004 |
| Backup e ripristino | provati e cronometrati (T4-105) | ✅ |
| Rilascio riproducibile e rollback | nessun artefatto di rilascio | ❌ RL-032 |

## Sintesi

- **Soddisfatti**: validazione e autorizzazione (V2, V4, V8), file (V5),
  autenticazione e sessioni (V6, V7), crittografia (V11), configurazione
  (V13), log (V16 nella parte applicativa).
- **Non soddisfatti**: intestazioni e accessibilità (V3), limite delle azioni
  AI e input estremi (V2/V4), dipendenze (V15), dati personali (V14),
  pubblicazione idempotente (V16/§8, RL-025).
- **Non provati**: staging pubblico (RL-033), rotazione dei log, cifratura dei
  token social (fuori MVP).
- Nessun requisito L2 dell'ASVS è risultato **non verificabile per mancanza di
  codice**: i ❔ sono prove esterne (staging, hosting) o fuori perimetro.
