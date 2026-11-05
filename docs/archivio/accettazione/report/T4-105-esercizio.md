# T4-105 · Esercizio: processi locali, backup e ripristino, osservabilità

Copre §6 (backup e documentazione operativa), §7.4 (guasti) e §7.5
(osservabilità). «Staging» = processi locali (domanda 4 della §12).

## 1. Avvio su processi locali

La procedura scritta in `README.md` e `docs/sicurezza-accesso.md` funziona:
`allinea.py`, `alembic upgrade head`, `uvicorn app.main:app`, worker
Procrastinate con `python -m procrastinate -a app.worker.app worker`, proxy TLS
temporaneo come in `tests/moduli/accesso/test_proxy_http_reale.py`. La prova è
nella ricostruzione di T4-101 (API e worker partono, `/api/health` risponde).

- **ZAP baseline**: **non eseguito** in questa sessione (ZAP non è installato e
  la prova richiede il proxy TLS attivo per un tempo non breve). Il comando è
  documentato in `docs/sicurezza-accesso.md`; il risultato va aggiunto al
  registro appena c'è. Non è un difetto del prodotto.
- **Issue #17**: la parte locale è chiusa e provata (`test_proxy_http_reale.py`,
  verde); la verifica su un proxy di staging pubblico **manca** (RL-033).

## 2. Backup e ripristino, cronometrati (R-11)

Prova del 31/10/2026 sul database di sviluppo (sola lettura) e sulla sua
cartella `backend/archivio_foto`:

| Passo | Comando | Esito | Tempo |
|---|---|---|---|
| Backup del database | `pg_dump -Fc` | ok, 189 KB | **0,3 s** |
| Backup delle foto | `cp -a archivio_foto` | ok, **228 file** | **0,3 s** |
| Ripristino in un database nuovo | `pg_restore` in `adflow_ripristino` | ok | **0,5 s** |
| Verifica | conteggi di `utente`, `campagna`, `post`, `foto`, `chiamata_ai` e versione `alembic` | **identici** (4, 6, 108, 69, 209, `013`) | — |
| Pulizia | `DROP DATABASE adflow_ripristino` | ok | — |

Il ripristino **riesce** e i numeri coincidono. Due cose da dire in chiaro:

1. **I tempi non sono RTO/RPO reali**: il database di prova ha poche righe e
   228 foto. Con i volumi ipotizzati (2 000 artigiani, 12 foto per campagna) il
   dump e la copia delle foto crescono di ordini di grandezza.
2. **Il `pg_dump` da solo non è un backup** (R-11): le foto stanno su disco
   locale (`archivio_foto_dir`); senza copiare la cartella il ripristino perde
   l'archivio e le foto non escono più. La prova lo ha fatto copiando **due**
   beni: database **e** foto. Due istanze dell'app non vedono gli stessi file
   (RL-034).

## 3. Guasti provocati (i test sono in `backend/tests/accettazione/guasti/`)

| Guasto di §7.4 | Esito |
|---|---|
| PostgreSQL fermo | **500 invece di 503** (RL-028); il worker riparte (tick idempotente) |
| AI: timeout, 429, JSON malformato, vuota, lunghissima | per ogni tipo d'errore la campagna arriva a uno stato finale (`generazione_fallita` o `in_revisione`), mai a metà; la chiamata resta nello storico AI anche se fallisce (verde) |
| Meta: 5xx, 190, 368, 4/17/32/613, contenitore in errore | coperti dai test dell'adattatore (`tests/adapters/social/test_meta.py`); col finto: temporaneo → un solo tentativo riusato e riprova fino a `TENTATIVI_MAX` poi `fallito`; definitivo → `fallito` subito; `fallito` → riprogrammabile (verde) |
| Timeout **dopo** che Meta ha pubblicato (D-07) | **documentato com'è oggi**: ogni riprova è un post vero; dopo 3 il post è `fallito` (RL-025, blocco assoluto) |
| Worker ucciso durante una pubblicazione | il tentativo è nella stessa transazione del commit: se il processo muore **prima** del commit il tentativo sparisce e il tick ripubblica (RL-025); due worker sani non raddoppiano (T4-103, verde) |
| Disco pieno durante un upload | **500 generico invece di un errore chiaro** (RL-029); nessuna foto a metà, originale intatto |
| Email non consegnabile | il flusso principale non si blocca: la respinta passa e la notifica resta con il suo esito (verde) |
| Orologio: 28/03/2027, fine anno, 29/02/2028 | la scadenza di mezzanotte di Roma è giusta (23:00 UTC) in tutti e tre i casi (verde) |

## 4. Osservabilità (§7.5)

Che cosa si vede oggi:

| Misura | Dove | Giudizio |
|---|---|---|
| latenza per richiesta | log JSONL `adflow.http` (`duration_ms`, `status_code`, `request_id`) | c'è, ma riga per riga: nessuna aggregazione, nessun p95 |
| eventi di sicurezza | log JSONL `adflow.sicurezza` (`auth_failure`, `role_denied`, …) | c'è, stessa limitazione |
| coda di Procrastinate | tabella `procrastinate_jobs` (stato, tentativi, `scheduled_at`) | interrogabile a mano, nessuna pagina né metrica |
| ritardo di pubblicazione | differenza `data_ora`/`pubblicata_il` | calcolabile a mano, non misurata |
| costo AI | pagina Storico AI e «Vedi campagna» con il totale (R-44, R-50) | **c'è**, con i numeri per versione del prompt |
| metriche e allarmi | — | **mancano**: nessun endpoint `/metrics`, nessun allarme su errori, coda o spesa (RL-031) |

## 5. Rilievi di questo task

- **RL-028** (Media): PostgreSQL fermo → 500 invece di 503.
- **RL-029** (Bassa): disco pieno → 500 generico.
- **RL-031** (Media): nessuna misura aggregata né allarme su latenza, coda e
  spesa AI; le prove di carico di §7.2 non sono state eseguite (non provato).
- **R-11 → RL-034** (Media in produzione): le foto su disco locale; il backup
  deve copiare due beni e due istanze non condividono i file.
- **R-09 → RL-032** (Alta in produzione): nessun artefatto di rilascio
  (container, compose, configurazione del proxy, rollback).
- **R-10 → RL-033** (Alta in produzione): la verifica su un proxy di staging
  pubblico manca (issue #17 aperta).
