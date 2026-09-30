# AdFlow Backend

API FastAPI per il progetto AdFlow Suite.

## Setup

1. Crea l'ambiente virtuale:
   ```bash
   python -m venv venv
   ```

2. Attiva l'ambiente:
   - Windows: `.\venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

4. Installa i pre-commit hook (una volta sola):
   ```bash
   pre-commit install
   ```

5. Copia `.env.example` in `.env` e inserisci le tue credenziali locali:
   ```bash
   cp .env.example .env
   ```

6. Assicurati che PostgreSQL sia in esecuzione e crea i database:
   ```sql
   CREATE DATABASE adflow;
   CREATE DATABASE adflow_test;
   ```

## Avvio

Avvia il server di sviluppo:
```bash
uvicorn main:app --reload
```

L'API sarà disponibile su `http://localhost:8000`

## Test

Esegui i test su PostgreSQL:
```bash
pytest
```

## Struttura

```
backend/
├── app/
│   ├── api/          # Router FastAPI
│   ├── services/     # Logica di business
│   ├── adapters/     # Adattatori per servizi esterni
│   ├── worker/       # Task Procrastinate
│   ├── domain.py     # Stati, transizioni, valori ammessi
│   ├── models.py     # SQLAlchemy models
│   ├── schemas.py    # Pydantic schemas
│   ├── config.py     # Configurazione
│   ├── db.py         # Database connection
│   ├── coda.py       # Worker queue
│   ├── security.py   # Autenticazione/autorizzazione
│   └── cli.py        # Comandi CLI
├── tests/
│   ├── unit/         # Test unitari
│   ├── services/     # Test servizi
│   ├── api/          # Test API
│   └── adapters/     # Test adattatori
├── main.py           # Entry point
└── requirements.txt  # Dipendenze
```
