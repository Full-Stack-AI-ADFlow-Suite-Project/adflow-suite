# AdFlow Suite

Repository ufficiale per il progetto di fine tirocinio Full Stack AI.

## 📁 Struttura del Progetto
Il repository riparte dai soli documenti (ADR-51): il codice nasce con i task dello sprint 1.
- `docs/`: documentazione del progetto (vedi sotto)
- `backend/`: API FastAPI e Worker Procrastinate (Python) · nasce con il task T1-01
- `frontend/`: Interfaccia utente (React + TypeScript + Mantine) · nasce con il task T1-51

## 📚 Documentazione

La documentazione ha **due canali** (ADR-46):
- **Appunti** · [`docs/appunti/`](docs/appunti/LEGGIMI.md): diagrammi (`architettura/`), pagine statiche di prova (`pagine/`, mappa in [`index.html`](docs/appunti/pagine/index.html)), note sul flusso e sull'architettura, lavori aperti, decisioni (ADR). Materiale in continua rimodulazione, mantenuto dall'amministratore dei documenti; è la fonte di verità. Si parte da [`LEGGIMI.md`](docs/appunti/LEGGIMI.md).
- **Canale agenti** · [`AGENTS.md`](AGENTS.md) + [`docs/agenti/`](docs/agenti/): regole (`constitution.md`), cosa (`spec.md`), come (`plan.md`), task (`tasks.md`), verifica (`converge.md`). Breve, derivato dagli appunti. Anche le persone ci trovano i task da prendere.

## 🚀 Setup (Fase 1 - Locale)

Servono Python 3.11+, Node 22+ e PostgreSQL 16 con i database `adflow` e `adflow_test`. Le istruzioni del frontend si scrivono nel task T1-51.

### Backend

Installazione, una volta sola, dalla radice del repository:

```bash
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
pre-commit install
cp backend/.env.example backend/.env
```

Poi apri `backend/.env` e metti utente e password del tuo PostgreSQL in `DATABASE_URL` e `DATABASE_URL_TEST`.

Avvio, da `backend/` con l'ambiente virtuale attivo:

```bash
alembic upgrade head               # porta il database all'ultima migrazione
uvicorn app.main:app --reload      # API su http://localhost:8000
```

Dati di partenza, una volta sola (si può rilanciare: ciò che esiste già resta com'è):

```bash
python -m app.cli seed             # artigiano con profilo, operatore e admin
```

Il comando chiede a terminale la password dei tre utenti (`artigiano@example.com`, `operatore@example.com`, `admin@example.com`): non è scritta nel codice. Un altro utente si crea con `python -m app.cli crea-utente --email … --nome … --ruolo artigiano|operatore|admin` (funziona da T1-13).

Il seed crea anche gli account social finti Facebook e Instagram, nello stato `collegato`. Se si rilancia, aggiunge gli account mancanti e conserva quelli esistenti, incluso il loro stato.

`python -m app.cli cambia-password --email …` chiede e conferma la nuova password a terminale, poi delega al service di accesso; l'implementazione del cambio password arriva con T1-13.

In `.env` configura `CONSORZIO_NOME`, `CONSORZIO_TELEFONO` e `CONSORZIO_EMAIL`: `GET /api/consorzio` restituisce soltanto questi contatti, senza sessione. Se non sono configurati restituisce stringhe vuote. `SESSIONE_ARTIGIANO_GIORNI=7` e `SESSIONE_OPERATORE_ORE=12` definiscono la durata senza uso (anche per l'admin); saranno usate dal login di T1-11 e dal rinnovo a ogni richiesta di T1-12.

Controllo: `http://localhost:8000/api/health` risponde `{"stato":"ok"}`; la documentazione delle API è su `http://localhost:8000/docs`.

Prima di ogni PR, sempre da `backend/`:

```bash
alembic upgrade head && pytest && black --check .
```

I test usano `adflow_test` e lo svuotano a ogni esecuzione: non metterci dati da conservare.

Per avviare il worker Procrastinate (il tick periodico è registrato nell'app), da
`backend/`:

```bash
python -m procrastinate -a app.worker.app worker --concurrency 1
```

Le tabelle della coda le crea `alembic upgrade head` (migrazione 007). Finché non c'è T1-43 il tick finisce in errore a ogni minuto (`NotImplementedError`): è atteso.

## 🔧 Regole di Git (Leggere attentamente!)
1. **NON** lavorare mai direttamente sul branch `main`.
2. Prima di iniziare un task, crea un branch: `git checkout -b feature/<id>-<breve>` (es. `feature/T1-22-api-bozza`)
3. Dopo il primo setup del backend lancia `pre-commit install` (una volta sola): formatterà automaticamente il tuo codice a ogni `git commit`.
4. Quando hai finito, pusha il branch e apri una **Pull Request** su GitHub. Revisione: corsia 0 approvata da tutto il team, corsie 1–5 riviste in gruppo (vedi `docs/agenti/tasks.md`); il merge lo fa l'admin.

## Protezioni dell'accesso (#16–19)

La migrazione 009 aggiunge i contatori condivisi dei tentativi di login in PostgreSQL.
Prima dell'avvio aggiornare lo schema. La politica predefinita ammette cinque
richieste per IP e cinque per account ogni 900 secondi, anche con più worker;
contano anche gli accessi riusciti. Il blocco risponde 429 con `Retry-After`.

In produzione impostare `AMBIENTE=produzione`, un `LOGIN_LIMITE_SEGRETO` casuale
di almeno 32 caratteri identico su tutte le istanze e `EMAIL_TEST_ENVIRONMENT=false`.
I cookie sono sempre Secure in produzione. Per il proxy fidato, i log e le prove
HTTPS leggere [la procedura di sicurezza](docs/novita/16-19-sicurezza-accesso.md).
Non usare il segreto finto di `.env.example` in produzione.

La creazione utenti richiede email valide secondo email-validator, senza DNS.
Il login mantiene la compatibilità con gli indirizzi storici; `.test` è ammesso
nelle nuove creazioni solo con `EMAIL_TEST_ENVIRONMENT=true` in sviluppo/test.
La suite comprende prove TLS locali con certificati temporanei generati da cryptography.

