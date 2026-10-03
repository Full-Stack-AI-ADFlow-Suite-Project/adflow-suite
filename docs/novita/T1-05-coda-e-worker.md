# Novità · T1-05 Coda e worker (correzione)

3 ottobre 2026 · branch `feature/T1-05-fix-coda-e-worker` · corsia 0 (serve l'approvazione di tutto il team)

## In breve
La coda e il worker di T1-05 (PR #10) erano su `main` ma non funzionavano: il worker non partiva e `accoda()` falliva sul database vero. Ora il worker parte, il tick gira ogni minuto e un job accodato per nome viene eseguito. Il branch parte da quello di T1-06 (PR #13): va unito dopo #12 e #13.

## Cosa non andava
I test di T1-05 sostituivano la coda con un oggetto finto, quindi nessuno di questi errori si vedeva.

| Problema | Effetto | Correzione |
|---|---|---|
| `PsycopgConnector(dsn=…)`: il parametro si chiama `conninfo` | il worker usciva subito con `unexpected keyword argument 'dsn'` | `conninfo=` |
| L'indirizzo di `.env` inizia con `postgresql+psycopg://`, che psycopg non accetta | connessione rifiutata dopo 30 secondi di attesa | `indirizzo_psycopg()` toglie il nome del driver |
| Nessuna migrazione creava le tabelle di Procrastinate | nessun job si poteva scrivere né leggere | migrazione `007_coda.py` |
| `accoda()` leggeva `.id` da un numero, e la coda non veniva mai aperta | `AttributeError` e `AppNotOpen` nell'API | `accoda()` restituisce l'id e apre la coda al primo job |
| `tick_pubblicazione()` senza l'argomento `timestamp` che Procrastinate passa ai job periodici | il tick sarebbe fallito a ogni minuto con `TypeError` | `tick_pubblicazione(timestamp)` |
| Job `async` che chiamano service sincroni | un job `async` non può accodare un altro job (`RuntimeError`) e blocca il worker mentre lavora | il tick è una `def` normale |
| `worker.py` registrava job vuoti con i nomi di `genera_campagna`, `rigenera_post` e degli altri | il `jobs.py` di un modulo non poteva registrare il suo job (`TaskAlreadyRegistered`) senza toccare un file della corsia 0 | tolti: in `worker.py` resta solo il tick |

## Cosa cambia per chi lavora
1. **Ricrea le tabelle**: `alembic upgrade head` aggiunge la migrazione 007 (tabelle `procrastinate_*`).
2. **Un job si scrive nel `jobs.py` del suo modulo**, senza toccare `worker.py`:
   ```python
   from app.core.coda import GENERA_CAMPAGNA, app
   from app.core.db import transazione

   @app.task(name=GENERA_CAMPAGNA)
   def genera_campagna(campagna_id: int) -> None:      # def normale, non async
       with transazione() as db:
           ...                                     # chiama il service del modulo
   ```
3. **Si accoda per nome**: `accoda(GENERA_CAMPAGNA, campagna_id=campagna.id)` restituisce l'id del job.
4. **Nei test la coda è in memoria**, senza fare nulla: la fixture `coda` di `conftest.py` è attiva in ogni test. Per controllare che un job sia stato accodato:
   ```python
   def test_ca14_...(client, utente_di_prova, coda):
       ...
       [job] = coda.jobs.values()
       assert job["task_name"] == "genera_campagna"
       assert job["args"] == {"campagna_id": campagna.id}
   ```
5. **Avvio del worker** (README): `python -m procrastinate -a app.worker.app worker --concurrency 1`. Fino a T1-43 il tick finisce in errore a ogni minuto, perché `pubblica_dovuti()` è ancora uno stub: è atteso.

## Scelte da rivedere insieme
- **`accoda()` scrive il job subito, fuori dalla transazione di chi chiama.** Se la richiesta poi fallisce, il job resta in coda; e il worker può prenderlo prima del `commit`. Per ora: `accoda()` si chiama per ultima e il job controlla lo stato quando parte (per `genera_campagna` ci sono le 3 esecuzioni a 30 secondi di plan §4). Per accodare dentro la stessa transazione servirebbe `accoda(db, nome, …)`: cambia la firma approvata in T1-02, quindi è una decisione di tutti.
- **La migrazione 007 usa lo schema della versione di Procrastinate installata** (`procrastinate==3.10.0` in `requirements.txt`), senza copiarne l'SQL. Quando si cambia versione serve una migrazione nuova con gli script di aggiornamento di Procrastinate.
- **Le tabelle della coda stanno nello stesso schema del modello.** L'autogenerazione di Alembic le ignora con il filtro `del_modello()` di `tabelle.py`.
- **La coda dell'API si apre al primo `accoda()`**, non all'avvio: così `main.py` non cambia e i test con `client` non aprono connessioni al database di sviluppo.
- **Restano in `core/coda.py` i doppi nomi** `GENERA_CAMPAGNA` e `JOB_GENERA_CAMPAGNA`: scegliere una sola forma è un altro task.

## Documenti aggiornati
- `docs/agenti/tasks.md`: casella di T1-05 spuntata.
- `docs/agenti/plan.md` §7: righe di `core/coda.py`, `worker.py` e della fixture `coda`.
- `README.md`: nota sulle tabelle della coda e sul tick.
- `test_t103_tabelle.py`: la catena delle migrazioni arriva a 007.

## Come si prova
Da `backend/`, con `.venv` attivo e `.env` compilato:

```bash
alembic upgrade head && pytest && black --check .
python -m procrastinate -a app.worker.app healthchecks
python -m procrastinate -a app.worker.app worker --concurrency 1
```

283 test verdi. `test_job_di_prova_accodato_per_nome_ed_eseguito` usa la coda vera su `adflow_test`: connessione, schema, accodamento ed esecuzione. Nessuna libreria nuova, nessuna variabile nuova.
