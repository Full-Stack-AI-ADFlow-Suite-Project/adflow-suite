# Spec · cosa fa il prodotto

I numeri stanno solo nelle regole (§5); il resto rimanda agli ID.

## 0. Perimetro MVP
Vale `perimetro-mvp.md` (ADR-114, 13/10/2026): dove questa pagina non torna con quella, vale quella. In breve: l'AI vera analizza le foto, redige il piano e scrive i testi; il numero dei post lo fissa la frequenza; le foto che mancano diventano immagini AI (R-28); un post = una foto; l'operatore approva o respinge, e può sistemare il testo; pubblicazione reale su una sola pagina di prova Meta; calendario per campagna.
- **Fuori MVP**: le regole e i criteri che non valgono nell'MVP stanno nel §7, con i loro ID, pronti per la roadmap (`docs/ROADMAP.md`).
- **Congelate** (codice e test restano, l'interfaccia le nasconde): archivio come rimpiazzo (R-27), caroselli (R-21), spunta (R-30), nota interna (R-32), sospendi, riattiva, annulla (R-33), riprogramma (R-34), togli canale (§2.3).
- **Nuove o cambiate nell'MVP**: R-05, R-13, R-21, R-25, R-28, R-37, R-41…R-45.

## 1. Attori
- **Artigiano**: compila il profilo della bottega, crea e invia campagne (canali e, se vuole, foto a gruppi), vede il piano approvato. Sceglie nel profilo i post a settimana, che sono un impegno (R-26).
- **Operatore** (del consorzio): rivede le campagne e decide; crea i nuovi artigiani (R-37).
- **Admin**: crea operatori da riga di comando; nelle pagine vale come un operatore (R-29). **Sistema**: genera, controlla scadenze, pubblica, invia email.
Un solo consorzio. Canali: Facebook e Instagram, solo foto.

## 2. Flusso
**2.1 Profilo e campagna** (due pagine). Pagina **Profilo** = passi 1–9 (una volta; si salva uscendo dal passo 9 e porta alla pagina Campagna); nel passo 7 né archivio della bottega (congelato) né logo. Pagina **Campagna** = passi 10–12; con profilo già salvato si apre con il **Bentornato**: "Va bene così" → passo 10 senza salvare, "Modifica" → pagina Profilo. Passo 10 = campagna in **bozza**: titolo, inizio, fine, descrizione, **canali** (uno o più tra quelli collegati; la pagina propone quelli del profilo). Passo 11 = **gruppi** di foto caricate (descrizione, data facoltativa `da_usare_il`); facoltativo: senza foto la campagna è fatta di immagini AI (R-28). Passo 12 = riepilogo, **avvisi** che non bloccano (R-25), **dichiarazione** dell'artigiano (R-41) e **invio**: ricontrolla dichiarazione, descrizioni e canali collegati, copia frequenza e obiettivo dal profilo e ne salva la fotografia (`profilo_snapshot`). Dopo l'invio la pagina Campagna mostra, al posto dei passi, una vista per stato (§4). R-08, R-10…R-13, R-22, R-25, R-41.

**2.2 Generazione** (worker), a tappe, ognuna salvata prima della successiva (R-24):
1. **Analisi** dei gruppi di foto caricate, con la descrizione del gruppo. Per ogni foto: `idonea`, `simile_a`, `tipo`, `punteggio`, `motivo`.
2. **Piano**: l'AI propone le uscite (tema e gruppo) e, per ogni canale, i post: foto, data e ora. Il numero dei post non lo decide l'AI (R-05); lo sfasamento tra i canali sì. Un post = una foto (R-21). Limiti: R-05, R-08. Controllo del piano: R-09. Il piano ha sempre i post chiesti: non si ferma mai per mancanza di foto. La data di un gruppo (`da_usare_il`) è un'indicazione per l'AI e per l'operatore: il controllo non la verifica.
3. **Immagini**: un'immagine AI per ogni post senza foto (R-28, R-43); sistemazione delle foto usate dal piano (R-42).
4. **Testo e hashtag** di ogni post secondo la scheda del suo canale (R-21) → validatore a due livelli, blocco e avviso (R-09).

Fine: post `da_approvare`, campagna `in_revisione`. Errori tecnici dell'AI: R-35. Costo di ogni chiamata: R-44. Una notifica avvisa gli operatori quando la campagna è pronta e quando va in `generazione_fallita`.

Scelta delle foto dentro un gruppo, in ordine: idoneità tecnica (filtro); vincoli del profilo (`foto_policy.persone = mai` → fuori le foto con persone riconoscibili); punteggio dell'analisi; pertinenza con la descrizione; varietà (gli scatti quasi uguali contano come uno); formato del canale.

Il piano ha sempre i post chiesti (R-05, R-26): quelli che le foto disponibili non coprono hanno un'immagine AI (R-28).

**2.3 Revisione** (operatore, pagina **Vedi campagna**, che si apre in ogni stato dopo l'invio).
- In `inviata` e `in_generazione` legge ciò che ha inviato l'artigiano e, se c'è, il piano.
- In `generazione_fallita` legge l'errore (R-35): **Riprova** (riparte da dove si era fermata).
- In `in_revisione` sistema i post (§3): un post non si toglie. Poi decide sulla campagna: **approva** (R-14: post approvati, campagna `attiva`) o **respingi** (motivo + nota, email all'artigiano).
- Congelati, nascosti nell'interfaccia: togli il canale (in `generazione_fallita` e `in_revisione`), nota interna (R-32), sospendi, riattiva, annulla (R-33) e riprogramma (R-34). In `attiva` e `sospesa` nessun intervento sui post (R-16).
- Nessuna modifica dell'operatore fa partire l'AI da sola.
- **Calendario della campagna** (R-45): in Vedi campagna e nella vista dell'artigiano.

Non esistono: togliere un post o un'uscita, fermare un singolo post dopo l'approvazione, una soglia minima di post per approvare. R-06, R-14…R-16, R-18, R-30…R-35.

**2.4 Pubblicazione** (tick ogni minuto): pubblica i post approvati alla loro data, con la loro foto sistemata (R-42), sulla pagina dell'artigiano: nell'MVP la pagina di prova Meta, Facebook e Instagram (plan §5); errori temporanei ritentati; un post `fallito` si vede in Vedi campagna, con una notifica agli operatori; quando ogni post è chiuso la campagna è `conclusa` (R-34). R-01.

## 3. Motivi del No e interventi
| Motivo | Azione | Limite | Dopo il limite |
|---|---|---|---|
| Foto scattate male | Le foto non idonee restano già fuori dai post. Se quelle buone sono poche: Respingi con motivo `foto`, nota, foto da rifare segnate | — | — |
| Testo o hashtag scritti male | **Modifica a mano** (R-30) oppure **Rigenera da zero** o **da testo proposto** + nota; stesse foto | R-03 | Resta la modifica a mano |
| Un canale intero non va | Si respinge (togli il canale è congelato) | — | — |
| Altro | Respingi con motivo `altro` e nota | — | — |

**Quando respingere** (linee guida, B3): solo per ciò che l'operatore non può sistemare. ① Foto non pubblicabili e non sostituibili: non sono prodotti della bottega, persone riconoscibili senza consenso, marchi od opere di altri, contenuti vietati da Meta. ② Affermazioni non verificabili chieste dalla campagna: prezzi, sconti, concorsi, certificazioni. ③ Fuori contratto o fuori dal regolamento del consorzio. Mai per testo debole, tono, hashtag o lunghezza: si sistemano con la modifica a mano o con Rigenera.

Ogni intervento crea una nuova versione del post, con il suo autore, che ripassa il validatore; le versioni rifiutate vanno all'AI come "cosa non rifare". Un post `da_rivedere` ha un blocco (R-09): si sblocca con una versione senza blocchi, scritta a mano o dall'AI.

## 4. Cosa vede chi
- **Artigiano**: mai post `da_approvare`, `scartato` o `scaduto`, mai le note interne. In revisione nessun piano e nessun post. Se `respinta`: motivo, nota e foto da rifare (anche nel Bentornato e per email). Se `scaduta`: avviso (anche per email). Tutto dentro la pagina Campagna, una vista per stato: in `attiva` e `conclusa` il piano approvato, cioè la strategia e il calendario dei post approvati, pubblicati, falliti o annullati (R-45, `GET /campagne/{id}/calendario`). Un post `fallito` o `annullato` si legge "non pubblicato". Se un canale è stato tolto la vista lo dice, con la nota dell'operatore; se la campagna è stata approvata dopo l'inizio dice quanti post non sono usciti. Le viste `sospesa` ("Pubblicazioni ferme", con il motivo) e `annullata` ("Campagna chiusa dal consorzio il…") restano per le campagne che ci arrivano, ma nell'MVP nessuna azione visibile le raggiunge. Il testo dei post in programma si legge, senza pulsanti per chiedere modifiche: "Qualcosa non va? Chiama il consorzio" (R-29). Non sono pagine a sé.
- **Artigiano**, più di una campagna: la pagina ne mostra una alla volta, con una riga di scelta in cima; si apre quella che chiede qualcosa: la bozza, poi una respinta o scaduta non ancora sostituita, poi quella in corso, poi quella in lavorazione. "Nuova campagna" sta nella stessa riga, se non c'è già una bozza. Respinta e scaduta restano finché l'artigiano crea una nuova campagna. In fondo l'elenco "Campagne passate". Barra dell'artigiano: Campagna, Profilo bottega, Esci.
- **Operatore**, pagine: campagne da approvare, Vedi campagna, nuovo artigiano (R-37). Si decide solo in Vedi campagna: anche Riprova sta lì. *Campagne da approvare* = le campagne di tutti gli artigiani in `inviata`, `in_generazione`, `generazione_fallita` e `in_revisione`, dalla più urgente (R-38).
- **Operatore**, Vedi campagna: in cima la decisione (approva, respingi; Riprova in `generazione_fallita`) e il piano (strategia, esito del controllo, quanti post hanno un'immagine AI); il costo AI della campagna (R-44); le uscite con i post dei loro canali affiancati e, per ogni post, "Immagine AI" dove c'è, blocchi e avvisi del validatore, storico delle versioni con l'autore, modifica a mano e Rigenera; calendario (R-45); per ogni gruppo le foto usate e non usate con punteggio e motivo, la fotografia del profilo, le decisioni.

## 5. Regole
| ID | Regola |
|---|---|
| R-01 | Si pubblica solo un post approvato. |
| R-02 | Ogni intervento crea una nuova versione; le precedenti restano. |
| R-03 | Per post: max **3** rigenerazioni del testo (da zero + da proposta insieme). Il ciclo si conta quando nasce la versione. La modifica a mano non consuma cicli. |
| R-04 | Le versioni rifiutate vanno all'AI come esempi di "cosa non rifare". |
| R-05 | Per ogni canale: post chiesti = post/settimana × giorni della campagna ÷ **7**, per difetto; foto disponibili = foto caricate `idonea` e senza `simile_a`, sommate sui gruppi. Il piano ha, per canale, esattamente i post chiesti: se le foto disponibili sono di più, il codice passa all'AI solo le migliori per punteggio dell'analisi, fino ai post chiesti, e le altre restano non usate; quelli che le foto non coprono hanno un'immagine AI (R-28). Una foto compare in al massimo **1** post per canale. Le foto d'archivio tra le disponibili (R-27): congelato. |
| R-06 | **Scadenza morbida**: un post `da_approvare` diventa `scaduto` quando passa la sua data; una campagna con un piano diventa `scaduta`, con i post rimasti, quando i post `da_approvare` sono meno della **metà** dei post chiesti sui canali non tolti; una campagna senza piano scade alle **00:00** (Europe/Rome) del giorno di inizio. |
| R-08 | Inizio ≥ oggi + **3** giorni (alla creazione, modifica e invio); durata (fine − inizio + 1) da **7** a **92** giorni; data e ora di ogni post dentro il periodo e mai nel passato (≥ adesso + **15** min). |
| R-09 | Validatore a due livelli. **Blocco**: prezzi o premi che non sono nei dati della bottega, parole vietate, "cose da non dire" del profilo, testo vuoto, limiti della piattaforma (R-21). **Avviso**: limiti editoriali della scheda del canale (R-21). Testo con blocchi o avvisi → riscrive max **3** volte; dopo, con un blocco il post è `da_rivedere`, con i soli avvisi no. Piano non valido → riscrive max **3** volte, poi vale come errore tecnico (R-35). |
| R-10 | Profilo compilato una volta; ai rientri si conferma o si modifica. |
| R-11 | All'invio la campagna salva la fotografia del profilo; generazione e rigenerazioni usano quella. |
| R-12 | Una sola bozza per artigiano; campagne non `annullata/conclusa/respinta/scaduta` non sovrapposte. |
| R-13 | Gruppo di foto caricate: da **1** a **20** foto; descrizione obbligatoria all'invio. Nessun minimo di foto all'invio: senza foto la campagna è tutta con immagini AI (R-28). Foto: JPG/PNG/WEBP, ≤ **10 MB**, lato corto ≥ **1080 px**. `da_usare_il`, se c'è, cade dentro il periodo della campagna. |
| R-14 | Si approva la campagna in blocco: tutti i post `da_approvare`; quelli con la data già passata diventano `scaduto` (R-06); `scartato` e `scaduto` restano come sono. Mai con un post `da_rivedere`, con un intervento in corso (R-31) o senza post da approvare. Gli avvisi del validatore non bloccano. |
| R-15 | Respinta o scaduta = chiusa; non blocca il periodo; l'artigiano ne crea una nuova. |
| R-16 | In campagna attiva o sospesa nessuna modifica ai post e nessun intervento sul singolo post: si sospende, si riattiva o si annulla (R-33). Unica eccezione: riprogrammare un post fallito (R-34). |
| R-18 | Le foto non idonee restano fuori dai post: l'AI non prova a salvarle. Respingi con motivo `foto` e le foto da rifare segnate quando quelle buone sono poche. Respingi richiede sempre motivo (`foto` / `altro`) e nota; vale da `in_revisione`. Quando respingere: §3. Un post non si toglie: i post calano solo con un canale tolto o per scadenza. |
| R-21 | Scheda per canale, numeri di prova. Limiti editoriali (avviso): Facebook **500** caratteri e **3** hashtag; Instagram **600** caratteri e **5** hashtag. Limiti della piattaforma (blocco): Facebook **5000** caratteri e **30** hashtag; Instagram **2200** caratteri e **30** hashtag. Max **10** foto per post su entrambi. **Scelta MVP**: un post = **1** foto (caroselli congelati); immagini quadrate **1:1** o verticali **4:5** su entrambi; link cliccabili nel testo previsti su Facebook, non previsti su Instagram. Sono scelte del progetto, non un elenco completo delle capacità delle piattaforme. |
| R-22 | Canali della campagna: almeno uno, tra `facebook` e `instagram`, solo con account `collegato` (creazione e modifica → 422; invio → 409). La frequenza vale per canale. |
| R-24 | Generazione a tappe: analisi, piano, immagini e versioni dei post si salvano man mano; una nuova esecuzione e Riprova non rifanno ciò che è già salvato. La sistemazione (R-42) tocca solo le foto usate dal piano. |
| R-25 | Avvisi nel dettaglio della campagna, non bloccano l'invio: `foto_poche` se le foto caricate sono meno dei post chiesti per canale, con il numero dei post che avranno un'immagine AI (R-28); `riempitivi_molti` se i post che mancano sono più di **1** ogni **2** foto caricate; `frequenza_alta` se post/settimana × **4** supera il massimo della fascia `foto_policy.quantita_mese` (meno_5 → **4**, da5_a12 → **12**, da12_a20 → **20**, oltre_20 → nessun limite; senza fascia nessun avviso). |
| R-26 | La frequenza è un impegno: su ogni canale escono i post chiesti (R-05), non meno. Il prezzo si misura su post/settimana × canali della campagna. Importo e fatturazione sono fuori dall'MVP: nessun dato e nessuna schermata sul prezzo. |
| R-27 | **Congelato**: nessuna foto d'archivio nel piano, sezione Archivio nascosta. **Archivio della bottega**: le foto `caricata` e `idonea` di un profilo, cioè quelle delle sue campagne chiuse (`conclusa`, `annullata`, `scaduta`, `respinta`), usate o no, e quelle caricate dal profilo in un gruppo senza campagna. Restano fuori le foto segnate in una decisione `respinta`. Per un canale, una foto d'archivio mai pubblicata lì conta tra le foto disponibili di R-05; una già pubblicata lì torna solo dopo **90** giorni, come riempitivo (R-28). Dove è uscita una foto lo scrive la pubblicazione sulla foto stessa, canale per canale (`foto.pubblicata_su`, plan §2). |
| R-28 | **Rimpiazzi**: i post chiesti che le foto disponibili non coprono hanno `riempitivo` = `immagine_ai`: un'immagine creata dall'AI dopo il piano, quadrata **1:1** (valida su entrambi i canali), con i vincoli di R-43, salvata come foto con origine `creata_ai`. Un'uscita con lo stesso tema su due canali usa la stessa immagine. Nessun tetto: i post restano quelli chiesti. Ogni rimpiazzo ha il suo testo, scritto e validato come per gli altri post. Le foto che il piano non usa restano non usate. I riempitivi `cartolina` (tolto) e `archivio` (congelato) restano solo come valori ammessi, per le righe vecchie. |
| R-29 | **Accesso.** Dopo l'accesso: artigiano → pagina Campagna (pagina Profilo, se non ha un profilo); operatore e admin → campagne da approvare. La sessione scade dopo un periodo senza uso: **7** giorni per l'artigiano, **12** ore per operatore e admin; ogni richiesta la rinnova. L'admin passa ogni controllo di ruolo dell'operatore, non quelli dell'artigiano. Il contatto del consorzio (nome, telefono, email) sta nella configurazione e si legge senza sessione. Nessun recupero della password per email: la cambia il consorzio (comando `cambia-password`). |
| R-30 | **Modifica a mano e spunta**, solo in `in_revisione` su un post `da_approvare` senza intervento in corso. Modifica: testo e hashtag; nasce una versione `modifica_operatore` con l'autore, validata; con un blocco → 422 e nessuna versione; testo uguale a prima → 422. Spunta "va bene" (congelata): chi e quando, visibile a tutti gli operatori; si azzera a ogni nuova versione e a ogni cambio di data; non si mette su un post `da_rivedere`. |
| R-31 | **Intervento in corso**: alla richiesta di un intervento AI il post salva il tipo e l'ora; si spegne quando nasce la versione o alla terza esecuzione fallita (post invariato, ciclo non contato). Un job che trova la campagna fuori da `in_revisione` o il post non `da_approvare` non fa nulla. Un intervento partito da più di **10** minuti vale come fallito: non blocca più e si può rilanciare. Con un intervento in corso sul post nessun altro intervento → 409. |
| R-32 | **Nota interna** (congelata): in ogni stato dopo l'invio, quante se ne vuole; decisione con esito `nota`; la leggono solo gli operatori; nessuno stato, nessuna email. Negli elenchi dell'operatore compare l'ultima. |
| R-33 | **Sospendi, riattiva, annulla** (congelati), ognuna con la sua decisione. Riattiva riceve i post in arretrato (approvati con la data passata) da pubblicare adesso: gli altri diventano `annullato`. Annulla porta ad `annullato` tutti i post `approvato`. Un post `annullato` è chiuso e non si pubblica. |
| R-34 | **Riprogramma** (congelato): un post `fallito`, in campagna attiva o sospesa, torna `approvato` con una nuova data e ora dentro il periodo e ≥ adesso + **15** min; il contenuto non cambia. **Conclusione**: la campagna attiva è `conclusa` quando ogni post è `pubblicato`, `fallito`, `annullato`, `scartato` o `scaduto`; se c'è un post `fallito`, solo dopo la fine del periodo. |
| R-35 | **Errori tecnici dell'AI.** Ogni errore ha un tipo: `temporaneo` (tempo scaduto, rete, troppe richieste, servizio sovraccarico), `risposta` (vuota, troncata, non nel formato chiesto), `configurazione` (chiave, credito, modello), `richiesta` (foto troppo pesante, testo troppo lungo, file mancante), `rifiuto` (filtro del provider). `temporaneo` e `risposta` → nuova esecuzione, **3** in tutto, poi `generazione_fallita`. `configurazione` → `generazione_fallita` subito. `richiesta` o `rifiuto` su una sola foto → la foto diventa non idonea, con il motivo, e si continua; sul testo di un post → versione con testo vuoto e un blocco (`da_rivedere`), e si continua. Di ogni errore che ferma un'esecuzione si salvano tipo, messaggio, tappa e canale; l'operatore legge l'ultimo accanto a Riprova. Una campagna ferma da **30** minuti in `inviata` o `in_generazione` passa a `generazione_fallita` (tipo `temporaneo`). |
| R-37 | **Nuovo artigiano**: l'operatore crea l'utente artigiano con email di accesso e nome del referente; la password la genera il sistema e la mostra una sola volta; email già usata → 409. Il profilo lo compila l'artigiano al primo accesso. Gli account social del nuovo artigiano nascono come quelli del seed. |
| R-38 | **Campagne da approvare**: ordinate per "entro quando", cioè la data del primo post `da_approvare` oppure le 00:00 dell'inizio se il piano non c'è. |
| R-41 | **Dichiarazione dell'artigiano**: all'invio una spunta obbligatoria, "Le foto mostrano prodotti della mia bottega; le persone riconoscibili hanno dato il consenso"; senza → 422. Si salva nella fotografia del profilo con la data. |
| R-42 | **Sistemazione delle foto**, una sola funzione locale, usata da anteprima e pubblicazione: rotazione secondo i metadati, posizione GPS tolta, ritaglio al centro nelle proporzioni della scheda del canale (R-21) solo se la foto ne è fuori, lato corto **1080 px**, autocontrasto leggero, JPEG. L'originale resta (costituzione §1.3). |
| R-43 | **Immagini AI**: mostrano ambienti, materiali, attrezzi, lavorazioni, atmosfere e stagioni; mai un prodotto finito come se fosse della bottega, persone riconoscibili, testi, loghi o marchi. Il prompt parte da fotografia del profilo, campagna, tema e formato. Il testo del post porta "Immagine creata con AI". |
| R-44 | **Costo dell'AI**: ogni chiamata (analisi, piano, testo, immagine) registra campagna, post se c'è, tipo, modello e costo stimato in dollari; Vedi campagna mostra il totale della campagna. Nessun tetto di spesa nel codice. |
| R-45 | **Calendario della campagna**: elenco per giorno dei post approvati, pubblicati, falliti o annullati, con data, ora, canale, stato, testo e foto; lo leggono il proprietario e l'operatore, dopo l'approvazione. |

## 6. Criteri di accettazione
Dato / Quando / Allora in forma breve. Il test porta l'ID nel nome (`test_ca09_...`). I CA delle funzioni congelate restano verdi; quelli fuori MVP sono nel §7.

| ID | Dato → Quando → Allora |
|---|---|
| CA-01 | utente attivo → login corretto → entra con il suo ruolo |
| CA-02 | utente → password errata → rifiutato, senza dire quale dato è sbagliato |
| CA-03 | artigiano → funzione operatore → 403 |
| CA-04 | artigiano → campagna o foto di un altro → 404 |
| CA-05 | artigiano senza profilo → entra → pagina Profilo, passo 1 |
| CA-06 | artigiano con profilo → rientra → pagina Campagna con Bentornato; "Va bene così" non salva il profilo, "Modifica" apre la pagina Profilo |
| CA-07 | passo 9 → manca un obbligatorio → non salva e lo indica |
| CA-08 | bozza aperta → rientra → pagina Campagna dal passo 10 con dati, canali, gruppi e foto |
| CA-09 | → crea o invia con inizio < oggi + 3 giorni → 422 (anche bozza ferma) |
| CA-10 | → durata > 92 giorni, < 7 giorni o fine ≤ inizio → 422 |
| CA-11 | bozza esistente → nuova bozza → 409 |
| CA-12 | campagna attiva → periodo sovrapposto → 409; se la precedente è respinta o scaduta → ok |
| CA-13 | bozza → foto non immagine, > 10 MB o lato < 1080 px, oppure ventunesima foto di un gruppo → 422 con motivo |
| CA-14 | bozza con un gruppo senza descrizione, o senza la dichiarazione (R-41) → invio → 422; senza foto → invio ammesso |
| CA-15 | bozza completa → invio → inviata, frequenza e obiettivo copiati, snapshot salvato |
| CA-16 | campagna inviata → profilo modificato → generazione e Riprova usano lo snapshot |
| CA-17 | 14 giorni, 3 post/sett., 2 canali, un gruppo di 5 foto idonee e diverse → generazione → 6 uscite, 6 post per canale (5 con una foto, 1 con un'immagine AI), nessuna foto due volte sullo stesso canale |
| CA-18 | testo con un blocco → 3 riscritture ancora con un blocco → post `da_rivedere`; con i soli avvisi → non `da_rivedere`, avvisi salvati nella versione |
| CA-19 | errore `temporaneo` dell'AI a ogni esecuzione → 3 esecuzioni → `generazione_fallita`, con tipo, messaggio, tappa e canale salvati; Riprova → inviata e riparte |
| CA-20 | generazione riuscita → piano salvato, post `da_approvare`, campagna `in_revisione` |
| CA-21 | in revisione senza post da rivedere → approva → post `da_approvare` approvati, campagna attiva, riga approvazione per post; i post con la data già passata diventano `scaduto`; avvisi del validatore → approva ammesso |
| CA-22 | post `da_rivedere` o intervento in corso → approva → 409 |
| CA-23 | campagna dopo l'invio → nota interna → stato invariato, decisione `nota`, nessuna email; l'artigiano non la vede (congelato) |
| CA-24 | in revisione → respingi senza motivo o nota → 422 |
| CA-25 | in revisione → respingi `foto` con 2 foto segnate → respinta, post scartati, email con motivo, nota, 2 miniature |
| CA-26 | post → rigenera da zero → nuova versione, stesse foto, validata |
| CA-27 | post → rigenera da proposta senza testo → 422; con testo → nuova versione, stesse foto |
| CA-28 | post con 3 rigenerazioni → quarta → 409; la modifica a mano resta ammessa |
| CA-29 | campagna attiva o sospesa → modifica a mano, rigenerazione o spunta su un post → 409 |
| CA-30 | in revisione → passa la data di un post → quel post `scaduto`, campagna ancora approvabile; restano `da_approvare` meno della metà dei post chiesti → campagna `scaduta`, post rimasti scaduti, email; campagna senza piano → `scaduta` alle 00:00 del giorno di inizio |
| CA-31 | in revisione → artigiano apre → nessun piano e nessun post; respinta → vede motivo, nota, foto |
| CA-32 | attiva → sospendi → non pubblica; riattiva con post in arretrato → quelli scelti tornano pubblicabili, gli altri `annullato`; annulla → post `approvato` annullati, non pubblica più; ogni azione ha la sua decisione (congelato) |
| CA-36 | post approvato con data raggiunta → due tick → pubblicato una volta sola |
| CA-37 | post da approvare con data raggiunta → tick → non pubblicato |
| CA-38 | errore temporaneo del social ×3 → post `fallito`, visibile all'operatore in Vedi campagna |
| CA-39 | attiva → ogni post `pubblicato`, `scartato` o `scaduto` → conclusa; con un post `fallito` → resta attiva fino alla fine del periodo, poi conclusa |
| CA-48 | canale senza account collegato → crea o modifica la bozza con quel canale → 422; account scollegato dopo → invio → 409 |
| CA-50 | generazione fallita dopo l'analisi → Riprova → le foto già analizzate non si rianalizzano |
| CA-53 | in revisione con 2 canali → togli un canale con nota → i suoi post scartati; approva → gli altri approvati; togliere l'ultimo canale → 409; l'artigiano vede il canale tolto e la nota (congelato) |
| CA-54 | bozza con foto caricate sotto i post chiesti per canale → dettaglio → avviso `foto_poche` con il numero dei post che avranno un'immagine AI, e `riempitivi_molti` se i post che mancano sono più di 1 ogni 2 foto caricate; profilo `meno_5` con frequenza `f3_4` → avviso `frequenza_alta`; l'invio resta ammesso |
| CA-55 | campagna pronta, in `generazione_fallita`, o post `fallito` → una notifica agli operatori per ogni evento |
| CA-56 | campagna attiva → il proprietario legge il calendario → strategia e soli post approvati, pubblicati, falliti o annullati, e il numero dei post scaduti; prima dell'approvazione → 409; campagna di un altro → 404 |
| CA-57 | su un canale foto disponibili meno dei post chiesti → generazione → i post del canale sono quelli chiesti; quelli che mancano hanno `immagine_ai`, con la sua immagine quadrata 1:1 e il suo testo con "Immagine creata con AI"; approvato e arrivato alla data → pubblicato con la sua immagine |
| CA-58 | errore `configurazione` dell'AI → prima esecuzione → `generazione_fallita`, nessun'altra esecuzione |
| CA-59 | errore `richiesta` o `rifiuto` su una sola foto → la foto resta fuori con il motivo, la generazione arriva a `in_revisione` |
| CA-60 | operatore → Vedi campagna in `generazione_fallita` → legge tipo, messaggio, tappa e canale dell'ultimo errore |
| CA-61 | admin → funzione dell'operatore → ammesso; funzione dell'artigiano → 403 |
| CA-62 | sessione non usata oltre la durata del suo ruolo → 401; usata prima → resta valida e la scadenza si sposta |
| CA-63 | senza sessione → `GET /consorzio` → nome, telefono, email |
| CA-64 | post in revisione → modifica a mano → versione `modifica_operatore` con autore, validata, cicli invariati, spunta azzerata; con un blocco o senza cambiamenti → 422, nessuna versione |
| CA-65 | post → spunta → chi e quando salvati; nuova versione → spunta azzerata; post `da_rivedere` → spunta → 409 (congelato) |
| CA-66 | rigenerazione fallita 3 volte → post invariato, ciclo non contato, intervento spento; intervento partito da più di 10 minuti → approva ammesso |
| CA-67 | post `fallito` in campagna attiva → riprogramma dentro il periodo → `approvato` con la nuova data, decisione `riprogrammato`; fuori dal periodo o nel passato → 422; post non fallito → 409 (congelato) |
| CA-68 | campagna ferma da 30 minuti in `inviata` o `in_generazione` → tick → `generazione_fallita` con errore `temporaneo` |
| CA-69 | operatore → campagne da approvare → per ogni campagna conteggi dei post, entro quando e ultima nota interna, dalla più urgente |
| CA-70 | artigiano con più campagne → pagina Campagna → apre quella che chiede qualcosa (§4), con la riga di scelta |
| CA-79 | operatore → nuovo artigiano con email e nome → 201 con la password provvisoria, una sola volta; l'artigiano entra e arriva al passo 1 del profilo; email già usata → 409; artigiano → 403 |
| CA-80 | 10 foto idonee e diverse, 6 post chiesti su un canale → generazione → 6 post con le 6 foto di punteggio più alto; le altre 4 non usate |
| CA-81 | foto ruotata nei metadati, con GPS, PNG 3000 × 2000 → sistemazione per Instagram → JPEG dritta, senza GPS, 4:5 o 1:1 con lato corto 1080 px; l'originale resta |
| CA-82 | generazione con analisi, piano, testi e 2 immagini AI → ogni chiamata ha il suo costo registrato; Vedi campagna mostra il totale |
| CA-83 | adattatore Meta con risposte HTTP simulate → Facebook ok → id del post salvato; Instagram contenitore e pubblicazione → id salvato; errore definitivo → `fallito`; tempo scaduto o errore 5xx → temporaneo, ritentato |

## 7. Fuori MVP
Regole e criteri che non valgono nell'MVP (ADR-114): non si costruiscono né si estendono. Restano qui, con i loro ID, per la roadmap (`docs/ROADMAP.md`). Dove il codice c'è ancora (gruppi `create_ai`, caroselli, archivio) resta, con i suoi test, nascosto nell'interfaccia; il resto lo ha tolto T3-01.

**Regole**

| ID | Regola |
|---|---|
| R-03 (ritocchi) | Max **3** ritocchi della foto per post; scelta e cambio della foto e spostamento non consumano cicli. |
| R-06 (promemoria) | Promemoria all'operatore **48 h** prima dell'inizio. |
| R-07 | Permesso scaduto o account non più collegato alla pubblicazione → campagna `sospesa` + avvisi. Nell'MVP l'errore rende il post `fallito`. |
| R-13 (create_ai) | Gruppi `create_ai` con `n_immagini` da **1** a **20**. Il codice resta; il pulsante per aggiungerli è nascosto. |
| R-17 | Il ritocco vale solo per il post su cui si lavora; l'originale resta. Nell'MVP le foto si sistemano in locale (R-42). |
| R-19 | Immagini AI chieste dall'artigiano con i gruppi `create_ai`, sempre in aggiunta alle foto caricate; gruppo, descrizione e `n_immagini` si salvano fin da subito e la generazione li ignora. Nell'interfaccia il pulsante resta nascosto. Le immagini AI dell'MVP sono solo rimpiazzi (R-28). |
| R-20 | Piano debole: su un canale le foto disponibili sono meno della **metà** dei post chiesti, oppure un gruppo `caricate` non ha nessuna foto idonea; la campagna si ferma in `piano_da_rivedere` e Prosegui la fa ripartire. Nell'MVP il piano non è mai debole; lo stato resta per le righe vecchie. |
| R-23 | Foto con la stella (`da_usare`): se idonea, è sempre in un post del piano; non è mai un doppione (`simile_a` passa all'altra); se sono più dei post chiesti, il piano ne usa almeno quanti sono i post chiesti. Nell'MVP le foto le sceglie il punteggio dell'analisi; la colonna resta. |
| R-29 (ingresso) | L'operatore arriva su una pagina d'ingresso, con le campagne da sistemare. |
| R-36 | **Interventi sul piano**, solo in `in_revisione`. Cambia foto: con una foto `idonea` dello stesso gruppo che non è in un altro post dello stesso canale; nasce una versione `cambio_foto` con lo stesso testo; non vale per i riempitivi. Sposta: nuova data e ora dentro il periodo e ≥ adesso + **15** min; il testo resta. Nessuna delle due fa partire l'AI. (Il ritaglio è nell'MVP, in R-42.) |
| R-37 (anagrafica) | Anagrafica dell'artigiano (codice ART, codice consorzio, telefono, `iscritto_il`, iscrizione sospesa), cambio password obbligato al primo accesso, "Nuova password provvisoria". |
| R-38 (pagine dell'operatore) | Pagina artigiano: le ultime **3** campagne chiuse, per data di chiusura; le altre nella pagina delle chiuse. Elenco artigiani: codice, bottega, referente, città, iscrizione, stato dell'account per canale, campagne da approvare e in corso, prossima scadenza; ricerca e filtri nel browser. Sezioni della pagina artigiano: *Da approvare* = inviata, in_generazione, piano_da_rivedere, generazione_fallita, in_revisione · *In corso* = attiva, sospesa · *Storico* = scaduta, conclusa, annullata, respinta. Un solo pulsante: Vedi campagna. |
| R-39 | **Metriche**. Filtri: artigiano, campagna, periodo (`dal`, `al`, sulla data di pubblicazione; **30** giorni se vuoto). Per ogni post l'ultima rilevazione; i totali sono la somma delle ultime rilevazioni, anche divisi per canale. Post `fallito` e `annullato` fuori dalla tabella; a parte il conteggio dei falliti. Nessun grafico. Report settimanale agli operatori; all'artigiano un riepilogo quando la campagna è `conclusa`. |
| R-40 | **Logo della bottega**: JPG, PNG o WEBP, ≤ **2 MB**, lato corto ≥ **300 px**; sta nel profilo e nella fotografia del profilo; va sulle cartoline. Nell'MVP il logo è una foto come le altre; la colonna resta. |

**Criteri**

| ID | Dato → Quando → Allora |
|---|---|
| CA-33 | generazione → ogni foto ha versione ritoccata e l'originale resta |
| CA-34 | foto usata su 2 canali → ritocca per un post → cambia solo quello |
| CA-35 | 3 ritocchi → quarto → 409; scegli originale → ok senza consumare cicli |
| CA-40 | permesso scaduto o account scollegato dopo l'invio → prima pubblicazione → sospesa + avvisi |
| CA-41 | campagne in stati diversi → pagina artigiano → ognuna nella sezione giusta; delle chiuse solo le ultime 3, le altre nella pagina delle campagne chiuse |
| CA-42 | in revisione, inizio tra < 48 h → tick orario → un promemoria, una volta |
| CA-43 | nome diverso tra anagrafica e profilo → pagina artigiano → differenza segnalata |
| CA-44 | post pubblicato → lettura giornaliera → metriche salvate e visibili |
| CA-45 | sistema completo → invio e approvazione → post pubblicati (E2E nel browser) |
| CA-46 | bozza → gruppo `create_ai` con descrizione e `n_immagini` → salvato e restituito nel dettaglio (il codice resta: il test resta) |
| CA-47 | → gruppo `create_ai` con `n_immagini` fuori da 1–20, foto caricata in un gruppo `create_ai`, o `da_usare_il` fuori dal periodo → 422 (il codice resta: il test resta) |
| CA-49 | su un canale foto disponibili sotto la metà dei post chiesti → generazione → `piano_da_rivedere`, nessun testo generato; Prosegui → riparte e arriva a `in_revisione` |
| CA-51 | foto con la stella idonea → è in un post del piano; non idonea → resta fuori, con il motivo; quasi uguale a un'altra senza stella → il doppione è l'altra |
| CA-52 | piano con un carosello → post con più foto in ordine; pubblicato una volta con tutte le foto (caroselli congelati: il test resta) |
| CA-71 | post in revisione → cambia foto con una idonea del gruppo libera su quel canale → versione `cambio_foto`, stesso testo; foto di un altro gruppo, non idonea o già sul canale → 422 |
| CA-72 | post in revisione → sposta dentro il periodo → nuova data, spunta azzerata; fuori dal periodo o nel passato → 422 |
| CA-73 | nuovo artigiano → password provvisoria mostrata una volta → al primo accesso deve cambiarla prima di ogni altra pagina |
| CA-74 | iscrizione sospesa → invio → 409; le campagne approvate continuano a uscire |
| CA-75 | metriche senza date → ultimi 30 giorni; per ogni post l'ultima rilevazione; falliti e annullati fuori dalla tabella |
| CA-76 | foto d'archivio idonea mai uscita su un canale → generazione → conta tra le foto disponibili di quel canale; uscita lì da meno di 90 giorni → resta fuori; da più di 90 → torna solo come riempitivo `archivio`; dopo la pubblicazione la foto porta canale e data (archivio congelato: il test resta) |
| CA-77 | profilo con il logo → campagna inviata → le cartoline portano il logo; logo sostituito dopo l'invio → la campagna inviata usa ancora quello di prima |
| CA-78 | → logo che non è un'immagine o > 2 MB → 422 con motivo |
