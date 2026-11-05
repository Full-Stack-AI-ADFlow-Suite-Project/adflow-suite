# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Artigiano** (utente primario): titolare di una bottega artigiana del consorzio. Non tecnico: entra dal telefono e dal PC, e il telefono resta lo scenario critico (375 px). Compila il profilo della bottega una volta, crea le campagne, risponde alle richieste del consorzio, legge il piano approvato.
- **Operatore** del consorzio: revisiona e sistema le campagne da scrivania, chiede all'artigiano ciò che serve, approva o respinge, crea i nuovi artigiani.
- **Admin**: vale come un operatore nelle pagine. **Sistema**: genera, pubblica, controlla le scadenze.
- Un solo consorzio. Canali: Facebook e Instagram, solo foto.

## Product Purpose

Trasforma le foto che un artigiano carica in una campagna social completa: l'AI analizza le foto, propone il piano (tema, post per canale con data e ora), genera un'immagine AI per ogni post che le foto non coprono e scrive testi e hashtag. L'operatore revisiona, corregge e decide; il sistema pubblica i post approvati. Successo = il consorzio pubblica campagne corrette e puntuali senza che l'artigiano debba saper usare strumenti di marketing.

## Positioning

Un "ufficio stampa del consorzio": l'artigiano dà solo le foto e i dati della bottega, la macchina e l'operatore fanno il resto, fino alla pubblicazione reale sui canali. Nessuno strumento di marketing generico offre la revisione umana dell'operatore del consorzio come passaggio obbligato prima di ogni pubblicazione.

## Operating Context

- L'artigiano entra dal telefono in bottega e dal PC a casa o in ufficio: i percorsi devono essere comprensibili a 375 px e con il menu chiuso (il nome della bottega resta visibile), e restare comodi anche sullo schermo largo.
- L'operatore lavora da scrivania su elenchi e dettagli (Vedi campagna): densità e leggibilità contano più dell'effetto.
- La demo è dal vivo, sul percorso dell'artigiano (pitch del 6 novembre 2026). I dati di esempio in `frontend/src/api/esempi/` alimentano le pagine finché l'endpoint non è su `main`.
- Le pagine statiche di `docs/archivio/pagine/` sono il riferimento concordato dell'interfaccia dell'MVP.
- Richiesta all'artigiano senza email: l'operatore avvisa a voce o con un messaggio.

## Capabilities and Constraints

- Interfaccia e dominio in italiano; testi visibili scritti nel frontend con il tono scelto; restano i testi fissi di `brief-interfaccia.md` §1.4.
- Comportamento invariato (perimetro I6): rotte, chiamate, campi, validazioni, stati, ordine di sezioni e passi non si toccano con interventi visivi.
- Un post = una foto; l'immagine AI è sempre quadrata 1:1 e porta l'indicazione "Immagine creata con AI". Le immagini AI non mostrano mai prodotti finiti spacciati per la bottega, persone riconoscibili, testi o marchi.
- Le foto appaiono nelle proporzioni dei canali (da 4:5 a 1,91:1) senza deformazioni: ritaglio sul soggetto o bordi con la foto sfocata.
- Niente si cancella: versioni, decisioni e campagne chiuse restano visibili.
- Tema scuro in roadmap: il tema è uno solo, chiaro.
- Funzioni congelate restano nascoste nell'interfaccia (es. caroselli, nota interna, spunta, togli canale).

## Brand Commitments

- Nome: **AdFlow Suite** (wordmark dedicato, `frontend/src/components/Wordmark.tsx`).
- Voce: italiano, tono da "consorzio che sa il fatto suo", diretto e rassicurante verso l'artigiano.
- Riferimento visivo concordato dell'MVP: `docs/archivio/pagine/` e `adflow.css`.

## Evidence on Hand

- `docs/archivio/pagine/`: pagine statiche di riferimento dell'interfaccia (mappa in `index.html`).
- `frontend/src/api/esempi/`: dati di esempio usati dalle pagine.
- Nessun materiale fotografico di marca oltre al wordmark: non inventare loghi, testimonianze o numeri.

## Product Principles

1. **L'artigiano non deve sapere come funziona**: etichette e spiegazioni invece degli stati del database; un'azione chiara per pagina; il telefono è lo scenario di default.
2. **La decisione resta umana**: l'AI propone, l'operatore decide; l'interfaccia mette in evidenza ciò che richiede un giudizio (blocchi, avvisi, richieste aperte).
3. **L'operatore scansiona**: elenchi ordinati per urgenza, stati leggibili, azioni ammesse solo quando il server le dice.
4. **Nessuna promessa falsa**: l'immagine AI è sempre dichiarata; un post non pubblicato si legge "non pubblicato".
5. **Precisione prima dell'espressione**: i cambi sono visivi e di testo, mai di comportamento.

## Accessibility & Inclusion

Requisito formale: **WCAG 2.1 livello AA** (contrasto 4.5:1 testo normale, 3:1 testo grande e componenti/indicato di focus). Verifica con `@axe-core/playwright` già in `devDependencies`. Utente primario su touch: target di tocco adeguati.
