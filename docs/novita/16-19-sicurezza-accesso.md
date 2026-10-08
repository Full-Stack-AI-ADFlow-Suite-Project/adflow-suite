# Follow-up #16–19 · sicurezza dell'accesso

Implementazione richiesta da Gianluca dopo l'apertura delle issue; comprende
la corsia 0 (configurazione, composizione, tabella e migrazione) e la corsia 1
(accesso). T1-11, T1-12 e T1-13 sono integrati in `main` tramite le PR #28 e #30
(la #31 era stata unita nel branch della #30). La PR #36 si appoggia a `main`
e sostituisce la #21, chiusa senza merge dopo l'eliminazione della vecchia base.
Le parti comuni richiedono la revisione
di tutto il team; il merge resta all'admin. Nessun nuovo servizio.

## #16 · contatori condivisi PostgreSQL

La migrazione 009 crea `limite_login`. Sono due limiti indipendenti: IP e
identità dell'account. Cinque richieste per ciascuno in una finestra di 900 secondi
a partire dal primo tentativo. I valori sono configurabili in `.env` mediante
`LOGIN_LIMITE_TENTATIVI` e `LOGIN_FINESTRA_SECONDI`. Anche un accesso riuscito
consuma un tentativo; un blocco non revoca le sessioni già valide. I payload
malformati consumano il limite IP prima della validazione. Gli header inoltrati
si accettano solo attraverso la configurazione fidata di Uvicorn.

L'upsert PostgreSQL serializza gli incrementi concorrenti. La prenotazione usa
una transazione distinta dalla sessione di autenticazione: un 401 o rollback
del login non ripristina il contatore. I contatori sopravvivono ai riavvii e
sono condivisi tra processi/istanze. Non servono Redis o SQLite.
Login, logout e rinnovo chiudono la dipendenza database prima di inviare la risposta:
il browser riceve il cookie soltanto dopo il commit della sessione.
Il contatore satura a limite+1; un 429 restituisce `Retry-After` e `no-store`.
In caso di guasto del database il login restituisce 503, senza bypass.
La pulizia elimina al massimo 100 contatori scaduti per prenotazione; una
scadenza esatta apre una nuova finestra. Cambiare il segreto resetta le chiavi
logiche: farlo come operazione coordinata, senza lasciare istanze con segreti diversi.

Le chiavi sono HMAC-SHA256 di IP/account con un prefisso distinto; non si
salvano IP o email in chiaro. `LOGIN_LIMITE_SEGRETO` deve essere casuale,
almeno 32 caratteri, custodito in `.env` e uguale su tutte le istanze.
La modalità produzione rifiuta il valore finto. Le chiavi sono pseudonimi, non
dati anonimi: permettono correlazione e, con il segreto, verifica degli identificatori.

## #17 · cookie e proxy

`AMBIENTE=produzione` rende i cookie Secure al login, al rinnovo e alla cancellazione anche
se il backend riceve HTTP dal proxy. Rifiuta `COOKIE_SECURE=false`. In sviluppo
il valore opzionale può essere impostato; altrimenti segue lo schema percepito.
Il router non interpreta direttamente `X-Forwarded-Proto`.

Esempio per un proxy già presente sulla stessa macchina (sostituire la topologia
con quella reale prima del deploy), avvio da `backend/`:

```sh
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log
```

Non usare `--forwarded-allow-ips '*'`. Se il proxy è remoto, consentire solo
gli indirizzi/reti effettivi e impedire l'accesso diretto al backend tramite
rete/firewall. Il proxy termina TLS con un certificato valido, forza HTTPS
e sovrascrive gli header ricevuti dal client. Per Nginx già disponibile:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    access_log off;
}
```

La suite prova realmente un client HTTPS con certificato verificato, un proxy
TLS temporaneo e un processo Uvicorn separato. Controlla i cookie di login/logout
e il rifiuto di uno schema contraffatto da un mittente non fidato. La configurazione
di rete e il certificato dello staging reale non sono verificabili da questa prova.
Prima del rilascio allegare alla issue #17 l'evidenza dell'ambiente reale:
HTTPS attraverso il proxy; Secure/HttpOnly/SameSite=Lax/Path=/ al login/logout;
header contraffatti sovrascritti; backend non raggiungibile direttamente.
Non inserire cookie, credenziali o certificati privati nell'evidenza.

## #18 · eventi JSON senza dati personali

Il logger `adflow.sicurezza` scrive una riga JSON su stderr a livello INFO.
Non propaga agli altri logger. I soli campi sono `security_event`, `event_type`,
`esito`, `timestamp` UTC e `request_id`. Il server genera un UUID per ogni richiesta,
restituito in `X-Request-ID`; gli ID inviati dal client sono ignorati.
Eventi distinti: `auth_failure`, `auth_invalid_input`, `invalid_session`,
`role_denied`, `login_rate_limited`, `login_limiter_unavailable`.
Non si serializzano messaggi delle eccezioni, body, URL, query, IP, email,
password, token, cookie o header ricevuti. Un guasto del sink non cambia la
semantica HTTP né concede accesso. Gli eventi riguardano richieste negate;
gli accessi riusciti non producono questo log.

Il deploy deve raccogliere stderr, definire rotazione/retention/accesso con il
team e monitorare aumenti di `auth_failure`/`login_rate_limited`, e ogni
`login_limiter_unavailable`. Nessun nuovo servizio obbligatorio. Gli eventi
sono registrati anche sotto attacco: dimensionare raccolta e rotazione senza
aggiungere identificatori personali. Disabilitare gli access log HTTP che
includono IP/query, come nell'esempio Uvicorn. La mappatura ai controlli ASVS/ISO
e le politiche operative richiedono il team; questi log non certificano conformità.

## #19 · email senza DNS

Nuova dipendenza: email-validator 2.3.0, licenza Unlicense, per sintassi e
normalizzazione Unicode. Dipendenze transitive: idna (BSD-3-Clause), dnspython
(ISC). Nuova dipendenza per le sole prove TLS: cryptography 50.0.2
(Apache-2.0 o BSD-3-Clause), con certificati/chiavi temporanei, senza installare
un eseguibile OpenSSL esterno. Tutte le chiamate usano `check_deliverability=False`; non si verifica
il possesso della casella. Non si cambiano ruoli o endpoint.

Le nuove creazioni normalizzano Unicode e maiuscole/minuscole e rifiutano
domini riservati/indirizzi non validi. `EMAIL_TEST_ENVIRONMENT=true` permette
le fixture `.test` solo fuori produzione; i test lo impostano temporaneamente.
Il login cerca sia la forma normalizzata sia quella storica, mantenendo gli
account già creati. Se la nuova politica rifiuta un vecchio indirizzo, il login
usa la precedente identità senza permettere nuove creazioni analoghe.
La creazione confronta le identità normalizzate degli indirizzi esistenti,
anche Unicode storici, senza modificarli; questo controllo richiede una scansione
degli indirizzi alla creazione (non a ogni login). Il vincolo unico risolve
anche creazioni concorrenti della stessa nuova identità normalizzata.
Identità ambigue continuano a essere rifiutate; nessuna correzione automatica
dei dati. Eventuali collisioni Unicode nei dati storici vanno revisionate dal
team prima di interventi sui record.

## Verifica e stato

Test su PostgreSQL `adflow_test`: limite esatto, scadenza, 8/20 richieste
concorrenti, sei processi indipendenti, rate limit su IP/account, payload
malformati, successo e sessioni esistenti, guasti del DB/logger, contenuto JSON
reale senza PII, proxy fidati/non fidati, TLS reale, Unicode e account storici.
Provati upgrade/downgrade completo e 009→008→009, inclusa coerenza dei modelli.
Nessuna migrazione eseguita sul database applicativo.

Le issue restano aperte fino alla revisione/merge. #17 richiede inoltre la prova
dello staging reale. I responsabili del deploy/logging e le policy operative
devono essere confermati dal team; non sono stati inventati assegnatari GitHub.


## Riallineamento al modello corrente

La revisione dei contatori è 009, dopo 008_riallineamento. La PR #36 si appoggia a `main`, dove T1-12 e T1-13 sono entrati con il merge della #30 e T1-14 con la #33, conservando sessioni per ruolo, rinnovo sliding e cambio password con revoca. La stessa politica Secure protegge login, logout e rinnovo. I nuovi test dell'accesso verificano anche GET /canali e le API di revisione T1-42 con login reale, admin/operatore/artigiano, logout e scadenza. Il riesame comprende anche il codice di pubblicazione T1-43 integrato con la #35. Lo staging non è ancora predisposto: la prova locale non chiude #17; il team deploy deve predisporlo e allegare l'evidenza reale.
