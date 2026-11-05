# AdFlow Suite

Repository del progetto di fine tirocinio Full Stack AI: prepara e pubblica le campagne social degli artigiani di un consorzio, con l'AI che scrive piano e testi e un operatore che rivede e approva.

**Stato** (ADR-123): tutto chiuso dal 5 novembre 2026, senza una data di consegna. I lavori si aprono uno alla volta, su scelta del team.

## Si parte da qui

Dalla radice, ogni volta che riapri il progetto:

```bash
uv run python allinea.py
```

Aggiorna `main` (mai il branch di lavoro né le modifiche non salvate), installa le dipendenze cambiate e porta il database all'ultima migrazione; `--stato` mostra lo stato senza toccare nulla. In VS Code è il task predefinito (**Ctrl+Shift+B**, su macOS ⇧⌘B). Poi `uv run python avvia.py` avvia API, worker e frontend insieme; Ctrl+C li ferma.

**La prima volta** servono [uv](https://docs.astral.sh/uv/getting-started/installation/), PostgreSQL 16 con i database `adflow` e `adflow_test` e Node 22+; Python 3.11 lo scarica uv. `allinea.py` crea `.venv`, installa le dipendenze e l'hook di `pre-commit`, copia `backend/.env.example` in `backend/.env` e si ferma: si mettono utente e password di PostgreSQL in `DATABASE_URL` e `DATABASE_URL_TEST` e si rilancia. I comandi sono gli stessi su Windows, macOS e Linux e si lanciano uno alla volta.

## Dove si trova che cosa

| Dove | Che cosa ci trovi |
|---|---|
| [`backend/README.md`](backend/README.md) | Comandi del backend, controlli delle PR, prove a mano, dati e percorso della demo, Meta, produzione |
| [`frontend/README.md`](frontend/README.md) | Avvio del frontend, dati di esempio, struttura |
| [`AGENTS.md`](AGENTS.md) | Le regole di lavoro, per le persone e per gli agenti |
| [`docs/agenti/`](docs/agenti/) | Regole del codice (`constitution.md`), che cosa fa il prodotto (`spec.md`), com'è fatto (`plan.md`), storia degli sprint e corsia della presentazione (`tasks.md`) |
| [`docs/ADR.md`](docs/ADR.md) | Le decisioni, con il perché |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Ciò che resta fuori dall'MVP e ciò che manca per la produzione |
| [`docs/proposta-tecnica.md`](docs/proposta-tecnica.md), [`docs/pitch.md`](docs/pitch.md) | La proposta per il cliente e la scaletta del pitch |
| [`docs/archivio/`](docs/archivio/LEGGIMI.md) | La storia: pagine statiche, perimetro dell'MVP, sicurezza, simulazione di accettazione, brief, QA, testi completi |
