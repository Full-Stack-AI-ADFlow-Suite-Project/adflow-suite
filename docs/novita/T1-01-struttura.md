# Novità · T1-01 Struttura del backend

2 ottobre 2026 · branch `feature/T1-01-struttura` · corsia 0 (serve l'approvazione di tutto il team)

## In breve
Nasce `backend/`: l'API si avvia, risponde su `/api/health`, e ogni corsia trova già la cartella del suo modulo e gli strumenti comuni. Non c'è ancora nessuna tabella e nessuna funzione di prodotto: quelle arrivano con T1-02…T1-06.

## Cosa c'è adesso
- **Sette moduli** in `backend/app/moduli/` (accesso, notifiche, artigiani, campagne, contenuti, revisione, pubblicazione), ognuno con `router.py`, `service.py` e `jobs.py` vuoti.
- **Quattro adattatori** in `backend/app/adapters/` (ai, social, email, archivio), per ora cartelle vuote.
- **Composizione**: `main.py` monta i router sotto `/api`; `worker.py` importa i job; `tabelle.py` raccoglie i modelli per Alembic.
- **Strumenti comuni** in `core/`: configurazione, sessione del database, errori, ora corrente, controllo dei cambi di stato.
- **Alembic** configurato, ancora senza migrazioni.
- **Test**: 28, tutti verdi. Comprendono `test_confini.py`, che controlla le regole di import tra moduli.

## Cosa cambia per chi lavora
1. **Installazione**: le istruzioni sono nel README. L'ambiente virtuale è `.venv` nella radice del repository.
2. **Il file `backend/.env` è obbligatorio**: senza `DATABASE_URL` e `DATABASE_URL_TEST` l'applicazione non parte. Si copia da `.env.example`.
3. **Gli indirizzi del database iniziano con `postgresql+psycopg://`** (driver psycopg 3).
4. **`pytest` svuota `adflow_test` a ogni esecuzione** e ci applica le migrazioni. Non metterci dati da conservare.
5. **Nei test** si usano le fixture `db` (sessione annullata a fine test) e `client` (per chiamare l'API).
6. **Nei service** gli errori si sollevano con le classi di `core/errori.py` (`NonTrovato`, `StatoNonValido`, …): la risposta `{"detail": "messaggio"}` la costruisce `main.py`.
7. **Nessuno chiama `commit`**: lo fa `core/db.py` alla fine della richiesta o del job.
8. **Gli endpoint si scrivono senza `/api`**: il prefisso lo aggiunge `main.py`.

Il dettaglio di ogni strumento è in `docs/agenti/plan.md` §7.

## Scelte prese in questa PR
- **Configurazione completa da subito**: `core/config.py` contiene tutte le variabili di plan §1, così le altre corsie non devono toccare `core/`.
- **Nessuna password nel codice**: gli indirizzi del database non hanno un valore predefinito.
- **Niente tabelle e niente migrazioni**: sono del task T1-03.
- **Niente Procrastinate per ora**: la coda è del task T1-05.
- **I test applicano le migrazioni vere**, invece di creare le tabelle dai modelli: così un errore in una migrazione si vede subito.
- **`black` fissato alla 23.3.0**, la stessa versione del pre-commit.

## Librerie aggiunte
| Libreria | Perché | Licenza |
|---|---|---|
| fastapi | API | MIT |
| uvicorn | server dell'API | BSD-3-Clause |
| pydantic-settings | lettura di `.env` | MIT |
| SQLAlchemy | modelli e query | MIT |
| psycopg | driver PostgreSQL | LGPL-3.0 |
| alembic | migrazioni | MIT |
| pytest | test | MIT |
| httpx2 | client dei test dell'API | BSD-3-Clause |
| black | formattazione | MIT |
| pre-commit | controlli a ogni commit | MIT |

## Documenti aggiornati
- `README.md`: installazione e avvio del backend.
- `AGENTS.md`: comandi e rimando a plan §7.
- `docs/agenti/plan.md`: driver e ambiente in §1; nuova §7 "Base comune".
- `docs/agenti/constitution.md`: file di `backend/` e `conftest.py` nell'albero di §2.
- `docs/agenti/converge.md`: ambiente dei controlli e fixture dei test.
- `docs/agenti/tasks.md`: casella di T1-01 spuntata.
- `docs/agenti/spec.md`: nessuna modifica (il task non tocca il comportamento del prodotto).

## Come si prova
Da `backend/`, con `.venv` attivo e `.env` compilato:

```bash
alembic upgrade head && pytest && black --check .
uvicorn app.main:app --reload
```

Poi `http://localhost:8000/api/health` deve rispondere `{"stato":"ok"}`.

## Da sapere
Esiste anche il branch `feature/T1-01-struttura-modulare` di Nilton sullo stesso task, senza PR aperta. Questo branch riparte da `main` e segue i nomi della costituzione (`moduli/`, `accesso`); il team deve decidere quale dei due tenere.
