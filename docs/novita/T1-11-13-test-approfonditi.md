# Novità · T1-11–13 Test approfonditi

7 ottobre 2026 · corsia 1 · branch `feature/T1-11-13-auth`

## Problemi riprodotti e corretti
1. Gli errori di validazione FastAPI potevano includere la password ricevuta
   nell'input del dettaglio 422, anche quando mancava l'email. Il router di
   accesso ora intercetta soltanto gli errori di validazione delle proprie
   rotte e restituisce `{"detail": "Dati di accesso non validi."}`, senza input
   ricevuto e con `Cache-Control: no-store`. Coperti anche JSON malformato,
   body non oggetto, testo e form. La composizione comune resta invariata.
2. Byte NUL nei campi text e surrogati Unicode isolati causavano errori di
   PostgreSQL o di codifica. Validazione preventiva nel modulo accesso:
   email del login rifiutata con 422; creazione utenti con `DatiNonValidi`
   senza inserimenti. Password UTF-8 valide restano esattamente come inserite,
   compresi spazi, accenti, emoji e NUL (la password non è salvata come text).

Prima delle correzioni: 10 casi aggiuntivi falliti e 13 passati. Dopo le
correzioni gli stessi 23 casi sono tutti passati. Nessun segreto reale usato
nelle prove: soltanto credenziali e account sintetici.

## Copertura aggiunta
- Limiti password 1/1024 caratteri, Unicode e mancata normalizzazione.
- Hash password corrotti: 401 senza sessione creata.
- Input SQL ostili, ruolo/id nel body, hash DB usato come cookie e Bearer
  senza cookie: nessuna autenticazione o elevazione di privilegi.
- Vista utente nello schema OpenAPI senza password/hash/token.
- HTTP e CLI con il vero `get_db`/`transazione` del progetto, usando soltanto
  il motore adflow_test: commit osservabile da altra connessione e rollback
  della rotazione se la creazione del nuovo token fallisce.
- Revoca tra client distinti; modifiche di ruolo e disattivazione effettuate
  da altra connessione, applicate già alla richiesta successiva.
- Creazioni concorrenti della stessa email con 2/4/8 transazioni:
  un solo utente, duplicati controllati e transazioni ancora utilizzabili.
- Otto login da dispositivi distinti con 2/4/8 thread: token unici,
  sessioni persistite e logout che revoca soltanto la sessione indicata.

## Esiti
Suite finale su Windows: **378 test passati**, 40 verifiche aggiuntive
rispetto ai 338 precedenti. Black: **101 file conformi**. Diff senza errori.

Database verificato prima della suite: esattamente `127.0.0.1:5432/adflow_test`;
verificato anche `current_database()` e nelle fixture delle transazioni reali.
Nessuna operazione sul DB adflow. Policy Windows Selector,
`-p no:cacheprovider`; Black esclude `.pytest_cache` senza modificarne permessi.
Le prove HTTP usano TestClient ASGI e PostgreSQL reale: non sono una prova
di browser, proxy HTTPS o ambiente di produzione.

File aggiunti: `test_auth_casi_limite.py`, `test_auth_transazioni.py`.
Estesa la prova concorrente in `test_crea_utente.py`. Correzioni soltanto in
router, schemas e service di accesso; nessuna modifica alla corsia 0,
alle dipendenze, ai modelli, alla CLI o alle migrazioni.
