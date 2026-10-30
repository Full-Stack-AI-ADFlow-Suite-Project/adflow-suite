# Sicurezza dell'accesso · procedura operativa

Cosa fa il codice per proteggere l'accesso e cosa deve fare chi installa AdFlow in un ambiente reale. Le regole di sicurezza del progetto sono in `docs/agenti/constitution.md` §3; qui c'è il dettaglio operativo (issue #16–19). La storia delle PR che l'hanno costruito è in `docs/archivio/novita/` e in git.

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
  }
  ```

**Prova locale con TLS e proxy (issue #17, parte locale chiusa).** `tests/moduli/accesso/test_proxy_http_reale.py` prova in locale HTTPS con certificato X.509 verificato, un proxy TLS temporaneo e un processo Uvicorn separato (`--proxy-headers --forwarded-allow-ips 127.0.0.1`), verificando: cookie `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/` e assenza di `Domain` al login e al logout; sovrascrittura degli header contraffatti (`X-Forwarded-Proto`, `X-Forwarded-For`, `X-Request-ID`); rifiuto degli header inoltrati quando la richiesta arriva da un indirizzo non fidato (`192.0.2.1`). Evidenza registrata in `qa/issue-17/README.md` (senza cookie, credenziali o chiavi private). Per un futuro ambiente di staging pubblico si ripete la stessa verifica sul reverse proxy esterno.

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
