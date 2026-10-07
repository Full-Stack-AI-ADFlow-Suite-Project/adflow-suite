# Novità · T1-11–13 Verifica finale e HTTP reale

7 ottobre 2026 · corsia 1 · branch `feature/T1-11-13-auth`

## Difetti riprodotti e corretti in questa revisione
- Email storiche uguali salvo maiuscole/minuscole: il vincolo DB consenteva
  due record, mentre il login normalizzava l'email e prendeva arbitrariamente
  il primo. Il login ora richiede esattamente una corrispondenza; un'identità
  ambigua riceve lo stesso 401 generico delle credenziali errate. Una singola
  email preesistente con maiuscole continua a funzionare. Nessun dato storico
  è modificato e nessuna migrazione è aggiunta.
- Record pendenti del chiamante sotto `no_autoflush`: `begin_nested()` esegue
  comunque un flush prima del savepoint. Un errore di unicità su un record
  già pendente era erroneamente tradotto come duplicato della nuova email.
  Il flush preliminare è ora fuori dalla gestione degli errori del nuovo
  utente, così gli errori del chiamante propagano correttamente. Gli inserimenti
  validi, vecchi e nuovi, restano annullabili insieme nella transazione esterna.

Prima delle correzioni i tre casi di regressione erano falliti; dopo sono
passati. Aggiunte anche due prove positive sui comportamenti da conservare.
Restano verdi le precedenti correzioni su risposte 422 senza credenziali,
Unicode/NUL, autenticazione, permessi, revoca e concorrenza.

## Prova HTTP con server reale
`test_auth_http_reale.py` avvia un processo Uvicorn separato su una porta
locale temporanea, con l'app reale `app.main:app`. Nessun override di dipendenze
nel server. Il client invia richieste TCP, gestisce i cookie e verifica login,
me, login fallito, rotazione, token precedente revocato, logout, cancellazione
del cookie ed errori 422 senza credenziali.

DATABASE_URL è impostato soltanto nell'ambiente del processo figlio e coincide
con DATABASE_URL_TEST. Prima di avviare Uvicorn il figlio verifica esattamente
`127.0.0.1:5432/adflow_test` e `current_database()`. Anche il processo dei test
verifica il database. Nessuna modifica a `.env`, al servizio PostgreSQL o al
database adflow. Server terminato e atteso nel finally; dati sintetici rimossi.

## Esiti effettivi
- Suite completa: **384 test passati**, zero fallimenti; 6 nuove verifiche
  rispetto ai 378 precedenti. Tempo osservato: 64,94 secondi.
- Black: **103 file conformi**, esclusa soltanto `.pytest_cache` inaccessibile.
- `git diff --check` senza errori.
- Rapporto automatico JUnit salvato come `test-finali-auth.xml` nei deliverable.
- Windows Selector e `-p no:cacheprovider`, senza modificare permessi della cache.

Non sono prove di browser o proxy HTTPS di produzione; i flag HTTPS restano
coperti dai test ASGI già presenti. Durata sessione 8 ore da rivedere nel gruppo.
Nessuna modifica a core, modelli, migrazioni, composizione o dipendenze.
La chiusura formale dei task richiede revisione del gruppo e merge admin.
