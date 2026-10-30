# Carico di accettazione (T4-105)

Le prove di §7.2 di `docs/accettazione-post-mvp.md`, con `locust` lanciato con
`uvx` (non entra in `requirements.txt`).

## Database

Si usa **solo** il database dedicato `adflow_accettazione`: mai `adflow` (i dati
di lavoro) e mai `adflow_test` (le prove automatiche). Creazione e pulizia:

```bash
# dal backend, con le stesse credenziali di .env ma il nome del database cambiato
# (il comando concreto è in docs/accettazione/report/T4-105-carico.md)
```

A fine prova il database dedicato si rimuove, così non restano dati di carico.

## Dati

I dati si preparano con le fabbriche dei test dei moduli, da `backend/`:

```bash
# utenti e botteghe del seed, poi campagne in bozza/in revisione/attive
uv run python -m app.cli seed
```

Il locustfile lavora sugli utenti `artigiano@example.com` e
`operatore@example.com` del seed (password da `PASSWORD` nell'ambiente).

## Avvio

```bash
# API in locale sul database dedicato, provider finti
DATABASE_URL=postgresql+psycopg://…/adflow_accettazione \
AI_PROVIDER=finto SOCIAL_PROVIDER=finto \
uv run uvicorn app.main:app --host 127.0.0.1 --port 8905

# carico normale (10 utenti misti, 60 secondi: la prova completa è 30 minuti)
BASE_URL=http://127.0.0.1:8905 PASSWORD=… \
uvx locust -f docs/accettazione/carico/locustfile.py --headless \
    --host http://127.0.0.1:8905 -u 10 -r 2 -t 60s
```

## Che cosa si guarda

- p50, p95, p99 per endpoint; errori; connessioni al database;
- picco: 10 volte il carico per 2 minuti (503 ordinati invece di 500);
- durata: 2–8 ore (memoria, connessioni, crescita di `limite_login`,
  `chiamata_ai` e delle tabelle di Procrastinate);
- upload: 50 caricamenti paralleli da 10 MB (memoria di Pillow, 413 oltre i
  12 MB, disco);
- worker: 1000 post nello stesso minuto con Meta finto lento;
- storico AI: elenco e numeri con 100 000 chiamate.

I numeri ipotizzati e i risultati misurati stanno in
`docs/accettazione/report/T4-105-carico.md`.
