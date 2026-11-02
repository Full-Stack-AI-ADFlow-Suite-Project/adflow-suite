# AdFlow Suite - Backend

Monolite a moduli + worker per la gestione di campagne social per artigiani.

Installazione, configurazione, avvio e controlli prima della PR sono nel [README principale](../README.md): qui c'è solo la mappa del codice. Per allinearti e sapere quale task prendere, dalla radice: `uv run python allinea.py`.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2 + Alembic
- PostgreSQL 16
- Procrastinate (coda e job in PostgreSQL)
- LiteLLM (AI; provider finto per sviluppo e test)
- pytest

Le versioni stanno in `requirements.txt`. Una libreria nuova entra in `requirements.txt` nella PR del task che la usa, con nome, motivo e licenza.

## Comandi

Da questa cartella, con `uv run` davanti (usa `.venv` della radice senza attivarlo), uno alla volta:

```bash
uv run alembic upgrade head                                               # database all'ultima migrazione
uv run uvicorn app.main:app --reload                                      # API su http://localhost:8000
uv run python -m procrastinate -a app.worker.app worker --concurrency 1   # worker, con il tick di pubblicazione ogni minuto
uv run python -m app.cli seed                                             # dati di partenza
uv run pytest                                                             # test, sul database adflow_test
uv run black --check .                                                    # formattazione
```

Il tick di pubblicazione è registrato nel worker: non serve nessun cron esterno. I test svuotano `adflow_test` a ogni esecuzione e lo portano all'ultima migrazione.

## Dati della demo

Da database vuoto (dopo `alembic upgrade head`) un solo comando prepara la demo di `docs/agenti/converge.md` §4: gli utenti del seed, la bottega della demo (`demo@example.com`, profilo completo) e una campagna in bozza su Facebook e Instagram che inizia tra 4 giorni e dura 7, con le foto vere prese da una cartella qualsiasi. La password, la stessa per tutti gli utenti, si chiede a terminale; le foto restano fuori da git.

```bash
uv run python -m app.cli demo --foto CARTELLA              # tutte le foto valide della cartella
uv run python -m app.cli demo --foto CARTELLA --quante 3   # solo le prime 3: le altre posizioni sono immagini AI
```

Senza altro, la bottega ha il profilo del seed e testi generici. Per provare la propria bottega si mette nella cartella delle foto un `demo.json` con i campi da cambiare (quelli del profilo sono i campi di plan §2):

```json
{
  "profilo": {"nome": "Mosaici d'Arte", "referente": "Giovanni", "citta": "Ravenna", "frequenza": "f5_piu"},
  "campagna": {"titolo": "Collezione d'autunno", "descrizione": "Ritratti e quadri in mosaico"},
  "gruppo": "Tessere tagliate e posate a mano sul banco di lavoro"
}
```

Le foto passano per gli stessi controlli del caricamento (JPEG, PNG o WebP; lato corto da 1080 px; al massimo 36 megapixel): quelle scartate si stampano con il motivo. I file si prendono in ordine alfabetico. Per la demo vera servono anche `AI_PROVIDER=litellm` in `backend/.env`, Mailpit acceso (`mailpit`, email su http://localhost:8025) e, per la pubblicazione, la configurazione Meta qui sotto. Per rifare la demo si riparte da un database vuoto.

## Pubblicazione reale su Meta (pagina di prova)

Di default l'adattatore social è finto (`SOCIAL_PROVIDER=finto`): nessuna chiamata di rete e nessun post pubblicato davvero. Per la pubblicazione reale tutti gli artigiani dell'MVP usano **una sola Pagina Facebook di prova del team** con il suo account Instagram professionale (perimetro-mvp.md, D1). Configurazione da fare una volta sola; i dettagli sono in `docs/archivio/brief-meta.md`:

1. Da un account Facebook personale del team crea una **Pagina di prova** e collegale un **account Instagram professionale** (Impostazioni della Pagina → Account collegati). Chi configura deve esserne amministratore.
2. Su [developers.facebook.com](https://developers.facebook.com) crea un'app di tipo **Business** con il caso d'uso per gestire una Pagina e quello per l'API di Instagram, nella strada **Instagram API with Facebook Login**. Con lo Standard Access l'app agisce solo sulle risorse di chi la sviluppa: niente App Review né verifica aziendale.
3. Permessi da chiedere: `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish`.
4. Nel Graph API Explorer genera un **token utente** con quei permessi, poi scambialo con un token di lunga durata:

   ```
   GET /oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={token-utente}
   ```

   e con quello prendi il **token della Pagina** da `GET /me/accounts`. L'id dell'account Instagram arriva da `GET /{page-id}?fields=instagram_business_account`. Controlla le scadenze con lo strumento di debug dei token.
5. Se la Pagina chiede la **Page Publishing Authorization**, completala subito: finché manca la pubblicazione è bloccata.
6. Prova a mano prima del codice: un post con foto sulla Pagina (`POST /{META_GRAPH_VERSIONE}/{META_PAGINA_ID}/photos` con `message` e `source` o `url`) e uno su Instagram (`POST /{ig-id}/media` con `image_url` — JPEG a un indirizzo pubblico — e `caption`, poi `POST /{ig-id}/media_publish` con `creation_id`).
7. In `backend/.env` (mai in git): `SOCIAL_PROVIDER=meta`, `META_PAGINA_ID`, `META_INSTAGRAM_ID`, `META_TOKEN_PAGINA`, `META_GRAPH_VERSIONE` e `FOTO_URL_PUBBLICO` — l'indirizzo pubblico del tunnel da cui Instagram scarica le foto (`GET /foto/{id}/pubblica`); in demo lo stampa `cloudflared tunnel --url http://localhost:8000`. **Ripiego (D1)**: se `META_INSTAGRAM_ID` è vuoto Facebook pubblica per davvero e Instagram resta simulato.

Il token della Pagina è un segreto: solo in `backend/.env`, mai in git e mai nei log.

### Prova della pubblicazione dal tick (T3-43)

La pubblicazione reale la fa il worker: `pubblica-ora` serve alle prove a mano e pubblica subito tutti i post approvati, sulla Pagina vera sono troppi.

1. Campagna della demo approvata (Dati della demo, poi invio e approvazione).
2. In `backend/.env` `OROLOGIO_GIORNI_AVANTI` con i giorni che bastano a superare la data del primo post ma non quella del secondo (con la demo che inizia tra 4 giorni, di solito `4`).
3. Worker acceso (`uv run python -m procrastinate -a app.worker.app worker --concurrency 1`): al minuto dopo il tick pubblica. Nella tabella `pubblicazione` c'è la riga `ok` con `id_esterno` e il post è `pubblicato`; per Facebook `id_esterno` è `{pagina}_{post}` e il post si apre da `https://www.facebook.com/{post}`.
4. Worker fermo e `OROLOGIO_GIORNI_AVANTI=0`.

Con `META_INSTAGRAM_ID` vuoto il post Instagram esce dal finto (`id_esterno` `finto-N`) e il tunnel non serve.

## Struttura

```
backend/
├── app/
│   ├── core/          # Funzioni comuni (config, db, coda, errori, orologio, transizioni, security, limiti e eventi di sicurezza)
│   ├── adapters/      # Adattatori per servizi esterni (AI, social, email, archivio)
│   ├── moduli/        # Moduli di business (accesso, notifiche, artigiani, campagne, contenuti, revisione, pubblicazione)
│   ├── main.py        # App FastAPI
│   ├── worker.py      # Worker Procrastinate
│   ├── cli.py         # CLI per comandi di gestione
│   └── tabelle.py     # Composizione per Alembic
├── tests/
│   ├── moduli/        # Test dei moduli, con la fabbrica.py di ciascuno (vuota dove plan §6 non ne prevede)
│   ├── adapters/      # Test degli adattatori
│   ├── percorsi/      # Test dei percorsi con più moduli
│   ├── conftest.py    # Fixture pytest
│   └── test_confini.py # Test dei confini tra moduli
├── alembic/           # Migrazioni del database
└── requirements.txt
```

Cosa offre già `core/` e come si usano le fixture dei test: [`docs/agenti/plan.md`](../docs/agenti/plan.md) §7.

## Ordine dei moduli

1. accesso
2. notifiche
3. artigiani
4. campagne
5. contenuti
6. revisione
7. pubblicazione

Un modulo importa da un altro modulo solo `service` (e gli schemi che restituisce), e solo se l'altro lo **precede**. I dati di un altro modulo si leggono con le funzioni di plan §6, mai con SQL scritto a mano sulle sue tabelle.
