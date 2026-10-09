# AdFlow Suite - Backend

Monolite a moduli + worker per la gestione di campagne social per artigiani.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2 + Alembic
- PostgreSQL 16
- Procrastinate (coda e job in PostgreSQL)
- LiteLLM (AI; provider finto per sviluppo)
- pytest

## Installazione

Dalla radice del repository, con [uv](https://docs.astral.sh/uv/getting-started/installation/); i comandi sono gli stessi su Windows, macOS e Linux (dettagli nel [README principale](../README.md)):

```bash
uv venv --python 3.11 --seed .venv
uv pip install -r backend/requirements.txt
```

Gli altri comandi di questa pagina si lanciano da `backend/` con `uv run` davanti (per esempio `uv run pytest`), oppure con l'ambiente virtuale attivo.

## Configurazione

Copia `.env.example` in `.env` e configura le variabili:

```bash
cp backend/.env.example backend/.env
```

Variabili obbligatorie:

- `DATABASE_URL`: URL del database PostgreSQL
- `DATABASE_URL_TEST`: URL del database di test

## Database

```bash
# Esegui le migrazioni
alembic upgrade head

# Crea il database di test
createdb adflow_test
```

## Avvio

### API server

```bash
uvicorn app.main:app --reload
```

L'API sarà disponibile su `http://localhost:8000`

### Worker Procrastinate

```bash
python -m app.worker
```

Il worker esegue i job in background dalla coda PostgreSQL.

### Tick pubblicazione

Il job `tick_pubblicazione` deve essere schedulato esternamente per eseguirsi ogni minuto:

```bash
# Esempio con cron (Linux/Mac)
* * * * * cd /path/to/backend && python -c "from app.core.coda import accoda, JOB_TICK_PUBBLICAZIONE; accoda(JOB_TICK_PUBBLICAZIONE)"
```

## Test

```bash
pytest
```

I test usano il database `adflow_test` (creato manualmente).

## Struttura

```
backend/
├── app/
│   ├── core/          # Funzioni comuni (config, db, coda, errori, orologio, transizioni, security)
│   ├── adapters/      # Adattatori per servizi esterni (AI, social, email, archivio)
│   ├── moduli/        # Moduli di business (accesso, artigiani, campagne, contenuti, revisione, pubblicazione, notifiche)
│   ├── main.py        # App FastAPI
│   ├── worker.py      # Worker Procrastinate
│   ├── cli.py         # CLI per comandi di gestione
│   └── tabelle.py     # Composizione per Alembic
├── tests/
│   ├── moduli/        # Test dei moduli (con fabbrica.py per ciascuno)
│   ├── adapters/      # Test degli adattatori
│   ├── percorsi/      # Test dei percorsi API completi
│   ├── conftest.py    # Fixture pytest
│   └── test_confini.py # Test dei confini tra moduli
├── alembic/           # Migrazioni del database
└── requirements.txt
```

## Ordine dei moduli

1. accesso
2. notifiche
3. artigiani
4. campagne
5. contenuti
6. revisione
7. pubblicazione

Un modulo importa da un altro modulo solo `service` (e gli schemi che restituisce), e solo se l'altro lo **precede**.
