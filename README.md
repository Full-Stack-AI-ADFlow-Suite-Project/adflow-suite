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

- `backend/`: API FastAPI e worker Procrastinate (Python): comandi, dati della demo e Meta in [`backend/README.md`](backend/README.md)
- `frontend/`: interfaccia utente (React + TypeScript + Mantine): installazione e avvio in [`frontend/README.md`](frontend/README.md)
- `docs/`: documentazione (vedi sotto)
- `allinea.py`: il comando qui sopra; `avvia.py`: avvia API, worker e frontend insieme (`uv run python avvia.py`, Ctrl+C li ferma tutti)

## 📚 Documentazione

Un solo canale fa testo (ADR-114): [`AGENTS.md`](AGENTS.md) e [`docs/agenti/`](docs/agenti/): perimetro dell'MVP (`perimetro-mvp.md`), regole (`constitution.md`), cosa (`spec.md`), come (`plan.md`), task (`tasks.md`), verifica (`converge.md`). Anche le persone ci trovano i task da prendere.

- [`docs/proposta-tecnica.md`](docs/proposta-tecnica.md): la proposta tecnica per il cliente (analisi, architettura, piano con costi e tempi).
- [`docs/pitch.md`](docs/pitch.md): scaletta del pitch del 6 novembre 2026, con le slide in [`docs/pagine/AdFlow-pitch.html`](docs/pagine/AdFlow-pitch.html).
- [`docs/ROADMAP.md`](docs/ROADMAP.md): ciò che non entra nell'MVP; è anche la slide della roadmap nel pitch.
- [`docs/pagine/`](docs/pagine/index.html): pagine statiche dell'MVP, riferimento per l'interfaccia.
- [`docs/ADR.md`](docs/ADR.md): registro delle decisioni, con il perché e le alternative scartate; una riga nuova solo se cambia il perimetro dell'MVP.
- [`docs/accettazione.md`](docs/accettazione.md): esito della simulazione di accettazione, con i limiti dell'MVP e le correzioni proposte.
- [`docs/sicurezza-accesso.md`](docs/sicurezza-accesso.md): procedura operativa per proxy, log e HTTPS (issue #16–19) e interventi aperti prima di un'esposizione pubblica.
- [`docs/archivio/`](docs/archivio/LEGGIMI.md): tutto ciò che non fa testo, con la mappa dei vecchi percorsi: appunti e diagrammi di prima dell'MVP, note delle PR, i brief di tutte le corsie, piano e report della simulazione, la valutazione di sicurezza del 30/10, le evidenze di QA (ADR-115, ADR-122).

## 🚀 Setup

Servono [uv](https://docs.astral.sh/uv/getting-started/installation/), PostgreSQL 16 con i database `adflow` e `adflow_test` e, per il frontend, Node 22+. Python 3.11 lo scarica uv, se manca. I comandi sono gli stessi su Windows (PowerShell), macOS e Linux e vanno lanciati uno alla volta (`&&` non funziona in ogni shell).

La prima volta, dalla radice: `uv run python allinea.py`. Crea `.venv`, installa le dipendenze e l'hook di `pre-commit` e copia `backend/.env.example` in `backend/.env`, poi si ferma: metti utente e password del tuo PostgreSQL in `DATABASE_URL` e `DATABASE_URL_TEST` e rilancialo, che porta il database all'ultima migrazione. Poi `uv run python avvia.py` avvia tutto. I comandi uno per uno, il seed e le variabili di `.env` sono in [`backend/README.md`](backend/README.md); i controlli prima di una PR in [`docs/agenti/converge.md`](docs/agenti/converge.md) §1, rilanciati da GitHub a ogni PR.

Regole di lavoro (branch `feature/<id>-<breve>`, mai su `main`, PR rivista da un collega e unita dall'admin): [`AGENTS.md`](AGENTS.md). Prima di installare AdFlow in un ambiente reale: [`docs/sicurezza-accesso.md`](docs/sicurezza-accesso.md).
