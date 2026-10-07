# Novità · T1-12 Permessi

7 ottobre 2026 · corsia 1 · branch `feature/T1-11-13-auth`

`utente_corrente` legge il cookie attraverso la sessione PostgreSQL e l'orologio
iniettato. Restituisce 401 se il cookie manca, è sconosciuto, revocato, scaduto o
appartiene a un utente inattivo. Anche `/api/auth/me` usa questa dipendenza.

`richiede_ruolo(*ruoli)` mantiene il contratto esistente: prima autentica, poi
restituisce 403 se il ruolo non è ammesso. Nessun privilegio admin implicito:
il router deve includere esplicitamente `admin` nei ruoli ammessi, se previsto.
La fixture `utente_di_prova(ruolo)` continua a sostituire `utente_corrente`.

CA-03 è verificato via HTTP con cookie reale su una rotta isolata di test;
sono coperti anche operatore/admin ammessi, 401 e precedenza della scadenza
sul controllo dei ruoli. Nessuna modifica a composizione, core o fixture comuni.
La chiusura formale richiede revisione del gruppo e merge admin.
