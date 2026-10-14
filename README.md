# AdFlow Suite

Repository ufficiale per il progetto di fine tirocinio Full Stack AI.

**Perimetro MVP** (ADR-114): consegna e pitch il 6 novembre 2026, codice bloccato il 30 ottobre. Che cosa entra nell'MVP: [`docs/agenti/perimetro-mvp.md`](docs/agenti/perimetro-mvp.md); che cosa resta fuori: [`docs/ROADMAP.md`](docs/ROADMAP.md).

## ▶️ Si parte da qui

Ogni volta che riapri il progetto, dalla radice del repository:

```bash
uv run python allinea.py
```

Un solo comando: scarica le novità e aggiorna `main` (mai il tuo branch di lavoro, mai le modifiche non salvate), installa le dipendenze cambiate, porta il database all'ultima migrazione, poi ti dice quali task della tua area sono pronti, cosa leggere per ognuno e che branch aprire.

- La prima volta indica la tua area: `uv run python allinea.py 3` (0 comune e deliverable, 1 nuovo artigiano e calendario, 2 foto e invio, 3 AI vera, 4 Meta, 5 frontend). Resta ricordata.
- `uv run python allinea.py tutte` mostra lo stato di tutte le aree; `--stato` mostra lo stato senza toccare nulla.
- In VS Code è il task predefinito: **Ctrl+Shift+B** (su macOS ⇧⌘B), oppure _Terminal → Run Task → Allinea_.
- Chi lavora con un agente (Claude Code, Codex, Kilo…) non deve fare altro: [`AGENTS.md`](AGENTS.md) gli dice di lanciarlo a inizio sessione.

Funziona anche alla prima installazione: vedi [Setup](#-setup-fase-1---locale).

## 📁 Struttura del Progetto

- `docs/`: documentazione del progetto (vedi sotto)
- `backend/`: API FastAPI e worker Procrastinate (Python)
- `frontend/`: interfaccia utente (React + TypeScript + Mantine): installazione e avvio in [`frontend/README.md`](frontend/README.md)
- `allinea.py`: il comando qui sopra

## 📚 Documentazione

Un solo canale fa testo (ADR-114): [`AGENTS.md`](AGENTS.md) e [`docs/agenti/`](docs/agenti/): perimetro dell'MVP (`perimetro-mvp.md`), regole (`constitution.md`), cosa (`spec.md`), come (`plan.md`), task (`tasks.md`), verifica (`converge.md`). Anche le persone ci trovano i task da prendere.

- [`docs/proposta-tecnica.md`](docs/proposta-tecnica.md): la proposta tecnica per il cliente (analisi, architettura, piano con costi e tempi).
- [`docs/ROADMAP.md`](docs/ROADMAP.md): ciò che non entra nell'MVP; è anche la slide della roadmap nel pitch.
- [`docs/pagine/`](docs/pagine/index.html): pagine statiche dell'MVP, riferimento per l'interfaccia.
- [`docs/ADR.md`](docs/ADR.md): registro delle decisioni, con il perché e le alternative scartate; una riga nuova solo se cambia il perimetro dell'MVP.
- [`docs/sicurezza-accesso.md`](docs/sicurezza-accesso.md): procedura operativa per proxy, log e HTTPS (issue #16–19).
- [`docs/archivio/`](docs/archivio/LEGGIMI.md): appunti, note e diagrammi di prima dell'MVP, note datate delle PR, brief e script dei task chiusi; non fanno testo.

## 🚀 Setup (Fase 1 - Locale)

Servono [uv](https://docs.astral.sh/uv/getting-started/installation/), PostgreSQL 16 con i database `adflow` e `adflow_test` e, per il frontend, Node 22+. Python 3.11 lo scarica uv, se manca. Il frontend si installa e si avvia come dice [`frontend/README.md`](frontend/README.md).

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

Per provare a mano la pubblicazione senza aspettare i giorni veri, `OROLOGIO_GIORNI_AVANTI=12` in `backend/.env` manda avanti di 12 giorni l'ora di API e worker: si riavviano entrambi e si rifà l'accesso, perché le sessioni di prima risultano scadute. Le date che scrive il database da solo (per esempio quando è nato un errore) restano quelle vere. In produzione la variabile deve restare a 0: con un altro valore l'applicazione non parte.

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
3. `pre-commit` (installato da `allinea.py`) formatta il codice a ogni `git commit`: Python con black, frontend con prettier. Se un hook modifica dei file, rifai `git add` e ripeti il commit.
4. Una libreria nuova entra in `backend/requirements.txt` nella PR del task che la usa, con nome, motivo e licenza.
5. Quando hai finito, pusha il branch e apri una **Pull Request** su GitHub. La rivede un collega; se cambia composizione, `core/`, `alembic/`, `requirements.txt` o un `domain.py`, la rivede il referente dei file comuni. I controlli devono essere verdi; il merge lo fa l'admin.

## Protezioni dell'accesso (#16–19)

La migrazione 009 aggiunge i contatori condivisi dei tentativi di login in PostgreSQL.
Prima dell'avvio aggiornare lo schema. La politica predefinita ammette cinque
richieste per IP e cinque per account ogni 900 secondi, anche con più worker;
contano anche gli accessi riusciti. Il blocco risponde 429 con `Retry-After`.

In produzione impostare `AMBIENTE=produzione`, un `LOGIN_LIMITE_SEGRETO` casuale
di almeno 32 caratteri identico su tutte le istanze e `EMAIL_TEST_ENVIRONMENT=false`.
I cookie sono sempre Secure in produzione. Per il proxy fidato, i log e le prove
HTTPS leggere [la procedura di sicurezza](docs/sicurezza-accesso.md).
Non usare il segreto finto di `.env.example` in produzione.

La creazione utenti richiede email valide secondo email-validator, senza DNS.
Il login mantiene la compatibilità con gli indirizzi storici; `.test` è ammesso
nelle nuove creazioni solo con `EMAIL_TEST_ENVIRONMENT=true` in sviluppo/test.
La suite comprende prove TLS locali con certificati temporanei generati da cryptography.
