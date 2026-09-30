# Comandi per applicare le migrazioni

## Prerequisiti
1. PostgreSQL deve essere in esecuzione
2. I database `adflow` e `adflow_test` devono essere creati:
   ```sql
   CREATE DATABASE adflow;
   CREATE DATABASE adflow_test;
   ```

## Comandi per applicare le migrazioni

### Su database di sviluppo (adflow)
```bash
cd backend
./venv/Scripts/alembic upgrade head
```

### Su database di test (adflow_test)
```bash
cd backend
set DATABASE_URL=postgresql://postgres:password@localhost:5432/adflow_test
./venv/Scripts/alembic upgrade head
```

## Comandi per revert
```bash
cd backend
./venv/Scripts/alembic downgrade base
```

## Generare nuova migrazione (dopo aver aggiunto models)
```bash
cd backend
./venv/Scripts/alembic revision --autogenerate -m "descrizione migrazione"
```

## Verificare stato migrazioni
```bash
cd backend
./venv/Scripts/alembic current
```

## Testare migrazioni su database vuoto
```bash
cd backend
./venv/Scripts/pytest tests/test_migrazioni.py -v
```

Nota: Questo test richiede PostgreSQL in esecuzione e i database creati.
