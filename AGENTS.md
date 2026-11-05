# AdFlow Suite · istruzioni per gli agenti

Monorepo: `backend/` (FastAPI + worker Procrastinate, PostgreSQL), `frontend/` (React + Vite + Mantine), `docs/`.

## Stato

Tutto è chiuso (ADR-123, 5 novembre 2026): gli sprint sono conclusi e non c'è una data di consegna. Non esiste un "prossimo task". I lavori si aprono uno alla volta, in modo chirurgico, quando la persona li sceglie in chat. Il blocco del codice dell'MVP (ADR-114) resta: ogni lavoro nuovo è una scelta esplicita della persona.

## Come lavori

- Fai ciò che la persona chiede in chat, e solo quello. Non proporre lavori presi dalla documentazione, non cercare in `tasks.md` che cosa fare, non riprendere le note di una sessione precedente. Se vedi altro da fare, dillo in una riga e lascia scegliere.
- Se la richiesta non è chiara o manca un'informazione, fermati e chiedi. Non inventare requisiti.
- Un lavoro alla volta, su un branch `feature/<breve>` (o quello che la persona indica), mai su `main`.
- Il codice congelato porta il commento "Congelato per l'MVP, ADR-114": lo tocchi solo se la persona lo chiede.
- I dati di un altro modulo si leggono solo dal suo `service.py` (plan §6): niente SQL scritto a mano sulle sue tabelle e niente copie delle sue costanti.
- Una libreria nuova entra in `backend/requirements.txt` con nome, motivo e licenza.
- Nei test nessuna chiamata reale ad AI, Meta o email.
- Se cambi composizione, `core/`, `alembic/`, `backend/requirements.txt` o un `domain.py`, scrivilo nella PR.
- Commit in italiano all'imperativo: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`.
- Non modificare `docs/archivio/`. Gli altri documenti si modificano solo se il lavoro lo chiede.

## La documentazione

È una fonte di conoscenza passiva: si consulta quando serve per capire il codice o il perché di una scelta, non dà indicazioni su che cosa fare né su che cosa leggere prima. Il codice resta la fonte; dove un documento e il codice non tornano, vale il codice, e lo segnali.

| Dove | Che cosa ci trovi |
|---|---|
| `docs/agenti/constitution.md` | Le regole che il codice rispetta (invarianti, architettura, sicurezza) |
| `docs/agenti/spec.md`, `plan.md` | Regole e criteri del prodotto; architettura con lo stato di ogni rotta e job, §6 funzioni tra moduli, §7 `core/` e fixture dei test |
| `docs/agenti/tasks.md` | La storia degli sprint, i limiti noti dello sprint 5, la corsia della presentazione |
| `docs/ADR.md`, `docs/ROADMAP.md` | Le decisioni con il perché; ciò che resta fuori dall'MVP e ciò che manca per la produzione |
| `docs/proposta-tecnica.md`, `docs/pitch.md` | La proposta per il cliente e la scaletta del pitch |
| `backend/README.md` | Comandi, prove a mano, dati e percorso della demo, Meta, produzione |
| `docs/archivio/` | La storia: pagine statiche, perimetro, converge, sicurezza, accettazione, brief, QA e i testi completi (mappa in `LEGGIMI.md`) |

## Comandi

Serve `uv`: `uv run` usa `.venv` senza attivarlo, così i comandi sono gli stessi su Windows, macOS e Linux. Si lanciano uno alla volta (`&&` non funziona in ogni shell).
Dalla radice: `uv run python allinea.py` prepara l'ambiente, anche la prima volta (aggiorna `main` senza toccare il lavoro in corso, crea `.venv`, installa le dipendenze, copia `backend/.env.example` in `backend/.env`, porta il database all'ultima migrazione). Lo stato dei task che stampa è storia.
Da `backend/`: `uv run uvicorn app.main:app --reload` avvia l'API; `uv run alembic upgrade head`, poi `uv run pytest`, poi `uv run black --check .` sono il controllo prima della PR; da `frontend/` `npm run lint` e `npm run build`. GitHub li rilancia a ogni PR (`.github/workflows/`).
