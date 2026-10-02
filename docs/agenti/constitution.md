# Costituzione

Regole non negoziabili. Se un task le contraddice, fermati e chiedi.

## 1. Invarianti del prodotto
1. Si pubblica solo un post `approvato`; si approva solo la campagna intera.
2. Niente si cancella: versioni di post e foto, decisioni, campagne respinte o scadute restano.
3. La foto originale (versione 0) non si perde mai.
4. Generazione e rigenerazioni usano `campagna.profilo_snapshot`, mai il profilo corrente.
5. In campagna `attiva` o `sospesa` nessuna modifica ai post.
6. Il testo di un post cambia solo tramite AI + validatore: niente modifica a mano.
7. Pubblicazione idempotente: il tentativo si registra prima di chiamare il social; al massimo un `ok` per post.
8. Gli stati cambiano solo nel modulo proprietario e solo con `verifica_transizione()` (transizioni in plan §2).

## 2. Architettura
Monolite a moduli + worker: stesso codice Python, un database, una catena di migrazioni Alembic. Nessun servizio nuovo.

```
backend/app/  main.py · worker.py · cli.py · tabelle.py            (composizione)
backend/app/core/  config.py · db.py · coda.py · security.py · transizioni.py · errori.py · orologio.py
backend/app/adapters/  ai/ · social/ · email/ · archivio/
backend/app/moduli/<modulo>/  router.py · service.py · models.py · schemas.py · domain.py · jobs.py   (solo quelli che servono)
backend/alembic/
backend/  requirements.txt · .env.example · alembic.ini · pytest.ini
backend/tests/  conftest.py · moduli/<modulo>/ (con fabbrica.py) · adapters/ · percorsi/ · test_confini.py
frontend/src/  api/<modulo>.ts · api/esempi/ · auth.tsx · pages/{artigiano,operatore}/ · components/
```

Ordine dei moduli: `accesso`, `notifiche`, `artigiani`, `campagne`, `contenuti`, `revisione`, `pubblicazione`.

1. Un modulo importa da un altro modulo solo `service` (e gli schemi che restituisce), e solo se l'altro lo **precede**. Mai `models`, `router`, `jobs` altrui. Ciò che un service altrui restituisce si legge, non si modifica.
2. Dentro il modulo: `router.py` e `jobs.py` chiamano `service.py`, che usa `core` e `adapters`. Nessuna logica di business nei router né nei job.
3. Tra moduli solo `ForeignKey`; `relationship()` solo dentro il modulo.
4. Lo stato della campagna cambia solo in `campagne.service.cambia_stato()`, quello del post solo in `contenuti.service`. Stati, transizioni e valori ammessi stanno nel `domain.py` del modulo proprietario, senza copie.
5. Verso un modulo successivo solo con `core.coda.accoda(nome, …)`.
6. I service non fanno `commit`: la sessione la apre e la chiude il router o il job.
7. Un endpoint o job che usa più moduli vive nel modulo più avanti tra quelli che gli servono.
8. Solo la composizione conosce tutti i moduli.
9. Ogni servizio esterno (AI, social, email, archivio) sta dietro un adattatore con un'implementazione finta.
10. I test preparano i dati di un altro modulo con la sua `fabbrica.py`. `tests/test_confini.py` controlla gli import: deve restare verde.

## 3. Sicurezza
- Segreti solo in `backend/.env` (mai in git); ogni nuova variabile va in `.env.example` con un valore finto.
- Password con scrypt; cookie `adflow_sessione` httpOnly; nel database solo l'hash del token.
- Permessi controllati sul server a ogni richiesta: 401 senza sessione, 403 ruolo, 404 per risorse di un altro artigiano.
- Upload: controllo di tipo reale, peso e dimensioni; il nome del file lo genera il server.
- Permessi social cifrati. Nessun dato personale o token nei log.
- Nei test nessuna chiamata reale ad AI, social o email.
- Una libreria nuova si dichiara nella PR (nome, motivo, licenza).

## 4. Standard
- Dominio in italiano (tabelle, campi, funzioni, messaggi); termini tecnici in inglese.
- Python 3.11+, type hints, SQLAlchemy 2 (`Mapped`), Pydantic, `black`.
- Date in UTC (`timestamptz`); Europe/Rome solo per slot e scadenze.
- Errori API: `{"detail": "messaggio in italiano"}`; 401 / 403 / 404 / 409 stato non valido / 422 dati non validi.
- Frontend: TypeScript strict, Mantine, niente stato globale; i tipi di `api/<modulo>.ts` rispecchiano lo `schemas.py` del modulo.
- Test su PostgreSQL reale (`adflow_test`), mai SQLite; l'ora "adesso" si inietta (`core/orologio.py`).

## 5. Corsie e fatto
- Ogni file ha una corsia proprietaria (`tasks.md`). La corsia 0 è di tutto il team: composizione, `core/`, `alembic/`, e di ogni modulo `models.py`, `domain.py` e le funzioni di plan §6 scritte nella corsia 0. Si cambiano solo con un task della corsia 0.
- Un task è fatto quando il suo "Fatto quando" è vero, la checklist di `converge.md` è verde e la PR è unita dall'admin dopo la revisione: approvazione di tutto il team per la corsia 0, revisione di gruppo per le corsie 1–5.
