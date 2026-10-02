# T1-03 · Tabelle dello sprint 1

## Risultato

Dieci tabelle nei sei moduli, con una catena Alembic 001–006. L'indice
`uq_pubblicazione_ok_post` impedisce più di un esito `ok` per post;
restano ammessi più tentativi con errore. Le migrazioni contengono lo
schema esplicito e non importano i modelli applicativi.

## Scelte da rivedere insieme nella PR della corsia 0

- Chiavi primarie intere; `foto.gruppo_id` è UUID.
- Nomi singolari come in plan §2. Nessuna relazione ORM tra moduli.
- Array PostgreSQL per liste omogenee; JSONB per snapshot, analisi AI,
  strutture del profilo, orari ed errori di validazione.
- Il profilo richiede i sette campi indicati nel piano e un utente unico.
  I dati descrittivi non obbligatori restano nullable. I dati copiati nella
  campagna all'invio possono essere null in bozza.
- Numero di versione unico per post. Le chiavi esterne non eliminano
  automaticamente versioni, decisioni o altri record collegati.
- Sono esclusi tabelle e campi contrassegnati come sprint 2b, 3 o 4.
  Stati, transizioni, valori di dominio e funzioni comuni arrivano con T1-04.
- Le fabbriche sono di base: ricevono la sessione `db`, fanno flush senza
  commit e generano dati fittizi indipendenti. L'hash scrypt nella fabbrica
  utente è solo per test: l'integrazione col formato di `core/security.py`
  è di T1-06. Le fabbriche di campagne e post non attestano il flusso API
  né una storia completa di approvazioni, che saranno completate in T1-04.

## Prove eseguite

Windows, Python 3.12, dipendenze di `backend/requirements.txt`, PostgreSQL
16.15 locale, database `adflow_test`, fuso del server UTC.

- `alembic upgrade head`: tutte le sei migrazioni applicate al DB vuoto.
- `pytest -q -W error`: **44 test superati**, inclusi i 28 già presenti.
- I test nuovi verificano downgrade completo e upgrade, downgrade -1 e
  nuovo upgrade, coerenza con i modelli, vincoli email/profilo/versione,
  chiavi esterne, campi obbligatori, token duplicato, date con fuso,
  JSON/array/UUID, default, decisioni/approvazioni, rollback delle fabbriche
  e rifiuto di un secondo ok per inserimento e aggiornamento.
- `black --check .`: superato.
- `alembic check`: nessuna differenza tra schema e modelli.

Da `backend/`, con `.venv` attivo e `.env` locale compilato:

```powershell
python -m alembic upgrade head
python -m pytest -q -W error
python -m black --check .
python -m alembic check
```

La fixture di T1-01 svuota il database di test prima delle prove. Usare
esclusivamente il proprio `adflow_test`. Nessun segreto è aggiunto a Git,
nessuna nuova libreria e nessuna chiamata ad AI, social o email.

L'implementazione resta soggetta alla revisione di tutto il team e al merge
di Nilton. Il task non ha CA autonomi; non certifica login o pubblicazione
verso servizi social, che appartengono ai task successivi.
