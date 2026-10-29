# T3-926 · Pagine statiche della corsia 9

**Casella ☑, senza la rilettura di un collega.** Il «fatto quando» chiede pagine riviste da un collega: questa rilettura non c'è stata. I quattro punti «Da decidere» li ha decisi l'agente di chiusura, con il codice dell'app come riferimento; **la decisione spetta ai revisori della PR #166**, che confermano o correggono le righe di «Decisioni prese» qui sotto.

Riferimento usato: il codice del frontend (`stati.ts`, `StatoBadge.tsx`, `AvanzamentoCampagna.tsx`, `Guscio.tsx`, `Passo10.tsx`, `Rigenera.tsx`, `CambiaFoto.tsx`, `AzioniPost.tsx`, `StoricoAI.tsx`, `StoricoAIDettaglio.tsx`, `NumeriStorico.tsx`), `brief-richieste.md` §1.1–§1.7 e gli screenshot di `qa/corsia9/`. Le immagini in questa cartella sono le pagine statiche come si vedono ora, per chi rilegge.

## Pagine toccate, da far rileggere

| Pagina | Che cosa è cambiato | Da controllare |
|---|---|---|
| `AdFlow-operatore-storico-ai.html` (nuova) | Elenco con filtri, numeri, tabella per versione del prompt, due dettagli (riuscita con foto e voto, fallita); note con le rotte | Testi uguali a quelli dell'app; che l'elenco e il dettaglio (due pagine nell'app) stiano bene una sotto l'altra |
| `AdFlow-operatore-campagna.html` (Vedi campagna) | Etichette degli stati con spiegazione al passaggio del mouse; «Da correggere» al posto del badge del post con un blocco; barra di avanzamento (5 passi, errore, pausa, fermata, «3 di 5» sotto i 768 px); pulsanti «Modifica a mano», «Rigenera testo», «Rigenera immagine», «Cambia immagine», «Sposta», «Annulla il post»; finestra Rigenera testo con «Parti da questo testo» chiuso; finestra Cambia immagine con le tre sezioni, la quarta scelta e la spunta «Riscrivi anche il testo» (Rifai il post); Rigenera immagine (3 per post, la stessa immagine sui due canali); dicitura che va e viene; testi di prova, legenda e note | La pagina è una simulazione in JavaScript: provare gli scenari e i pulsanti; il 409 della quarta immagine e del testo senza cicli |
| `AdFlow-operatore-da-approvare.html` | Etichette e filtro (si legge l'etichetta, si filtra sul valore), note | Barra: vedi «Da decidere» (1) |
| `AdFlow-operatore-artigiano-campagne.html` | Etichette degli stati, nota, barra | |
| `AdFlow-calendario.html` | «In programma», «Pubblicato», «Non pubblicato», «Annullato» con spiegazione; legenda; nota; barra con Storico AI | |
| `AdFlow-ingresso.html` | Riga «bottega · referente»; etichette dei post dell'artigiano; note | |
| `AdFlow-campagne.html`, `AdFlow-archivio-foto.html`, `AdFlow-profilo-bottega.html` | Riga «bottega · referente» e una nota | |
| `AdFlow-campagna.html` | Riga «bottega · referente»; passo 10 con «1 settimana», «2 settimane», «1 mese» al posto di «2 settimane / 1 mese / 2 mesi»; nota | Il testo sotto i pulsanti spiega +6, +13, +29 giorni |
| `AdFlow-campagna-stati.html` | Riga «bottega · referente»; etichette dei post dell'artigiano; nota che dice che i valori nel selettore sono per scegliere la vista | |
| `index.html` | Mappa: scheda 14 «Storico AI», voce nella barra, conteggi (14 pagine del programma, 15 statiche MVP, 2 roadmap), descrizioni di Campagna, Campagne da approvare e Vedi campagna, fonti | I numeri (la fascia in alto diceva «7 MVP · 5 roadmap», non più vero) |
| `assets/adflow.css` | Due blocchi nuovi in fondo: `.avanzamento` (barra, compatta sotto i 768 px) e `.riga-bottega`. Nessuna regola esistente cambiata | |

Toccate in chiusura (decisioni 2–4 qui sotto): `AdFlow-operatore-elenco.html`, `AdFlow-operatore-artigiano.html`, `AdFlow-operatore-nuovo-artigiano.html` (voce Storico AI nella barra); `AdFlow-campagna.html`, `AdFlow-campagna-stati.html`, `AdFlow-profilo-bottega.html` (barra nuova); `AdFlow-campagna.html` anche con l'avviso del passo 12.

Non toccate: `AdFlow-login.html`, `AdFlow-operatore-ingresso.html`, `AdFlow-operatore-metriche.html`.

## Controlli fatti

- Ripetuto dopo le decisioni sopra: tutte le 18 pagine in Chromium a 1280 e a 375 px senza errori di pagina, errori in console né richieste fallite; nessuna scorre in orizzontale; 548 link relativi controllati (due viewport) puntano a file che esistono, con le ancore interne.
- Confronto con gli screenshot di `qa/corsia9/` (T3-926 e T3-927): barra dell'operatore con le cinque voci dell'app in Artigiani e Da approvare; avviso del passo 12 visibile. Le differenze con l'app (barra «pagina statica», briciole, riquadro di prova, nessuna linea tra i passi della barra di avanzamento) sono quelle volute di una pagina statica e sono elencate in `qa/corsia9/T3-927/README.md`.
- (Controlli di prima) 290 link relativi (barre, mappa, schede) puntano a file che esistono; le ancore interne esistono.
- Il testo visibile di Da approvare, Campagne dell'artigiano, Calendario, Vedi campagna e Ingresso non contiene valori con il trattino basso. Resta nello Storico AI il nome dei prompt (`post_v3`…), che sono versioni e non stati, come nell'app.
- Vedi campagna, provata con controlli automatici: etichette; barra per ogni stato (in revisione, preparazione non riuscita, L'AI la prepara, in pubblicazione, sospesa, annullata, respinta, scaduta); «Rigenera testo» vuoto o con testo; «Parti da questo testo» propone il testo attuale; Cambia immagine con le sezioni non vuote, spunta accesa e spenta; Rigenera immagine fino a 3, la quarta è rifiutata con il messaggio del brief; da immagine AI a foto la dicitura sparisce; dopo l'approvazione né quarta scelta né spunta né Rigenera.

## Decisioni prese (da confermare dai revisori della PR)

1. **Barra dell'operatore: Storico AI ovunque.** La voce (con l'icona dell'orologio, dopo Calendario e prima di Nuovo artigiano, come nell'app) è ora anche in `AdFlow-operatore-elenco.html`, `-artigiano.html` e `-nuovo-artigiano.html`. Nuovo artigiano ha ancora la sola barra corta di prima (Da approvare, Nuovo artigiano): ci ho aggiunto solo Storico AI, senza riordinarla.
2. **Barra dell'artigiano: quella nuova.** `AdFlow-campagna.html`, `-campagna-stati.html` e `-profilo-bottega.html` hanno ora Ingresso, Campagne, Calendario, Archivio foto, Profilo bottega (la stessa di `AdFlow-campagne.html`). La voce attiva è Campagne per le due pagine della campagna e Profilo bottega per il profilo. «Nuova Campagna» e «Stati & Calendario» non sono più voci di barra: le due pagine restano raggiungibili dai link nel testo e dalla mappa.
3. **Avviso «campagne sovrapposte» (T3-905, J3).** Al passo 12 di `AdFlow-campagna.html` c'è il terzo avviso, con il testo di `Passo12.tsx`: «Nello stesso periodo hai già un'altra campagna: i post delle due campagne usciranno insieme sulla tua pagina.» (con il codice `campagne_sovrapposte`). La pillola in testa dice «3 avvisi · puoi inviare» e la nota sotto cita il nuovo avviso.
4. **Spunta «Riscrivi anche il testo» e «Usa questa foto»: non si cambia, è il frontend.** La pagina statica descrive il comportamento dell'app (spunta accesa di base, nel riquadro «Crea una nuova immagine AI»). **Discrepanza da segnalare:** nell'app lo stato della spunta vale anche per «Usa questa foto»: in revisione una foto scelta parte con `riscrivi_testo: true` (`{"foto_id":102,"riscrivi_testo":true,"nota":null}`), mentre la finestra dice «Il testo non cambia». Se non è voluto, è un task del frontend (`CambiaFoto.tsx`), non delle pagine statiche.

## Non simulato

- Il blocco `immagine_non_creata` (Rigenera immagine sui post la cui immagine non è nata): nella pagina Rigenera immagine si prova sui post con un'immagine AI.
- Il pallino di colore davanti all'etichetta: le pagine usano il colore del badge, senza il punto, per non aggiungere CSS.
- Pagine sempre statiche: i dati dello Storico AI sono di esempio, uguali a quelli dell'app.
