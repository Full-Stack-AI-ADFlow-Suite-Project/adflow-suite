# Percorsi a mano degli sprint 1, 2a e 2b

Archiviato il 14/10/2026 (T3-08). Sono i percorsi con cui si sono chiusi gli sprint 1, 2a e 2b: citano cose che l'MVP ha tolto o congelato (stella, piano debole e Prosegui, logo, cartoline, archivio, nota interna, togli canale, sospensione). Non fanno testo: il percorso di oggi è quello della demo, in `docs/agenti/converge.md` §4.

## 3. Chiusura dello sprint 1 (T1-07)

*Storia.* I percorsi dei §3 e §4 per gli sprint 1, 2a e 2b sono quelli con cui gli sprint si sono chiusi: citano cose che l'MVP ha tolto o congelato (stella, piano debole e Prosegui, logo, cartoline, archivio, nota interna, togli canale, sospensione). Non si rifanno: per lo sprint 3 vale il percorso della demo in fondo al §4.

Su `main` pulito, da database vuoto: comandi del §1 verdi, tutti i CA con S = 1 coperti, frontend sulle API vere, poi a mano:

1. seed → avvio di API, worker, frontend;
2. artigiano: bozza di 7 giorni che inizia tra 4 giorni, su Facebook e Instagram, 4 foto in 2 gruppi con descrizione e una stella, invio;
3. la campagna passa a in_revisione (AI finta);
4. operatore: Vedi campagna, controlla il piano, le uscite con un post per canale, il numero di post per canale, uguale a quelli chiesti (R-05), nessuna foto due volte sullo stesso canale, la foto con la stella presente; un post con soli avvisi non blocca; approva;
5. data di test avanti (`OROLOGIO_GIORNI_AVANTI=12` in `backend/.env`, poi API e worker riavviati): i post si pubblicano (simulato), campagna conclusa;
6. prove negative: inizio tra 1 giorno, durata di 3 giorni, un PDF come foto, invio con 3 foto, canale non collegato, artigiano su pagina operatore (l'admin invece entra), errore di configurazione dell'AI (con `AI_PROVIDER=litellm`, finché il provider vero non c'è): generazione fallita subito, con il motivo accanto a Riprova;
7. piano debole: 4 settimane con 4 foto → `piano_da_rivedere`; Prosegui → in_revisione, con 12 post per canale: 4 con le foto e 8 cartoline (R-28).

Il controllo visivo contro le pagine statiche (`docs/pagine/`) lo fa una persona.

## 4. Chiusura degli sprint successivi (T2a-07, T2b-07, T3-07)

Come al §3: su `main` pulito, da database vuoto, comandi del §1 verdi, tutti i CA dello sprint coperti (`S` dello sprint in spec §6), frontend sulle API vere al posto dei dati di esempio, poi il percorso a mano.

Il percorso a mano di ogni sprint lo scrive qui il suo task di apertura (T2a-01, T2b-01, T3-01), insieme alle firme: così chi lavora sa fin dall'inizio che cosa verrà provato alla fine. Ogni percorso riparte da quello dello sprint prima e aggiunge le cose nuove e le loro prove negative.

Ciò che la chiusura trova rotto torna alla corsia proprietaria come una PR piccola: la chiusura non corregge il codice degli altri.

### Sprint 2a (T2a-07)

Da database vuoto, con AI e social finti:

1. seed → avvio di API, worker, frontend. Un artigiano nuovo (`crea-utente`, senza profilo) entra e arriva alla pagina Profilo, passo 1 (CA-05); al passo 9 con un obbligatorio vuoto non salva e lo indica (CA-07); completato, salva e arriva alla pagina Campagna. Non ha canali collegati (il collegamento è dello sprint 3): il resto si fa con l'artigiano del seed;
2. artigiano del seed: entra → Bentornato; "Va bene così" porta al passo 10 senza salvare il profilo, "Modifica" apre la pagina Profilo (CA-06);
3. passo 7 del profilo: carica il logo, lo sostituisce, lo rivede; archivio: un gruppo con la descrizione e 2 foto. Prove negative: logo che è un PDF, logo oltre 2 MB, logo con il lato corto sotto 300 px → rifiutati con il motivo (CA-78); foto d'archivio con il lato corto sotto 1080 px e gruppo senza descrizione → rifiutati;
4. campagna A, come al §3 passo 2 (7 giorni, inizio tra 4 giorni, Facebook e Instagram, 4 foto in 2 gruppi): esce e rientra → passo 10 con dati, canali, gruppi e foto (CA-08); cambia titolo e fine; una data di gruppo fuori dal nuovo periodo → rifiutata; invio → in_revisione; l'operatore approva; data di test avanti di 12 giorni → pubblicata e conclusa. Nel database ogni foto uscita porta canale e istante (`select id, pubblicata_su from foto`), le cartoline no (CA-76);
5. campagna B, 4 settimane con 4 foto nuove, inviata con l'errore di configurazione dell'AI del §3 passo 6 → generazione fallita; l'artigiano cambia il nome della bottega e il logo; torna l'AI finta, Riprova → in_revisione. Vedi campagna: 12 post per canale, con le foto nuove, le foto d'archivio mai uscite su quel canale (quelle del passo 3 e quelle di A che lì non sono uscite) e, per i post che mancano, cartoline con il logo e il nome di prima dell'invio (CA-16, CA-77); nessuna foto di A sul canale dove è appena uscita; nessuna foto due volte sullo stesso canale. L'operatore approva;
6. data di test avanti di 110 giorni: B si conclude. Campagna C, 4 settimane con 4 foto nuove → tra i riempitivi ci sono post `archivio` con le foto di A, uscite da più di 90 giorni, prima delle cartoline, e Vedi campagna li mostra come tali; una foto uscita su un canale da meno di 90 giorni lì non compare (CA-76);
7. prove negative: quelle del §3 passo 6, e in più modifica di una campagna non in bozza, archivio di un altro artigiano, eliminazione di una foto d'archivio già usata in un post → rifiutate.

### Sprint 2b (T2b-07)

Riparte dal percorso della 2a e ci aggiunge la revisione. Da database vuoto, con AI e social finti, un indirizzo di posta di prova (Mailpit) e un operatore in più oltre a quello del seed:

1. campagna A come al passo 4 della 2a, fino a `in_revisione`. Gli operatori ricevono una notifica `campagna_pronta`, una a testa e una sola anche se il job si riesegue (CA-55). L'artigiano apre la pagina Campagna: nessun piano e nessun post (CA-31);
2. operatore, Vedi campagna: **nota interna** → stato invariato, nessuna email, l'artigiano non la vede, in "Campagne da approvare" compare l'ultima nota (CA-23, CA-69). **Modifica a mano** di un post: nasce la versione con il suo autore, cicli invariati, spunta azzerata; testo uguale a prima o con un blocco → rifiutato (CA-64). **Spunta** "va bene" con chi e quando; su un post `da_rivedere` → rifiutata (CA-65). **Rigenera** da zero e da testo proposto: stesse foto, versione validata; da proposta senza testo → rifiutato; alla quarta → 409, la modifica a mano resta (CA-26…CA-28). Finché l'intervento è in corso l'approvazione è bloccata; dopo 10 minuti (data di test avanti) no (CA-66);
3. **togli il canale** con la nota: i post del canale scartati, l'artigiano vede il canale tolto e la nota; l'ultimo canale → 409 (CA-53). Approva: gli altri post approvati;
4. campagna B in revisione, **respingi** senza motivo o senza nota → rifiutato; con motivo `foto`, nota e 2 foto segnate → `respinta`, post scartati, email all'artigiano con motivo, nota e 2 miniature; l'artigiano le rivede nella pagina Campagna e nel Bentornato (CA-24, CA-25, CA-31);
5. campagna C approvata e attiva: **sospendi** → il tick non pubblica; **riattiva** con un post in arretrato scelto per uscire adesso → esce, gli altri arretrati `annullato`; **annulla** → i post `approvato` diventano `annullato`; ogni azione ha la sua decisione. In attiva o sospesa modifica, rigenera e spunta → rifiutate (CA-29, CA-32);
6. campagna D con un post che la pubblicazione fa fallire (social simulato in errore definitivo): una notifica `post_fallito` agli operatori; **riprogramma** dentro il periodo → `approvato`, decisione `riprogrammato`; fuori dal periodo o nel passato → rifiutato; su un post non fallito → 409 (CA-55, CA-67);
7. scadenze, con la data di test che avanza: in `in_revisione` passa la data di un post → quel post `scaduto`, la campagna si può ancora approvare; passa la data di tanti post da lasciarne meno della metà dei chiesti → campagna `scaduta`, post rimasti `scaduti`, email all'artigiano; campagna senza piano → `scaduta` alle 00:00 del giorno d'inizio (CA-30). Campagna ferma da 30 minuti in `inviata` o `in_generazione` (worker spento durante l'invio) → `generazione_fallita` con l'errore `temporaneo` accanto a Riprova (CA-68). Due tick di fila non ripetono notifiche né cambi (CA-55);
8. prove negative: quelle della 2a e, in più, ogni intervento di revisione fatto da un artigiano → 403, su una campagna di un altro artigiano o di un altro stato → rifiutato, nota o respingi su una campagna ancora in bozza → rifiutato.
