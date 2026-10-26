# T3-86 — Protocollo della prova con due persone

**Stato: NON ESEGUITO.** Questo documento prepara la prova: non contiene sessioni svolte, partecipanti reclutati, osservazioni o risultati. La casella T3-86 resta aperta.

Riferimenti: [brief interfaccia, §2, §4 e T3-86](../../../docs/agenti/brief-interfaccia.md), [perimetro MVP, blocco I](../../../docs/agenti/perimetro-mvp.md), [converge](../../../docs/agenti/converge.md).

## Prima di iniziare

- La prova si svolge sull'app con le PR della corsia 8 **già unite a main**. Verificare l'integrazione effettiva di T3-83 (PR #142), T3-84 (PR #143) e T3-85 (PR #144, branch feature/T3-85-layout-telefono). Un branch stacked, una preview o i soli screenshot non soddisfano questo prerequisito. Qui non se ne certifica l'avvenuta integrazione.
- Selezionare due artigiani del consorzio; in mancanza, due persone fuori dal team che usano il telefono per lavoro. Ciascuna prova dura 30 minuti sul proprio telefono. Non sostituire una delle due persone con un membro del team.
- Predisporre per ogni sessione l'accesso artigiano e dati di prova coerenti con l'app: profilo già compilato, una campagna in corso riconoscibile, possibilità di iniziare una nuova campagna senza una bozza precedente e una campagna con richiesta aperta del consorzio. Rendere disponibili sul telefono tre foto di prova conformi ai requisiti mostrati dall'app. Non modificare regole, schermate o dati durante un compito per facilitarlo.
- Usare dati di prova senza informazioni personali non necessarie. Non annotare nome, email, telefono, password o credenziali. Identificare le sessioni soltanto come P1 e P2; annotare del dispositivo solo ciò che serve a capire un problema di resa.
- Prima della prima sessione annotare commit di main, data della verifica e indirizzo dell'ambiente nella scheda di esecuzione. Se mancano integrazione o dati necessari, non iniziare e registrare il prerequisito mancante: non è un esito della prova d'uso.

## Conduzione di ciascuna sessione — 30 minuti

| Minuti | Attività                                                                   |
| ------ | -------------------------------------------------------------------------- |
| 0–3    | Spiegare lo scopo e verificare che l'accesso all'ambiente sia disponibile. |
| 3–8    | Compito 1: entrare e trovare la campagna in corso.                         |
| 8–19   | Compito 2: preparare una nuova campagna con tre foto.                      |
| 19–26  | Compito 3: rispondere alla richiesta del consorzio.                        |
| 26–30  | Domande aperte e chiusura.                                                 |

Introduzione da leggere senza mostrare il percorso: «Stiamo provando l'app, non te. Usala come faresti da solo dal tuo telefono. Se ti va, racconta quello che cerchi e quello che ti aspetti. Puoi fermarti quando vuoi.»

Chi osserva non suggerisce dove toccare, non indica il menu o i pulsanti e non corregge gli errori. Annota dove la persona si ferma, che cosa sbaglia e che cosa dice, distinguendo i fatti dalle interpretazioni. Una domanda neutra ammessa è «Che cosa stai cercando di fare?», senza indicare la risposta.

Se la persona chiede aiuto, non sbloccare il compito con istruzioni: registrare la richiesta e l'eventuale mancato completamento autonomo. Al termine dello spazio previsto passare al compito successivo. Se serve un ripristino tecnico, interrompere e annotarlo: non segnare quel compito come completato senza aiuto.

### Le tre consegne

1. **«Entra nell'app e mostrami la campagna che è in corso.»** Osservare accesso, orientamento e riconoscimento dello stato. Conclusione osservabile: la persona individua e apre la campagna corretta senza indicazioni.
2. **«Prepara una nuova campagna con queste tre foto, come se dovessi proporla al consorzio.»** Osservare la scelta dell'azione iniziale, dati e canali, caricamento delle tre foto e comprensione del riepilogo. Conclusione osservabile: nuova campagna compilata con tre foto effettivamente caricate e riepilogo raggiunto. Annotare anche dove la persona ritiene di aver finito e registrare separatamente l’eventuale invio. Non suggerire passi né premere Invio al suo posto.
3. **«Il consorzio ti ha fatto una richiesta. Trovala, leggi che cosa chiede e rispondi.»** Osservare riconoscimento della richiesta, comprensione della domanda, eventuale sostituzione delle foto e dichiarazione richiesta dall'app, invio della risposta. Conclusione osservabile: la risposta risulta inviata; un caricamento iniziato o un testo non inviato non equivalgono al completamento.

### Domande aperte finali

Scegliere le domande utili nel tempo disponibile, senza proporre risposte:

- «In quale momento hai dovuto fermarti a capire che cosa fare? Raccontami che cosa cercavi.»
- «Come hai capito quale fosse il prossimo passo? Che cosa ti aspettavi dopo averlo scelto?»
- «Quali parole o messaggi ti sono rimasti poco chiari? Come li diresti tu?»
- «Come descriveresti l'aspetto dell'app? Che cosa ti sembra adatto o poco adatto al lavoro dal telefono?»
- «Che cosa cambieresti per poterla usare da solo in bottega?»

## Scheda di esecuzione — vuota

Da compilare soltanto dopo aver verificato i prerequisiti. Nessun campo è già un risultato.

| Campo                                | Dato da compilare |
| ------------------------------------ | ----------------- |
| Data della verifica dei prerequisiti |                   |
| Commit di main provato               |                   |
| Ambiente e indirizzo, senza segreti  |                   |
| PR della corsia effettivamente unite |                   |
| Dati di prova predisposti            |                   |
| Prerequisiti mancanti, se presenti   |                   |

### Sessione P1 — scheda vuota

| Campo                                                                    | Dato da compilare |
| ------------------------------------------------------------------------ | ----------------- |
| Data e orario; durata effettiva                                          |                   |
| Artigiano del consorzio / persona esterna che usa il telefono per lavoro |                   |
| Telefono, sistema e browser, solo se rilevanti                           |                   |
| Eventuale interruzione o aiuto ricevuto                                  |                   |

| Compito                         | Esito autonomo: completato / parziale / non completato / interrotto | Tempo impiegato | Fatti: punto di arresto, errore, tentativi | Parole della persona, se annotate alla lettera |
| ------------------------------- | ------------------------------------------------------------------- | --------------- | ------------------------------------------ | ---------------------------------------------- |
| 1 — campagna in corso           |                                                                     |                 |                                            |                                                |
| 2 — nuova campagna con tre foto |                                                                     |                 |                                            |                                                |
| 3 — richiesta del consorzio     |                                                                     |                 |                                            |                                                |

| Domanda finale | Risposta effettivamente raccolta |
| -------------- | -------------------------------- |
|                |                                  |
|                |                                  |
|                |                                  |

### Sessione P2 — scheda vuota

| Campo                                                                    | Dato da compilare |
| ------------------------------------------------------------------------ | ----------------- |
| Data e orario; durata effettiva                                          |                   |
| Artigiano del consorzio / persona esterna che usa il telefono per lavoro |                   |
| Telefono, sistema e browser, solo se rilevanti                           |                   |
| Eventuale interruzione o aiuto ricevuto                                  |                   |

| Compito                         | Esito autonomo: completato / parziale / non completato / interrotto | Tempo impiegato | Fatti: punto di arresto, errore, tentativi | Parole della persona, se annotate alla lettera |
| ------------------------------- | ------------------------------------------------------------------- | --------------- | ------------------------------------------ | ---------------------------------------------- |
| 1 — campagna in corso           |                                                                     |                 |                                            |                                                |
| 2 — nuova campagna con tre foto |                                                                     |                 |                                            |                                                |
| 3 — richiesta del consorzio     |                                                                     |                 |                                            |                                                |

| Domanda finale | Risposta effettivamente raccolta |
| -------------- | -------------------------------- |
|                |                                  |
|                |                                  |
|                |                                  |

## Dopo le due prove: decidere sulle evidenze

Compilare la tabella soltanto con osservazioni realmente raccolte. Non trasformare un'impressione dell'osservatore in una citazione della persona, non attribuire frequenze a una sola sessione e non presentare due prove come una misura statistica dell'intero consorzio.

| Evidenza e sessione | Interpretazione da verificare | Correzione proposta | Destinazione e motivo | Verifica successiva |
| ------------------- | ----------------------------- | ------------------- | --------------------- | ------------------- |
|                     |                               |                     |                       |                     |

- Una correzione di stile o di un testo consentito rientra nella corsia solo se rispetta il §1 del brief: stessi campi, validazioni, condizioni, stati, ordine, rotte e chiamate; testi fissi e messaggi del backend invariati. Prima di considerarla conclusa, applicare i controlli richiesti dal brief, acquisire le evidenze e verificare che sia su main.
- Se serve cambiare comportamento, percorso, campi, testi fissi o altro fuori da quei limiti, catalogare la proposta in [docs/ROADMAP.md](../../../docs/ROADMAP.md), con evidenza, problema e risultato desiderato; non implementarla in questo task. Riportare nel pitch soltanto quanto effettivamente imparato.
- Allegare alla PR di T3-86 le note delle due sessioni e i riferimenti alle correzioni su main o alle voci in roadmap. Una correzione solo proposta o su un branch non equivale a una correzione integrata.
- Verificare il controllo del §1.5 sulle eventuali correzioni e la checklist di converge. **Lasciare T3-86 aperto** fino a quando il suo «Fatto quando» è realmente soddisfatto. Il solo protocollo non chiude il task e non sostituisce T3-87.
