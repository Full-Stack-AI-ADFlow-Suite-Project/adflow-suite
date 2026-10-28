# T3-926 · Pagine statiche della corsia 9

**Casella ☐: la pagina di una persona non spunta da sola.** Il «fatto quando» chiede che ogni pagina toccata sia riletta da un collega; finché Giovanni non conferma la rilettura la casella resta vuota.

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

Non toccate: `AdFlow-login.html`, `AdFlow-operatore-elenco.html`, `AdFlow-operatore-artigiano.html`, `AdFlow-operatore-nuovo-artigiano.html`, `AdFlow-operatore-ingresso.html`, `AdFlow-operatore-metriche.html`.

## Controlli fatti

- Tutte le 18 pagine si aprono in Chromium a 1280 e a 375 px senza errori in console né richieste fallite; nessuna scorre in orizzontale.
- 290 link relativi (barre, mappa, schede) puntano a file che esistono; le ancore interne esistono.
- Il testo visibile di Da approvare, Campagne dell'artigiano, Calendario, Vedi campagna e Ingresso non contiene valori con il trattino basso. Resta nello Storico AI il nome dei prompt (`post_v3`…), che sono versioni e non stati, come nell'app.
- Vedi campagna, provata con controlli automatici: etichette; barra per ogni stato (in revisione, preparazione non riuscita, L'AI la prepara, in pubblicazione, sospesa, annullata, respinta, scaduta); «Rigenera testo» vuoto o con testo; «Parti da questo testo» propone il testo attuale; Cambia immagine con le sezioni non vuote, spunta accesa e spenta; Rigenera immagine fino a 3, la quarta è rifiutata con il messaggio del brief; da immagine AI a foto la dicitura sparisce; dopo l'approvazione né quarta scelta né spunta né Rigenera.

## Da decidere (Giovanni)

1. **Spunta «Riscrivi anche il testo» e «Usa questa foto».** Nell'app (`CambiaFoto.tsx`) la spunta è accesa di base ed è nel riquadro «Crea una nuova immagine AI», in fondo alla finestra; ma lo stato vale anche per «Usa questa foto»: in revisione una foto scelta parte con `riscrivi_testo: true` (verificato dalla rete del browser: `{"foto_id":102,"riscrivi_testo":true,"nota":null}`), mentre il testo della finestra dice «Il testo non cambia». La pagina statica fa come l'app. Se non è voluto, va corretto nel frontend (non qui).
2. **Barra dell'operatore.** Vedi campagna e Da approvare avevano solo «Da approvare» e «Nuovo artigiano»: ho messo la barra dell'app (Da approvare, Artigiani, Calendario, Storico AI, Nuovo artigiano), perché «Storico AI dopo Calendario» non si può dire senza. Le pagine `AdFlow-operatore-elenco.html`, `AdFlow-operatore-artigiano.html` e `AdFlow-operatore-nuovo-artigiano.html` non sono nell'elenco di T3-926 e non hanno la voce Storico AI: una riga ciascuna, se la vuoi.
3. **Pagine con la barra vecchia, già prima della corsia 9.** `AdFlow-campagna.html`, `AdFlow-campagna-stati.html` e `AdFlow-profilo-bottega.html` hanno ancora «Nuova Campagna · Stati & Calendario · Profilo Bottega» al posto di «Ingresso · Campagne · Calendario · Archivio foto · Profilo bottega». Non l'ho cambiata.
4. **Avviso «campagne sovrapposte» (T3-905, J3).** Il testo del passo 12 («Nello stesso periodo hai già un'altra campagna…», brief §1.6) non è nell'elenco di T3-926 e non l'ho aggiunto.

## Non simulato

- Il blocco `immagine_non_creata` (Rigenera immagine sui post la cui immagine non è nata): nella pagina Rigenera immagine si prova sui post con un'immagine AI.
- Il pallino di colore davanti all'etichetta: le pagine usano il colore del badge, senza il punto, per non aggiungere CSS.
- Pagine sempre statiche: i dati dello Storico AI sono di esempio, uguali a quelli dell'app.
