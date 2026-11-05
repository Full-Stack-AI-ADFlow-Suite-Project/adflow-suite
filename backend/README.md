# AdFlow Suite · Backend

Monolite a moduli (FastAPI, SQLAlchemy 2 + Alembic, PostgreSQL 16) più un worker Procrastinate con la coda dentro PostgreSQL; AI con LiteLLM, social con l'API di Meta, entrambi dietro un adattatore con un provider finto per sviluppo e test. Python 3.11+, versioni in `requirements.txt`, ognuna con nome, motivo e licenza. La prima installazione si fa dalla radice con `uv run python allinea.py` ([README principale](../README.md)).

## Comandi

Da questa cartella, uno alla volta:

```bash
createdb adflow                                                           # database dell'applicazione (una volta sola)
createdb adflow_test                                                      # database dei test (una volta sola)
uv run alembic upgrade head                                               # database all'ultima migrazione
uv run uvicorn app.main:app --reload                                      # API su http://localhost:8000, documentate su /docs
uv run python -m procrastinate -a app.worker.app worker --concurrency 1   # worker, con il tick di pubblicazione ogni minuto
uv run python -m app.cli seed                                             # dati di partenza
uv run pytest                                                             # test, sul database adflow_test
uv run black --check .                                                    # formattazione
```

`pytest` e `black --check`, con `alembic upgrade head`, sono i controlli che GitHub rilancia a ogni PR (`.github/workflows/backend.yml`); per il frontend `npm run lint` e `npm run build` (`frontend.yml`).

- **Database dei test.** Il nome `adflow_test` su `localhost:5432` è un vincolo (RL-012): le fixture verificano di essere collegate proprio lì, poi lo svuotano e lo riportano all'ultima migrazione a ogni esecuzione. Con un altro nome o un'altra porta la suite non parte.
- **Utenti.** Il seed chiede a terminale la password di `artigiano@example.com`, `operatore@example.com` e `admin@example.com` e crea gli account social finti dell'artigiano; si può rilanciare. Altri comandi: `app.cli crea-utente --email … --nome … --ruolo artigiano|operatore|admin` e `app.cli cambia-password --email …`, che chiude le sessioni dell'utente.
- **`.env`.** `CONSORZIO_NOME`, `CONSORZIO_TELEFONO` e `CONSORZIO_EMAIL` sono i soli dati di `GET /api/consorzio`; `SESSIONE_ARTIGIANO_GIORNI=7` e `SESSIONE_OPERATORE_ORE=12` (anche per l'admin) sono la durata della sessione senza uso. Controllo: `GET /api/health` risponde `{"stato":"ok"}`.

## Prove a mano

- **Orologio di prova.** `OROLOGIO_GIORNI_AVANTI=12` manda avanti di 12 giorni l'ora di API e worker: si riavviano entrambi e si rifà l'accesso, perché le sessioni di prima risultano scadute. Le date che scrive il database restano vere. In produzione è 0, altrimenti l'applicazione non parte.
- **AI e social.** `AI_PROVIDER=finto` e `SOCIAL_PROVIDER=finto` non chiamano servizi esterni. Con `AI_PROVIDER=litellm` e una chiave non valida la generazione fallisce subito con l'errore `configurazione`, mostrato accanto a Riprova.
- **Email.** Le notifiche vanno al catcher locale Mailpit (`SMTP_HOST`, `SMTP_PORT`; pagina su http://localhost:8025).

## Dati della demo

Da database vuoto, dopo `alembic upgrade head`, un comando prepara gli utenti del seed, la bottega della demo (`demo@example.com`, profilo completo) e una campagna in bozza su Facebook e Instagram che inizia tra 4 giorni e dura 7. La password, uguale per tutti, si chiede a terminale.

```bash
uv run python -m app.cli demo --foto CARTELLA_FOTO              # tutte le foto valide della cartella, in ordine alfabetico
uv run python -m app.cli demo --foto CARTELLA_FOTO --quante 3   # solo le prime 3: gli altri post avranno un'immagine AI
```

Le foto passano gli stessi controlli del caricamento (JPEG, PNG o WebP; lato corto da 1080 px; al massimo 36 megapixel) e quelle scartate si stampano con il motivo. La cartella non è in git: finora si è usata una cartella di 13 foto di mosaici (`mosaico-01.jpg` … `mosaico-13.jpg`), di cui non sono scritti né l'autore né il posto (voce P-02 della corsia della presentazione in `docs/agenti/tasks.md`). Un `demo.json` nella cartella cambia i campi della bottega (quelli del profilo sono in plan §2):

```json
{
  "profilo": {"nome": "Mosaici d'Arte", "referente": "Giovanni", "citta": "Ravenna", "frequenza": "f5_piu"},
  "campagna": {"titolo": "Collezione d'autunno", "descrizione": "Ritratti e quadri in mosaico"},
  "gruppo": "Tessere tagliate e posate a mano sul banco di lavoro"
}
```

## Il percorso della demo

Da database vuoto, con `AI_PROVIDER=litellm`, `SOCIAL_PROVIDER=meta`, il tunnel acceso e i dati qui sopra; i CA sono quelli di spec §6.

1. L'operatore crea un artigiano nuovo e vede la password provvisoria una volta (CA-79); l'artigiano entra e arriva al passo 1 del profilo.
2. L'artigiano della demo crea una campagna di 7 giorni su Facebook e Instagram che inizia tra 4 giorni, con meno foto dei post; il passo 12 dice quanti post avranno un'immagine AI (CA-54); senza la dichiarazione l'invio è rifiutato, con la dichiarazione parte (CA-14).
3. La generazione dà i post per canale, con le foto migliori per punteggio e le immagini AI con la dicitura (CA-17, CA-57, CA-80); il costo è in Vedi campagna (CA-82).
4. In Vedi campagna l'operatore modifica un testo, ne rigenera un altro, cambia la foto di un post (CA-71) e chiede all'artigiano la foto di un secondo post (CA-86); in un'altra finestra l'artigiano la carica con la dichiarazione e invia (CA-87, CA-88, CA-90); l'operatore la usa con Cambia foto e approva; calendario per giorno (CA-56).
5. Con l'orologio avanti il worker pubblica sulla pagina di prova, con la foto dritta, senza GPS e nel formato del canale (CA-81, CA-83); se Instagram è simulato (D1) si vede solo Facebook.
6. Dopo l'approvazione l'operatore modifica un post che esce tra più di 15 minuti, ne sposta un altro, ne annulla un terzo con la nota, sospende con una nota (l'artigiano vede «Pubblicazioni ferme») e riattiva (CA-84, CA-72, CA-85, CA-32).
7. Una seconda campagna con foto non della bottega si respinge con motivo `foto`, nota e foto segnate; l'artigiano le rivede.
8. Prove negative: inizio tra 1 giorno, durata di 3 giorni, un PDF come foto, canale non collegato, artigiano su una pagina dell'operatore, rigenerazione su una campagna attiva, modifica di un post che esce entro 15 minuti, caricamento dell'artigiano dopo l'approvazione, approva con un post da rivedere, nuovo artigiano con un'email già usata (409).

## Pubblicazione reale su Meta

Di default `SOCIAL_PROVIDER=finto`: nessuna chiamata di rete. Nell'MVP tutti gli artigiani pubblicano su **una sola Pagina Facebook di prova del team**, con il suo account Instagram professionale (D1). La configurazione completa è in `docs/archivio/brief/brief-meta.md`; in breve:

1. Una Pagina di prova con un account Instagram professionale collegato, amministrata da chi configura.
2. Un'app **Business** su [developers.facebook.com](https://developers.facebook.com), strada *Instagram API with Facebook Login*: con lo Standard Access agisce solo sulle risorse di chi la sviluppa, senza App Review.
3. Permessi `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish`.
4. Dal Graph API Explorer un token utente, scambiato con uno di lunga durata (`GET /oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={token-utente}`); da lì il token della Pagina (`GET /me/accounts`) e l'id Instagram (`GET /{page-id}?fields=instagram_business_account`). Se la Pagina chiede la Page Publishing Authorization, la pubblicazione resta bloccata finché manca.
5. In `backend/.env`, mai in git: `SOCIAL_PROVIDER=meta`, `META_PAGINA_ID`, `META_INSTAGRAM_ID`, `META_TOKEN_PAGINA`, `META_GRAPH_VERSIONE` e `FOTO_URL_PUBBLICO`, l'indirizzo del tunnel da cui Instagram scarica le foto (`GET /foto/{id}/pubblica`; in demo lo stampa `cloudflared tunnel --url http://localhost:8000`). Con `META_INSTAGRAM_ID` vuoto Facebook pubblica davvero e Instagram resta simulato.

**Dal tick.** Con la campagna della demo approvata e `OROLOGIO_GIORNI_AVANTI` oltre la data del primo post ma non del secondo (di solito `4`), il worker pubblica al minuto dopo: in `pubblicazione` c'è la riga `ok` con `id_esterno` (`{pagina}_{post}` per Facebook, il post si apre da `https://www.facebook.com/{post}`; `finto-N` per Instagram simulato). `app.cli pubblica-ora` pubblica subito tutti i post approvati e serve solo alle prove a mano.

## In produzione

Le regole di sicurezza sono in `docs/agenti/constitution.md` §3; ciò che manca per un'esposizione pubblica è in `docs/ROADMAP.md`. Il testo completo di questa sezione, con l'esempio di Nginx, è in `docs/archivio/sicurezza-accesso.md`.

- **`.env`.** `AMBIENTE=produzione`; `LOGIN_LIMITE_SEGRETO` casuale di almeno 32 caratteri, uguale su tutte le istanze (il valore di `.env.example` è rifiutato); `EMAIL_TEST_ENVIRONMENT=false`; `OROLOGIO_GIORNI_AVANTI=0`.
- **Proxy.** Uvicorn sta dietro un proxy che termina HTTPS, sovrascrive gli header del client e non scrive access log; accetta gli header inoltrati solo da lì: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log`, mai `--forwarded-allow-ips '*'`. Le cinque intestazioni di sicurezza le manda il backend (`core/intestazioni_sicurezza.py`); il proxy le ripete con `always` solo su `/api/`. La prova locale con TLS vero è `tests/moduli/accesso/test_proxy_http_reale.py` (issue #17).
- **Cookie.** `adflow_sessione` è httpOnly, `SameSite=Lax`, `Path=/`; in produzione sempre Secure, e `COOKIE_SECURE=false` è rifiutato.
- **Limite degli accessi.** 5 tentativi per IP e 5 per account ogni 900 secondi (`LOGIN_LIMITE_TENTATIVI`, `LOGIN_FINESTRA_SECONDI`), poi 429 con `Retry-After`; 503 se il database non risponde. I contatori stanno in `limite_login` con chiavi HMAC di IP e account. Lo stesso segreto, con una chiave derivata, firma gli indirizzi pubblici delle foto: cambiarlo azzera i contatori e invalida gli indirizzi già dati a Instagram.
- **Eventi di sicurezza.** Il logger `adflow.sicurezza` scrive su stderr una riga JSON per `auth_failure`, `auth_invalid_input`, `invalid_session`, `role_denied`, `login_rate_limited`, `login_limiter_unavailable`, con `request_id` generato dal server; mai corpo, URL, IP, email, password, token o cookie.
- **Email.** email-validator senza DNS; il login trova anche la forma storica di un indirizzo; gli indirizzi `.test` valgono solo fuori produzione.
- **Valutazione di sicurezza.** `uv run python scripts/esegui_valutazione_sicurezza.py` (con `--security-only` solo i probe), solo su `adflow_test`; il log JSONL va in `security-assessment-logs/`, ignorato da git.

## Struttura

```
app/
  core/        config, db, coda, errori, orologio, transizioni, sicurezza (plan §7)
  adapters/    AI, social, email, archivio
  moduli/      accesso → notifiche → artigiani → campagne → contenuti → revisione → pubblicazione
  main.py · worker.py · cli.py · tabelle.py
tests/
  moduli/<modulo>/   unitari, service e API, con la fabbrica.py del modulo
  adapters/          senza rete
  percorsi/          più moduli insieme
  accettazione/      i test della simulazione di accettazione
  test_confini.py    le regole di import di constitution §2
alembic/       migrazioni
```

Un modulo importa da un altro solo `service` (e gli schemi che restituisce), e solo da quelli che lo precedono nell'ordine qui sopra; i dati degli altri si leggono con le funzioni di plan §6. I test dei CA si chiamano `test_caNN_…` (`grep -r "test_ca" tests`).
