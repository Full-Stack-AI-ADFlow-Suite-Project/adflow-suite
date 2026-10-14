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

## Pubblicazione reale su Meta (pagina di prova)

Di default l'adattatore social è finto (`SOCIAL_PROVIDER=finto`): nessuna chiamata di rete e nessun post pubblicato davvero. Per la pubblicazione reale tutti gli artigiani dell'MVP usano **una sola Pagina Facebook di prova del team** con il suo account Instagram professionale (perimetro-mvp.md, D1). Configurazione da fare una volta sola; i dettagli sono in `docs/agenti/brief-meta.md`:

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
