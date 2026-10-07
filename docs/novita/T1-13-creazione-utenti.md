# Novità · T1-13 Creazione utenti

7 ottobre 2026 · corsia 1 · branch `feature/T1-11-13-auth`

`accesso.service.crea_utente()` ora inserisce un utente attivo con password
scrypt, usando `core/security.py`. Email con spazi esterni rimossi e minuscole;
nome senza spazi esterni; ruoli ammessi: artigiano, operatore, admin.

Email duplicate (anche rispetto a email preesistenti con maiuscole), ruolo
non ammesso, email senza struttura minima, nome vuoto e password vuota o oltre
1024 caratteri producono `DatiNonValidi`. La verifica dell'email è sintattica
minima: non verifica DNS né consegna. Il limite password coincide con il login;
nessun nuovo requisito di complessità della password.

Il vincolo unico del DB è gestito anche se un'altra transazione crea la stessa
email dopo il controllo preventivo. Un savepoint preserva la transazione del
chiamante; il service non fa commit. Il vincolo esistente distingue maiuscole e
minuscole: la normalizzazione è nel service, senza nuove migrazioni.

La CLI esistente è utilizzabile da `backend/`:
```
python -m app.cli crea-utente --email persona@example.com --nome Persona --ruolo artigiano
```
La password viene richiesta e confermata a terminale, senza argomenti in chiaro.
Il seed resta invariato perché appartiene alla corsia 0.

Test sul database reale e comando CLI con il service reale (input password
simulato) in `tests/moduli/accesso/test_crea_utente.py`. Nessuna nuova dipendenza,
modifica a core, composizione, modelli o migrazioni. La chiusura formale richiede
revisione del gruppo e merge admin.

## Verifiche eseguite su Windows
- T1-11 + confini: 43 test passati.
- Accesso dopo T1-12 + confini: 53 test passati; suite completa: 314 passati.
- T1-13 + CLI: 33 test passati.
- Suite finale: **338 test passati**, non soltanto raccolti.
- Black: 99 file conformi, esclusa la cartella `.pytest_cache` inaccessibile.
- `git diff --check` senza errori.

Ogni esecuzione ha verificato `DATABASE_URL_TEST` verso
`127.0.0.1:5432/adflow_test`; la prima anche con `current_database()`.
Wrapper Windows con `asyncio.WindowsSelectorEventLoopPolicy()` e
`-p no:cacheprovider`. Le fixture hanno applicato le migrazioni su `adflow_test`.
Nessun test o creazione utente sul database `adflow`.
