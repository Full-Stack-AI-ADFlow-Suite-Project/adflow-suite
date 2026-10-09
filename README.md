# AdFlow Suite

Repository ufficiale per il progetto di fine tirocinio Full Stack AI.

## ▶️ Si parte da qui

Ogni volta che riapri il progetto, dalla radice del repository:

```bash
uv run python allinea.py
```

Un solo comando: scarica le novità e aggiorna `main` (mai il tuo branch di lavoro, mai le modifiche non salvate), installa le dipendenze cambiate, porta il database all'ultima migrazione, poi ti dice quali task della tua corsia sono pronti, cosa leggere per ognuno e che branch aprire.

- La prima volta indica la tua corsia: `uv run python allinea.py 3` (0 comune, 1 accesso e artigiani, 2 campagne, 3 contenuti, 4 revisione e pubblicazione, 5 frontend). Resta ricordata.
- `uv run python allinea.py tutte` mostra lo stato di tutte le corsie; `--stato` mostra lo stato senza toccare nulla.
- In VS Code è il task predefinito: **Ctrl+Shift+B** (su macOS ⇧⌘B), oppure _Terminal → Run Task → Allinea_.
- Chi lavora con un agente (Claude Code, Codex, Kilo…) non deve fare altro: [`AGENTS.md`](AGENTS.md) gli dice di lanciarlo a inizio sessione.

Funziona anche alla prima installazione: vedi [Setup](#-setup-fase-1---locale).

## 📁 Struttura del Progetto

- `docs/`: documentazione del progetto (vedi sotto)
- `backend/`: API FastAPI e worker Procrastinate (Python)
- `frontend/`: interfaccia utente (React + TypeScript + Mantine) · nasce con il task T1-51
- `allinea.py`: il comando qui sopra

## 📚 Documentazione

La documentazione ha **due canali** (ADR-46):

- **Appunti** · [`docs/appunti/`](docs/appunti/LEGGIMI.md): diagrammi (`architettura/`), pagine statiche di prova (`pagine/`, mappa in [`index.html`](docs/appunti/pagine/index.html)), note sul flusso e sull'architettura, lavori aperti, decisioni (ADR). Materiale in continua rimodulazione, mantenuto dall'amministratore dei documenti; è la fonte di verità. Si parte da [`LEGGIMI.md`](docs/appunti/LEGGIMI.md).
- **Canale agenti** · [`AGENTS.md`](AGENTS.md) + [`docs/agenti/`](docs/agenti/): regole (`constitution.md`), cosa (`spec.md`), come (`plan.md`), task (`tasks.md`), verifica (`converge.md`). Breve, derivato dagli appunti. Anche le persone ci trovano i task da prendere.

[`docs/novita/`](docs/novita/) raccoglie le note datate di alcune PR (cosa è entrato quel giorno, procedure operative): non fanno testo. Dove non tornano con il canale agenti, vale il canale agenti.

## 🚀 Setup (Fase 1 - Locale)

Servono [uv](https://docs.astral.sh/uv/getting-started/installation/), PostgreSQL 16 con i database `adflow` e `adflow_test` e, per il frontend, Node 22+. Python 3.11 lo scarica uv, se manca. Le istruzioni del frontend si scrivono nel task T1-51.

I comandi sono gli stessi su Windows (PowerShell), macOS e Linux: `uv run` usa l'ambiente virtuale `.venv` senza doverlo attivare. Vanno lanciati uno alla volta (`&&` non funziona in ogni shell).

### Backend

Prima installazione, dalla radice del repository:

```bash
uv run python allinea.py
```

Crea `.venv`, installa le dipendenze e l'hook di `pre-commit`, e copia `backend/.env.example` in `backend/.env`. A quel punto si ferma: apri `backend/.env`, metti utente e password del tuo PostgreSQL in `DATABASE_URL` e `DATABASE_URL_TEST`, e rilancialo. La seconda volta porta il database all'ultima migrazione.

Chi preferisce i passi a mano:

```bash
uv venv --python 3.11 --seed .venv
uv pip install -r backend/requirements.txt
uv run pre-commit install
cp backend/.env.example backend/.env
```

Avvio, da `backend/`:

```bash
uv run alembic upgrade head               # porta il database all'ultima migrazione
uv run uvicorn app.main:app --reload      # API su http://localhost:8000
```

Dati di partenza, una volta sola (si può rilanciare: ciò che esiste già resta com'è):

```bash
uv run python -m app.cli seed             # artigiano con profilo, operatore e admin
```

Il comando chiede a terminale la password dei tre utenti (`artigiano@example.com`, `operatore@example.com`, `admin@example.com`): non è scritta nel codice. Crea anche gli account social finti Facebook e Instagram dell'artigiano, nello stato `collegato`; se si rilancia, aggiunge gli account mancanti e conserva quelli esistenti, incluso il loro stato.

Altri comandi, sempre da `backend/`:

```bash
uv run python -m app.cli crea-utente --email … --nome … --ruolo artigiano|operatore|admin
uv run python -m app.cli cambia-password --email …
```

Il secondo chiede e conferma la nuova password a terminale e chiude le sessioni aperte dell'utente.

In `.env` configura `CONSORZIO_NOME`, `CONSORZIO_TELEFONO` e `CONSORZIO_EMAIL`: `GET /api/consorzio` restituisce soltanto questi contatti, senza sessione. `SESSIONE_ARTIGIANO_GIORNI=7` e `SESSIONE_OPERATORE_ORE=12` sono la durata della sessione senza uso (la seconda vale anche per l'admin): ogni richiesta la rinnova.

Controllo: `http://localhost:8000/api/health` risponde `{"stato":"ok"}`; la documentazione delle API è su `http://localhost:8000/docs`.

Per avviare il worker Procrastinate (il tick di pubblicazione, ogni minuto, è registrato nell'app), da `backend/`:

```bash
uv run python -m procrastinate -a app.worker.app worker --concurrency 1
```

Le tabelle della coda le crea `alembic upgrade head` (migrazione 007).

### Prima di ogni PR

Da `backend/`, un comando alla volta:

```bash
uv run alembic upgrade head
uv run pytest
uv run black --check .
```

I test usano `adflow_test` e lo svuotano a ogni esecuzione: non metterci dati da conservare. A ogni PR GitHub rilancia gli stessi tre comandi su una macchina pulita ([`.github/workflows/backend.yml`](.github/workflows/backend.yml)): prima di unire, il controllo deve essere verde. La lista completa è in [`docs/agenti/converge.md`](docs/agenti/converge.md).

## 🔧 Regole di Git (Leggere attentamente!)

1. **NON** lavorare mai direttamente sul branch `main`.
2. Prima di iniziare un task, crea un branch: `git switch -c feature/<id>-<breve>` (es. `feature/T1-24-invio-riprova`). Il nome te lo propone `allinea.py`.
3. `pre-commit` (installato da `allinea.py`) formatta il codice Python a ogni `git commit`. Se un hook modifica dei file, rifai `git add` e ripeti il commit.
4. Una libreria nuova entra in `backend/requirements.txt` con una PR della corsia 0, prima della PR del task che la usa.
5. Quando hai finito, pusha il branch e apri una **Pull Request** su GitHub. Revisione: corsia 0 approvata da tutto il team, corsie 1–5 riviste in gruppo (vedi `docs/agenti/tasks.md`); il merge lo fa l'admin.

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
