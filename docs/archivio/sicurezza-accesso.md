# Sicurezza · procedura operativa e interventi aperti

Cosa fa il codice per proteggere l'accesso, cosa deve fare chi installa AdFlow in un ambiente reale e che cosa manca prima di esporlo al pubblico con dati veri (ultima sezione). Le regole di sicurezza del progetto sono in `docs/agenti/constitution.md` §3; qui c'è il dettaglio operativo (issue #16–19). La storia delle PR che l'hanno costruito è in `docs/archivio/novita/` e in git; la valutazione completa del 30/10/2026, da cui viene l'ultima sezione, è in `docs/archivio/valutazione-sicurezza.md`; l'esito della simulazione di accettazione è in `docs/accettazione.md`, i suoi rilievi RL-xxx in `docs/archivio/accettazione/rilievi.md`.

## In produzione, prima dell'avvio

1. `uv run alembic upgrade head` (la migrazione 009 crea i contatori dei tentativi di accesso).
2. In `backend/.env`:
   - `AMBIENTE=produzione`;
   - `LOGIN_LIMITE_SEGRETO` casuale, di almeno 32 caratteri, uguale su tutte le istanze (mai il valore finto di `.env.example`: in produzione l'applicazione lo rifiuta);
   - `EMAIL_TEST_ENVIRONMENT=false`;
   - `OROLOGIO_GIORNI_AVANTI=0` (con un altro valore l'applicazione non parte).
3. Uvicorn dietro un proxy che termina HTTPS (vedi sotto), con gli access log spenti.
4. Raccolta di stderr per gli eventi di sicurezza, con rotazione, conservazione e accessi decisi dal team.

## Limite dei tentativi di accesso

- Due limiti indipendenti, per IP e per account: **5** richieste ciascuno in una finestra di **900** secondi dal primo tentativo (`LOGIN_LIMITE_TENTATIVI`, `LOGIN_FINESTRA_SECONDI`). Anche un accesso riuscito consuma un tentativo; un blocco non revoca le sessioni già valide; i dati malformati consumano il limite per IP prima della validazione.
- Oltre il limite: **429** con `Retry-After` e `Cache-Control: no-store`. Se il database non risponde il login dà **503**, senza scorciatoie.
- I contatori stanno in PostgreSQL (tabella `limite_login`): sopravvivono ai riavvii e valgono per tutti i processi e le istanze, senza Redis. Il conteggio usa una transazione separata dal login: un 401 non lo azzera.
- Le chiavi sono HMAC-SHA256 di IP e account con `LOGIN_LIMITE_SEGRETO`: né IP né email si salvano in chiaro, ma restano pseudonimi (con il segreto si possono verificare). Cambiare il segreto azzera i contatori: si fa su tutte le istanze insieme.
- Login, logout e rinnovo salvano la sessione prima di mandare il cookie.
- `LOGIN_LIMITE_SEGRETO` firma anche gli indirizzi pubblici delle foto (`GET /foto/{id}/pubblica`, plan §3): la chiave è derivata dal segreto con una separazione di dominio, quindi non coincide con quella dei contatori. Cambiare il segreto invalida anche gli indirizzi già dati a Instagram e le foto di una pubblicazione in corso non si scaricano più: si cambia a pubblicazioni ferme, su tutte le istanze insieme.

## Cookie e proxy

- Il cookie `adflow_sessione` è httpOnly, `SameSite=Lax`, `Path=/`. Con `AMBIENTE=produzione` è sempre Secure (login, rinnovo e cancellazione), anche se il proxy parla HTTP con il backend; `COOKIE_SECURE=false` è rifiutato. In sviluppo `COOKIE_SECURE` è facoltativo e segue lo schema della richiesta.
- Uvicorn accetta gli header inoltrati solo dal proxy fidato. Esempio con il proxy sulla stessa macchina, da `backend/`:

  ```sh
  uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log
  ```

  Mai `--forwarded-allow-ips '*'`. Con un proxy remoto si ammettono solo i suoi indirizzi e il backend non deve essere raggiungibile direttamente (rete o firewall).
- Il proxy termina TLS con un certificato valido, forza HTTPS e sovrascrive gli header del client. Per Nginx:

  ```nginx
  location /api/ {
      proxy_pass http://127.0.0.1:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_set_header X-Forwarded-For $remote_addr;
      access_log off;
      # RL-015: le cinque intestazioni di sicurezza solo sull'API. Il backend
      # le manda già (core/intestazioni_sicurezza.py): qui si nascondono e si
      # ridicono, per non farle arrivare doppie, e "always" le tiene anche
      # sulle risposte di errore.
      proxy_hide_header Content-Security-Policy;
      proxy_hide_header Strict-Transport-Security;
      proxy_hide_header X-Content-Type-Options;
      proxy_hide_header Referrer-Policy;
      proxy_hide_header X-Frame-Options;
      add_header Content-Security-Policy "default-src 'none'; frame-ancestors 'none'" always;
      add_header Strict-Transport-Security "max-age=31536000" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header Referrer-Policy "no-referrer" always;
      add_header X-Frame-Options "DENY" always;
  }
  ```

  Fuori da `/api/` nessuna di queste intestazioni: una CSP così stretta romperebbe `/docs` e il frontend, che prende le sue da sé.

**Prova locale con TLS e proxy (issue #17, parte locale chiusa).** `tests/moduli/accesso/test_proxy_http_reale.py` prova in locale HTTPS con certificato X.509 verificato, un proxy TLS temporaneo e un processo Uvicorn separato (`--proxy-headers --forwarded-allow-ips 127.0.0.1`), verificando: cookie `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/` e assenza di `Domain` al login e al logout; sovrascrittura degli header contraffatti (`X-Forwarded-Proto`, `X-Forwarded-For`, `X-Request-ID`); rifiuto degli header inoltrati quando la richiesta arriva da un indirizzo non fidato (`192.0.2.1`). Evidenza registrata in `docs/archivio/qa/issue-17/README.md` (senza cookie, credenziali o chiavi private). Per un futuro ambiente di staging pubblico si ripete la stessa verifica sul reverse proxy esterno.

## Eventi di sicurezza

- Il logger `adflow.sicurezza` scrive una riga JSON su stderr (livello INFO) e non propaga agli altri logger. Campi: `security_event`, `event_type`, `esito`, `timestamp` (UTC), `request_id`.
- Eventi: `auth_failure`, `auth_invalid_input`, `invalid_session`, `role_denied`, `login_rate_limited`, `login_limiter_unavailable`. Gli accessi riusciti non producono eventi.
- Ogni richiesta ha un `X-Request-ID` generato dal server; quelli mandati dal client si ignorano.
- Mai nei log: messaggi delle eccezioni, corpo, URL, query, IP, email, password, token, cookie, header ricevuti. Un guasto del logger non cambia le risposte né apre l'accesso.
- Da monitorare: aumenti di `auth_failure` e `login_rate_limited`, ogni `login_limiter_unavailable`. Questi log non certificano la conformità a ASVS o ISO: le politiche le decide il team.

## Email degli utenti

- Le email si controllano con email-validator, senza DNS (`check_deliverability=False`): sintassi e normalizzazione Unicode e maiuscole; non si verifica il possesso della casella.
- Una creazione rifiuta domini riservati e indirizzi non validi e confronta l'identità normalizzata con quelle esistenti; il vincolo unico copre anche le creazioni concorrenti. Le identità ambigue si rifiutano, senza correggere i dati.
- Il login trova sia la forma normalizzata sia quella storica: gli account già creati continuano a entrare.
- `EMAIL_TEST_ENVIRONMENT=true` ammette gli indirizzi `.test` solo fuori produzione (i test lo usano).

## Come si prova

I test girano su `adflow_test`, con host `localhost` o `127.0.0.1` e porta 5432, e controllano `current_database()` nei processi che aprono connessioni: mai sul database dell'applicazione. Coprono il limite esatto e la scadenza, richieste concorrenti e processi indipendenti, i guasti del database e del logger, il contenuto JSON senza dati personali, proxy fidati e non fidati, TLS reale, email Unicode e account storici. `cryptography` serve solo a queste prove, per generare certificati temporanei.

## Prima di un'esposizione pubblica

Riassunto degli interventi ancora aperti della valutazione del 30/10/2026 (testo integrale, con i criteri di completamento, in `docs/archivio/valutazione-sicurezza.md`). Già fatti e quindi tolti da qui: controllo di `Origin` sulle richieste mutanti in produzione, validazione HTTPS di `FOTO_URL_PUBBLICO`, probe SAST/DAST locali in CI. Ciò che cambia il perimetro (MFA, recupero password, tetto di spesa AI) va prima concordato: questa lista non autorizza a toccare il codice congelato.

- **TLS, proxy e rete** (issue #17, RL-033): ripetere su uno staging vero la prova locale di sopra; backend raggiungibile solo dal proxy; redirect HTTPS e HSTS; intestazioni di sicurezza anche sul livello che serve il frontend; access log senza query string (i link firmati delle foto).
- **Segreti**: `LOGIN_LIMITE_SEGRETO`, `META_TOKEN_PAGINA` e `OPENAI_API_KEY` in un secret manager; procedura di rotazione e revoca coordinata tra le istanze; token Meta con i permessi minimi; utente del database dedicato con privilegi minimi e TLS verso il database se non è locale; permessi su archivio foto, configurazione e backup cifrati, con un ripristino provato.
- **CSRF e CORS**: provare il caso di un sottodominio non autorizzato; API same-origin, oppure una allowlist esatta senza credenziali per origini arbitrarie.
- **Sessioni**: MFA almeno per `operatore` e `admin`; durata massima assoluta oltre al timeout d'inattività; revoca di tutte le sessioni di un utente; reset della password con token monouso (task a parte).
- **Abuso e spesa**: rate limit per endpoint e per utente su upload, rigenerazioni e job; limiti di concorrenza; budget, allarmi e interruttore sul provider AI; limiti di frequenza al proxy sulle foto pubbliche, senza bloccare Meta; limite del body anche nel proxy.
- **Foto firmate**: chiave dedicata, distinta da quella dei contatori; durata minima utile a Meta e cache allineata alla scadenza; mai URL firmati in log, errori o referrer.
- **Log e incidenti**: raccolta centralizzata con accesso ristretto e allarmi; eventi anche per utenti, ruoli, approvazioni e pubblicazioni; una procedura di risposta agli incidenti (revoca token, invalidazione sessioni, rotazione segreti).
- **Dipendenze e CI**: aggiornamenti automatici (Dependabot o simili), lock delle dipendenze transitive (RL-001/002), scansione dei segreti, `GITHUB_TOKEN` con i permessi minimi e Actions fissate a uno SHA; pillow da aggiornare (RL-004).
- **Dati personali e provider** (RL-040…RL-044): inventario dei dati, che cosa va al provider AI e con che conservazione, retention e cancellazione di database, foto, backup e log.

La valutazione si rilancia da `backend/`, solo su `adflow_test` locale (la suite ricrea lo schema; il log JSONL va in `backend/security-assessment-logs/`, ignorato da git):

```powershell
uv run python scripts/esegui_valutazione_sicurezza.py --security-only
uv run python scripts/esegui_valutazione_sicurezza.py
```
