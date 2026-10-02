# AdFlow Suite

Repository ufficiale per il progetto di fine tirocinio Full Stack AI.

## 📁 Struttura del Progetto
Il repository riparte dai soli documenti (ADR-51): il codice nasce con i task dello sprint 1.
- `docs/`: documentazione del progetto (vedi sotto)
- `backend/`: API FastAPI e Worker Procrastinate (Python) · nasce con il task T1-01
- `frontend/`: Interfaccia utente (React + TypeScript + Mantine) · nasce con il task T1-51

## 📚 Documentazione

La documentazione ha **due canali** (ADR-46):
- **Appunti** · [`docs/appunti/`](docs/appunti/LEGGIMI.md): diagrammi e pagine statiche (`architettura/`), note sul flusso e sull'architettura, lavori aperti, decisioni (ADR). Materiale in continua rimodulazione, mantenuto dall'amministratore dei documenti; è la fonte di verità. Si parte da [`LEGGIMI.md`](docs/appunti/LEGGIMI.md).
- **Canale agenti** · [`AGENTS.md`](AGENTS.md) + [`docs/agenti/`](docs/agenti/): regole (`constitution.md`), cosa (`spec.md`), come (`plan.md`), task (`tasks.md`), verifica (`converge.md`). Breve, derivato dagli appunti. Anche le persone ci trovano i task da prendere.
- **Novità** · [`docs/novita/`](docs/novita/): una nota per ogni PR che cambia il modo di lavorare (cosa c'è di nuovo, cosa cambia per il team).

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

Controllo: `http://localhost:8000/api/health` risponde `{"stato":"ok"}`; la documentazione delle API è su `http://localhost:8000/docs`.

Prima di ogni PR, sempre da `backend/`:

```bash
alembic upgrade head && pytest && black --check .
```

I test usano `adflow_test` e lo svuotano a ogni esecuzione: non metterci dati da conservare. Il worker si avvia dal task T1-05.

## 🔧 Regole di Git (Leggere attentamente!)
1. **NON** lavorare mai direttamente sul branch `main`.
2. Prima di iniziare un task, crea un branch: `git checkout -b feature/<id>-<breve>` (es. `feature/T1-22-api-bozza`)
3. Dopo il primo setup del backend lancia `pre-commit install` (una volta sola): formatterà automaticamente il tuo codice a ogni `git commit`.
4. Quando hai finito, pusha il branch e apri una **Pull Request** su GitHub. Revisione: corsia 0 approvata da tutto il team, corsie 1–5 riviste in gruppo (vedi `docs/agenti/tasks.md`); il merge lo fa l'admin.
