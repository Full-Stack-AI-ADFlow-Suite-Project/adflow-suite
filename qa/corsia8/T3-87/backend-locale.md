# T3-87: verifica backend locale — esito e limiti

Nessun test backend locale completato con risultato osservato. Nessun DB QA creato, migrazione, seed o server avviato da questo agente. Nessun URL, credenziale, PID server o log pytest disponibile. Nessun percorso API eseguito. T3-87 NON è attestato come completato.

Letti AGENTS.md, constitution, perimetro-mvp, converge (1 e 4), brief-interfaccia (1.5 e T3-87), configurazione e fixture. La fixture motore_test rifiuta nomi DB senza suffisso _test e svuota public: serve DB separato dedicato ai test. AI e Social sono forzati finti dalle fixture, email va sostituita esplicitamente con EmailFinto per un server QA.

Ostacolo: prima chiamata Node senza risultato, interrotta dal controller dopo attesa prolungata. Conteneva solo import Node, eventuale mkdir work/qa87 e verifica interprete Python sorgente/import dipendenze. Nessuna creazione DB o server era contenuta. Runtime successivamente resettato. Nessun output né PID restituito. Chiamata shell conclusiva di inventario terminata con codice 0 senza output.

Nessun codice prodotto modificato, merge, push, chiamata reale ad AI/Social/Meta/email o pubblicazione. Nessuna credenziale stampata o pubblicata. allinea.py non eseguito perché aggiorna main/database contro il mandato di QA isolata.

I PASS CI backend comunicati dal controller restano evidenza separata e non sono test PostgreSQL eseguiti localmente da questo agente. Restano aperti percorsi UI/API, prove negative, screenshot e confronto visivo. T3-86 richiede persone reali e non è svolto né simulato da agenti. Rami Draft non equivalgono a main integrato. Non assegnare il task come fatto sulla base di questo rapporto.
