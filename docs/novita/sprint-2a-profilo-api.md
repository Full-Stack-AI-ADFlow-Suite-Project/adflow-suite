# Sprint 2a · API del profilo della bottega

Prima parte della Corsia 1 avviata su richiesta di Gianluca in questa sessione.
Lo sprint 2 non ha ancora task numerati in tasks.md: la PR resta in bozza per la
formalizzazione e la revisione di gruppo. Non si spunta alcun task dello sprint 1.

## Comportamento

- GET /api/profilo legge solo il profilo dell'artigiano autenticato; 404 se assente.
- PUT /api/profilo crea o sostituisce i dati del proprio profilo; risposta 200.
- Campi obbligatori e valori ammessi seguono plan §2 e artigiani/domain.py.
- Gli errori 422 sono in italiano e indicano i campi senza riflettere valori personali.
- id, utente_id, logo e aggiornato_il non sono scrivibili dal client.
- Il salvataggio è completo: gli opzionali omessi diventano null. Il logo esistente
  resta invariato; la sua gestione avrà un endpoint da concordare.
- Scegliere un canale nel profilo non collega un account social. Il vincolo degli
  account collegati rimane sulle campagne, come da R-22.
- Un upsert PostgreSQL protegge anche le prime scritture concorrenti. Nessun commit
  nel service; il router usa la sessione comune con scope function.
- Ora UTC iniettata; GET non aggiorna il profilo. Gli snapshot delle campagne e i
  permessi degli account social restano invariati.

## Verifica

Test API del profilo assente, creazione e modifica, isolamento, campi obbligatori,
valori del dominio, JSON annidato, Unicode malformato, numeri non finiti, campi
non scrivibili, rollback, concorrenza e ruoli con cookie reale.
Supporto backend a CA-05/06/07 e preservazione dello snapshot di CA-16: le pagine
frontend e la prova della generazione/Riprova restano alle rispettive corsie.

I test usano solo PostgreSQL locale adflow_test, controllato anche con
current_database(). DATABASE_URL viene temporaneamente sostituito con l'URL di
test prima di importare l'app. .env non viene modificato e nessuna connessione
viene aperta al database applicativo. Nessuna nuova dipendenza.

## Lavori successivi e dipendenze

- Archivio: foto e gruppi sono di campagne; foto_di_archivio() è ancora una firma
  da fissare in Corsia 0. Artigiani non può importare il modulo campagne successivo.
  Formalizzare la lettura e la gestione dei gruppi senza campagna con Corsia 2.
- Logo: concordare percorso API, validazione, lettura del file e politica di
  sostituzione, riusando l'adattatore archivio esistente.
- Notifiche: manca models.py e la relativa migrazione; notifiche.crea() resta un
  contratto futuro della Corsia 0. Formalizzare dati/eventi prima di implementare
  il job email di Corsia 1 e gli agganci nei moduli delle altre corsie.
- Pagine Profilo e Campagna: Corsia 5.

Non vengono cambiati core, composizione, modelli, migrazioni, domain, fabbriche,
funzioni comuni di plan §6, requirements o documenti docs/agenti.
