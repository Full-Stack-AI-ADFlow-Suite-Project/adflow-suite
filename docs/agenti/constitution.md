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
8. Gli stati cambiano solo con `verifica_transizione()` (transizioni in plan §2).

## 2. Architettura
- Monolite modulare + worker, stesso codice Python. Nessun servizio nuovo.
- Dipendenze: `api → services → adapters`; tutti possono usare `domain` e `models`.
- Nessuna logica di business nei router né nei task del worker.
- Ogni servizio esterno (AI, social, email, archivio) sta dietro un adattatore con un'implementazione finta.
- `domain.py` è l'unica fonte di stati, transizioni e valori ammessi.
- Schema del database solo tramite migrazioni Alembic.

```
backend/app/  api/ · services/ · adapters/ · worker/ · domain.py · models.py · schemas.py · config.py · db.py · coda.py · security.py · cli.py · main.py
backend/alembic/ · backend/tests/{unit,services,api,adapters}/
frontend/src/  api.ts · auth.tsx · pages/ · components/
```

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
- Frontend: TypeScript strict, Mantine, niente stato globale; i tipi di `api.ts` rispecchiano `schemas.py`.
- Test su PostgreSQL reale (`adflow_test`), mai SQLite; l'ora "adesso" si inietta.

## 5. Fatto
Un task è fatto quando il suo "Fatto quando" è vero, la checklist di `converge.md` è verde, la PR è rivista da un'altra persona e unita dall'admin.
