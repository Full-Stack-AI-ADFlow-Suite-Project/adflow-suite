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

Le versioni stanno in `requirements.txt`. Una libreria nuova entra con una PR della corsia 0.

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
│   ├── moduli/        # Test dei moduli (con fabbrica.py per ciascuno)
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
