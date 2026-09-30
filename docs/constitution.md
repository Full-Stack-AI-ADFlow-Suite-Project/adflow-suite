# Costituzione · AdFlow Suite

Regole **non negoziabili** per chiunque lavori sul progetto, persona o agente AI. Vengono prima di ogni altro documento: se un task, una richiesta o un pezzo di codice le contraddice, ci si ferma e si apre una discussione.

Il metodo di lavoro è **spec-driven**: prima si scrive cosa e perché, poi come, poi i task, poi il codice, poi la verifica.

| Fase | Documento | Contenuto |
|---|---|---|
| Costituzione | `docs/constitution.md` (questo) | Regole non negoziabili, standard, sicurezza, modo di lavorare |
| Spec | [`docs/spec.md`](spec.md) | **Cosa** fa il prodotto e **perché**: flusso, regole, criteri di accettazione. Niente tecnologia |
| Plan | [`docs/plan.md`](plan.md) | **Come** lo costruiamo: stack, architettura, modello dati, API, job |
| Decisioni | [`docs/ADR.md`](ADR.md) | Registro delle decisioni architetturali, una riga per decisione |
| Tasks | [`docs/tasks.md`](tasks.md) | Checklist ordinata di micro-task, con dipendenze |
| Implement | §6 di questo file | Come si esegue un task |
| Converge | [`docs/converge.md`](converge.md) | Come si verifica che un task e uno sprint siano davvero finiti |
| Allegati | `docs/architettura/` | Diagrammi (sorgente `AdFlow-diagrammi.html`) e pagine statiche di riferimento |

---

## 1. Principi di prodotto (invarianti)

Il codice non può mai violarli, nemmeno temporaneamente. Ognuno ha almeno un test (vedi `converge.md`).

1. **Nessun post esce senza approvazione.** Si pubblica solo un post `approvato`, e si approva solo la campagna intera (spec R-01, R-14).
2. **Niente si cancella dalla storia.** Versioni dei post, versioni delle foto, decisioni e campagne respinte o scadute restano nel database (ADR-12, ADR-40).
3. **La foto originale non si perde mai.** Ogni ritocco è una nuova versione; la versione 0 è l'originale caricato (R-17).
4. **La campagna usa la fotografia del profilo** salvata all'invio, mai il profilo corrente (R-11, ADR-24).
5. **Dopo l'approvazione nessuna modifica** ai post: si sospende o si annulla (R-16, ADR-44).
6. **Il testo cambia solo passando dall'AI e dal validatore**: niente modifica a mano (ADR-42).
7. **La pubblicazione è idempotente**: il tentativo si registra prima di chiamare il social, e c'è al massimo un esito `ok` per post (ADR-13).
8. **Gli stati cambiano solo tramite `verifica_transizione()`** e solo lungo le transizioni scritte in `plan.md` §3.

## 2. Architettura non negoziabile

- **Monolite modulare + worker**, stesso codice Python (ADR-01). Niente microservizi, niente servizi aggiuntivi senza una nuova ADR.
- **Dipendenze ammesse:** `api → services → adapters`; tutti possono usare `domain` e `models`. Mai il contrario.
- **Nessuna logica di business** nei router FastAPI né nei task del worker: stanno nei `services`.
- **Ogni servizio esterno sta dietro un adattatore** (AI, social, email, archivio foto) e ha un'implementazione finta per sviluppo e test (ADR-06, ADR-07).
- **`domain.py` è l'unica fonte** di valori ammessi, stati e transizioni. Frontend e backend non ripetono queste liste a mano: il frontend le riceve dai tipi di `api.ts`.
- **Il database cambia solo con migrazioni Alembic.** Mai modifiche manuali allo schema.

## 3. Sicurezza

- **Segreti solo in `backend/.env`**, mai in git. `.env.example` si aggiorna a ogni nuova variabile, con valori finti.
- **Password** con scrypt. **Sessione**: il cookie `adflow_sessione` è httpOnly e contiene il token; nel database c'è solo il suo hash (ADR-05).
- **Permessi sempre controllati sul server**, a ogni richiesta: 401 senza sessione, 403 ruolo sbagliato, **404 per le risorse di un altro artigiano** (non si rivela che esistono).
- **Upload**: si controllano tipo reale del file, peso e dimensioni prima di salvarlo; i nomi dei file sul disco li genera il server.
- **Permessi dei social** salvati cifrati. Nessun dato personale (email, testi delle campagne, token) nei log.
- **Nessuna chiamata AI, social o email reale nei test**: si usano gli adattatori finti. Le chiavi reali servono solo per la prova manuale.
- Nessuna libreria nuova senza dirlo nella PR (nome, motivo, licenza).

## 4. Standard di codice

- **Lingua**: nomi di dominio in **italiano** (tabelle, campi, funzioni, messaggi); termini tecnici standard in inglese (`router`, `task`, `schema`).
- **Backend**: Python 3.11+, type hints ovunque, SQLAlchemy 2 (`Mapped`), Pydantic per il contratto API, formattazione `black` tramite pre-commit.
- **Date** salvate in UTC (`timestamptz`); il fuso Europe/Rome si usa solo per calcolare slot e scadenze.
- **Errori API**: un solo formato, `{"detail": "messaggio in italiano"}`. Codici: 401, 403, 404, 409 stato non valido, 422 dati non validi.
- **Frontend**: TypeScript strict, Mantine, niente librerie di stato globale; i tipi in `api.ts` rispecchiano `schemas.py`.
- **Test**: ogni regola di business porta con sé il suo test; i test girano su PostgreSQL reale (database `adflow_test`), mai su SQLite.

**Struttura del repository**
```
adflow-suite/
├─ CLAUDE.md · AGENTS.md   istruzioni per gli agenti AI (rimandano qui)
├─ docs/                   constitution · spec · plan · ADR · tasks · converge · architettura/
├─ backend/
│  ├─ app/
│  │  ├─ api/        router FastAPI: solo HTTP, permessi e conversione dati
│  │  ├─ services/   logica di business (generazione, revisione, pubblicazione, validatore)
│  │  ├─ adapters/   servizi esterni dietro interfacce: ai, social, email, archivio, prompts
│  │  ├─ worker/     Procrastinate: app, task (involucri sottili sui services), avvio
│  │  ├─ domain.py   valori ammessi e macchine a stati (unica fonte)
│  │  ├─ models.py   tabelle SQLAlchemy · schemas.py contratto API · config.py · db.py
│  │  └─ coda.py     accodamento job dall'API · security.py · cli.py · main.py
│  ├─ alembic/      migrazioni
│  └─ tests/        pytest su PostgreSQL reale
└─ frontend/src/    api.ts (client + tipi) · auth.tsx · pages/ · components/
```

## 5. Documenti e decisioni

- **Una sola fonte per ogni informazione**: il *cosa* sta in `spec.md`, il *come* in `plan.md`, le decisioni in `ADR.md`. Non si copia: si rimanda.
- **Cambiare una decisione** = nuova riga in `ADR.md` (mai cancellare le vecchie, si segnano "Sostituita da") **e** aggiornare `spec.md` / `plan.md` **nella stessa PR**.
- Se il codice deve discostarsi dai documenti, prima si cambiano i documenti.
- I diagrammi si modificano solo in `architettura/AdFlow-diagrammi.html` e si rigenerano con gli strumenti in `architettura/strumenti/` (vedi `LEGGIMI.md`).

## 6. Implement · come si esegue un task

1. **Si prende un task** da `tasks.md` che sia libero e con tutti i prerequisiti chiusi. Si scrive il proprio nome nella colonna "Assegnato a" (in una PR piccola o nella PR del task).
2. **Un task = un branch = una PR.** Nome del branch: `feature/<id>-<breve>` (esempio `feature/T1-04-login`). Mai lavorare su `main`.
3. **Si leggono prima** questa costituzione, la riga del task e le sezioni di `spec.md` e `plan.md` che il task cita. Niente di più, niente di meno.
4. **Si fa solo il task.** Un problema trovato fuori dal task diventa un nuovo task o una domanda, non una modifica nella stessa PR.
5. **Se manca un'informazione o due documenti si contraddicono**, ci si ferma e si chiede nel gruppo (o si apre una domanda nella PR). Un agente AI non inventa requisiti.
6. **Commit piccoli**, in italiano all'imperativo, con prefisso `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`.
7. **Prima di aprire la PR** si esegue la checklist del task in `converge.md` §1 e si spunta la casella del task in `tasks.md`.
8. **La PR** descrive cosa fa, quali criteri di accettazione (`CA-xx`) copre e come si prova. La rivede almeno un'altra persona; il merge lo fa l'admin.

## 7. Definizione di "fatto"

Un task è fatto quando:
- il suo criterio "Fatto quando" in `tasks.md` è vero;
- `pytest` è verde e `npm run build` compila (e `npm run lint` non segnala errori);
- i criteri di accettazione citati hanno un test che passa;
- nessun principio di questa costituzione è violato;
- documenti, `.env.example` e README sono aggiornati se il task li tocca;
- la PR è stata rivista e unita a `main`.

## 8. Git

- `main` è protetto: si entra solo con una Pull Request rivista.
- Prima di iniziare un task: `git checkout main`, `git pull`, poi il branch del task.
- Al primo setup: `pre-commit install` (formatta il codice a ogni commit).
- Conflitti: si risolvono sul proprio branch portando dentro `main`, mai forzando il push su branch altrui.
