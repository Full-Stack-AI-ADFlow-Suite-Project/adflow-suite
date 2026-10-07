# Novità · T1-11–13 Preparazione della revisione

7 ottobre 2026 · Gianluca · corsia 1 · branch `feature/T1-11-13-auth`

Le caselle T1-11, T1-12 e T1-13 in `docs/agenti/tasks.md` sono spuntate per
la PR, come richiesto da tasks.md e converge.md. Indicano implementazione e
verifiche completate sul branch: la chiusura formale richiede ancora revisione
del gruppo e merge dell'admin. Non sono stati modificati i task delle altre corsie.

## Controllo prima della PR
- Base remota aggiornata e compatibile; nessun commit di `origin/main` mancante.
- Ultima suite: **384 test passati**, zero fallimenti/errori/test saltati.
- Black: **103 file conformi**, esclusa soltanto `.pytest_cache` inaccessibile.
- Diff senza errori di spaziatura; CA-01, CA-02 e CA-03 coperti.
- Verificato esattamente `127.0.0.1:5432/adflow_test` e `current_database()`.
  Fixture con migrazioni 001–007, wrapper Windows Selector, cacheprovider disabilitato.
- Prova HTTP con Uvicorn separato e transazioni PostgreSQL reali inclusa nella suite.
- Nessuna nuova dipendenza, migrazione o modifica a core/modelli/composizione.
- Frontend non presente nella copia di lavoro e non modificato: lint/build non eseguiti.
- Main locale e branch di integrazione conservano il lavoro `2535a42`.

## Decisioni richieste ai revisori
- Approvare la durata iniziale di 8 ore della sessione.
- Confermare che i follow-up seguenti siano condizioni obbligatorie prima del
  rilascio in produzione, pur consentendo il merge dello sprint dopo la revisione.
- Confermare gli assegnatari operativi delle attività della corsia 0.

## Follow-up registrati su GitHub
1. [#16 · Rate limiting (corsia 0/1)](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/issues/16).
   Controlli per IP e account, politica da approvare, concorrenza e limiti dello
   storage. Nessun servizio nuovo; memoria locale non condivisa tra worker.
2. [#17 · Proxy HTTPS e cookie Secure (corsia 0)](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/issues/17).
   Proxy fidato, header contraffatti rifiutati e verifica staging della catena HTTPS.
3. [#18 · Logging auth senza dati personali (corsia 0)](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/issues/18).
   Eventi distinti, request_id validato e test della serializzazione effettiva.
4. [#19 · Validazione email (corsia 1)](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/issues/19).
   email-validator, compatibilità degli account, nessun DNS al login; `.test`
   richiede test_environment oppure una scelta di fixture approvata.

Queste attività non sono implementate in questa PR. Nuove variabili comuni,
tabelle/migrazioni, logger globale e deployment richiedono coordinamento e
approvazione della corsia 0. Nessuna modifica implicita della politica di sicurezza.
