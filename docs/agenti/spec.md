# Spec · cosa fa il prodotto

I numeri stanno solo nelle regole (§5); il resto rimanda agli ID.

## 1. Attori
- **Artigiano**: compila il profilo della bottega, crea e invia campagne (canali, foto a gruppi e, se vuole, gruppi di immagini da creare con l'AI), vede il piano approvato. Sceglie nel profilo i post a settimana, che sono un impegno (R-26).
- **Operatore** (del consorzio): rivede le campagne e decide; gestisce anagrafica e account social.
- **Admin**: crea operatori, configura; nelle pagine vale come un operatore (R-29). **Sistema**: genera, controlla scadenze, pubblica, invia email.
Un solo consorzio. Canali dell'MVP: Facebook e Instagram, solo foto.

## 2. Flusso
**2.1 Profilo e campagna** (due pagine). Pagina **Profilo** = passi 1–9 (una volta; si salva uscendo dal passo 9 e porta alla pagina Campagna). Pagina **Campagna** = passi 10–12; con profilo già salvato si apre con il **Bentornato**: "Va bene così" → passo 10 senza salvare, "Modifica" → pagina Profilo. Passo 10 = campagna in **bozza**: titolo, inizio, fine, descrizione, **canali** (uno o più tra quelli collegati; la pagina propone quelli del profilo). Passo 11 = **gruppi**: di foto caricate (descrizione, data facoltativa `da_usare_il`, stella `da_usare` sulle foto) oppure di immagini da creare (`create_ai`: descrizione e `n_immagini`). Passo 12 = riepilogo, **avvisi** che non bloccano (R-25) e **invio**: ricontrolla minimi e canali collegati, copia frequenza e obiettivo dal profilo e ne salva la fotografia (`profilo_snapshot`). Dopo l'invio la pagina Campagna mostra, al posto dei passi, una vista per stato (§4). R-08, R-10…R-13, R-19, R-22, R-25. Archivio della bottega e logo, nel passo 7 del profilo, arrivano con la 2a (R-27).

**2.2 Generazione** (worker), a tappe, ognuna salvata prima della successiva (R-24):
1. **Analisi** dei gruppi di foto caricate, con la descrizione del gruppo. Per ogni foto: `idonea`, `simile_a`, `tipo`, `punteggio`, `motivo`.
2. **Piano**: l'AI propone le uscite (tema e gruppo) e, per ogni canale, i post: formato, foto, data e ora. Il numero dei post non lo decide l'AI (R-05); lo sfasamento tra i canali e il carosello sì. Limiti: R-05, R-08, R-23. Controllo del piano: R-09. Piano debole → `piano_da_rivedere` (R-20). La data di un gruppo (`da_usare_il`) è un'indicazione per l'AI e per l'operatore: il controllo non la verifica.
3. **Immagini**: le cartoline dei post riempitivo (R-28); ritocco delle foto usate dal piano (dallo sprint 3); creazione delle immagini AI (non ancora pianificata, R-19).
4. **Testo e hashtag** di ogni post secondo la scheda del suo canale (R-21) → validatore a due livelli, blocco e avviso (R-09).

Fine: post `da_approvare`, campagna `in_revisione`. Errori tecnici dell'AI: R-35. Dalla 2b una notifica avvisa gli operatori quando la campagna è pronta, quando si ferma in `piano_da_rivedere` e quando va in `generazione_fallita`.

Scelta delle foto dentro un gruppo, in ordine: idoneità tecnica (filtro); vincoli del profilo (`foto_policy.persone = mai` → fuori le foto con persone riconoscibili); stella; pertinenza con la descrizione; varietà (gli scatti quasi uguali contano come uno); formato del canale.

Il piano ha sempre i post chiesti (R-05, R-26): quelli che le foto disponibili non coprono sono riempitivi (R-28), e su un canale con riempitivi il piano non fa caroselli.

**2.3 Revisione** (operatore, pagina **Vedi campagna**, che si apre in ogni stato dopo l'invio).
- In `inviata` e `in_generazione` legge ciò che ha inviato l'artigiano e, se c'è, il piano.
- In `generazione_fallita` legge l'errore (R-35): **Riprova** (riparte da dove si era fermata) oppure, dalla 2b, **Togli il canale** che fallisce.
- In `piano_da_rivedere` vede il piano e le foto: **Prosegui** (la generazione riparte dai testi) oppure, dalla 2b, **Togli il canale** o **Respingi**. Nello sprint 1 c'è solo Prosegui: una campagna senza foto disponibili resta ferma.
- In `in_revisione` sistema i post (§3): un post non si toglie. Poi decide sulla campagna: **approva** (R-14: post approvati, campagna `attiva`), **togli il canale** (dalla 2b: i post di quel canale scartati, con una nota che legge anche l'artigiano; resta almeno un canale; è definitivo), **respingi** (dalla 2b: motivo + nota, email all'artigiano).
- **Nota interna** (dalla 2b), in ogni stato dopo l'invio (R-32).
- In `attiva` e `sospesa`: **sospendi**, **riattiva**, **annulla** (R-33) e **riprogramma** un post fallito (R-34). Nessun altro intervento (R-16).
- Dallo sprint 3: **cambia foto** e **sposta** un post (R-36). Nessuna modifica dell'operatore fa partire l'AI da sola.

Non esistono: togliere un post o un'uscita, fermare un singolo post dopo l'approvazione, una soglia minima di post per approvare. R-06, R-14…R-18, R-20, R-30…R-36.

**2.4 Pubblicazione** (tick ogni minuto): pubblica i post approvati alla loro data, con tutte le loro foto, sulla pagina dell'artigiano; errori temporanei ritentati; un post `fallito` si vede in Vedi campagna, dalla 2b con una notifica agli operatori e con Riprogramma (R-34), dallo sprint 3 anche tra le cose da sistemare della pagina di ingresso; quando ogni post è chiuso la campagna è `conclusa` (R-34). R-01, R-07.

## 3. Motivi del No e interventi
| Motivo | Azione | Limite | Dopo il limite |
|---|---|---|---|
| Foto scattate male | Le foto non idonee restano già fuori dai post. Se quelle buone sono poche: Respingi con motivo `foto`, nota, foto da rifare segnate | — | — |
| Foto ritoccata male dall'AI (sprint 3) | **Ritocca di nuovo** (nota facoltativa), vale solo per quel post | R-03 | Scegli foto originale o versione precedente (non consuma cicli) |
| Foto idonea ma sbagliata per il post (sprint 3) | **Cambia foto** con un'altra del gruppo (R-36) | — | — |
| Testo o hashtag scritti male | **Modifica a mano** (R-30) oppure **Rigenera da zero** o **da testo proposto** + nota; stesse foto | R-03, solo per le rigenerazioni | Resta la modifica a mano |
| Un canale intero non va | **Togli il canale**, con nota | — | — |
| Altro | Respingi con motivo `altro` e nota | — | — |

Ogni intervento crea una nuova versione del post, con il suo autore, che ripassa il validatore; le versioni rifiutate vanno all'AI come "cosa non rifare". Un post `da_rivedere` ha un blocco (R-09): si sblocca con una versione senza blocchi, scritta a mano o dall'AI.

## 4. Cosa vede chi
- **Artigiano**: mai post `da_approvare`, `scartato` o `scaduto`, mai le note interne. In `piano_da_rivedere` e in revisione nessun piano e nessun post. Se `respinta`: motivo, nota e foto da rifare (anche nel Bentornato e per email). Se `scaduta`: avviso (anche per email). Tutto dentro la pagina Campagna, una vista per stato: in `attiva`, `sospesa`, `conclusa` e `annullata` il piano approvato, cioè la strategia e il calendario dei post approvati, pubblicati, falliti o annullati (sprint 3, `GET /campagne/{id}/calendario`), e le metriche (sprint 4). Un post `fallito` o `annullato` si legge "non pubblicato". Se un canale è stato tolto la vista lo dice, con la nota dell'operatore; se la campagna è stata approvata dopo l'inizio dice quanti post non sono usciti. Sospesa: "Pubblicazioni ferme", con il motivo; annullata: "Campagna chiusa dal consorzio il…". Il testo dei post in programma si legge, senza pulsanti per chiedere modifiche: "Qualcosa non va? Chiama il consorzio" (R-29). Non sono pagine a sé.
- **Artigiano**, più di una campagna (dalla 2b): la pagina ne mostra una alla volta, con una riga di scelta in cima; si apre quella che chiede qualcosa: la bozza, poi una respinta o scaduta non ancora sostituita, poi quella in corso, poi quella in lavorazione. "Nuova campagna" sta nella stessa riga, se non c'è già una bozza. Respinta e scaduta restano finché l'artigiano crea una nuova campagna. In fondo l'elenco "Campagne passate". Barra dell'artigiano: Campagna, Profilo bottega, Esci.
- **Operatore**, pagine: ingresso (sprint 3; fino ad allora si arriva su campagne da approvare), campagne da approvare, elenco artigiani, nuovo artigiano, pagina artigiano, campagne chiuse di un artigiano, Vedi campagna, metriche. Si decide solo in Vedi campagna: anche Riprova sta lì. *Campagne da approvare* = le campagne di tutti gli artigiani negli stati della sezione omonima, dalla più urgente (R-38).
- **Operatore**, Vedi campagna: in cima la decisione e il piano (strategia, esito del controllo, avvisi sui riempitivi); le uscite con i post dei loro canali affiancati e, per ogni post, il tipo di riempitivo, blocchi e avvisi del validatore, spunta, storico delle versioni con l'autore; calendario (sprint 3); per ogni gruppo le foto usate e non usate con punteggio e motivo, la fotografia del profilo, decisioni e note interne.
- **Operatore**, pagina artigiano, sezioni: *Da approvare* = inviata, in_generazione, piano_da_rivedere, generazione_fallita, in_revisione · *In corso* = attiva, sospesa · *Storico* = scaduta, conclusa, annullata, respinta: solo le ultime chiuse (R-38), tutte nella pagina delle campagne chiuse, in una sola sezione con un filtro per esito. Un solo pulsante: Vedi campagna.

## 5. Regole
| ID | Regola |
|---|---|
| R-01 | Si pubblica solo un post approvato. |
| R-02 | Ogni intervento crea una nuova versione; le precedenti restano. |
| R-03 | Per post: max **3** rigenerazioni del testo (da zero + da proposta insieme) e max **3** ritocchi della foto. Il ciclo si conta quando nasce la versione. Modifica a mano, scelta e cambio della foto, spostamento non consumano cicli. |
| R-04 | Le versioni rifiutate vanno all'AI come esempi di "cosa non rifare". |
| R-05 | Per ogni canale: post chiesti = post/settimana × giorni della campagna ÷ **7**, per difetto; foto disponibili = foto caricate `idonea` e senza `simile_a`, sommate sui gruppi. Il piano ha, per canale, esattamente i post chiesti: quelli che le foto disponibili non coprono sono riempitivi (R-28). Dalla 2a tra le foto disponibili contano anche le foto d'archivio mai pubblicate su quel canale (R-27). Una foto compare in al massimo **1** post per canale. |
| R-06 | Promemoria all'operatore **48 h** prima dell'inizio, per le campagne `in_revisione` o `piano_da_rivedere`. **Scadenza morbida** (dalla 2b): un post `da_approvare` diventa `scaduto` quando passa la sua data; una campagna con un piano diventa `scaduta`, con i post rimasti, quando i post `da_approvare` sono meno della **metà** dei post chiesti sui canali non tolti; una campagna senza piano scade alle **00:00** (Europe/Rome) del giorno di inizio. |
| R-07 | Permesso scaduto o account non più collegato alla pubblicazione → campagna `sospesa` + avvisi. |
| R-08 | Inizio ≥ oggi + **3** giorni (alla creazione, modifica e invio); durata (fine − inizio + 1) da **7** a **92** giorni; data e ora di ogni post dentro il periodo e mai nel passato (≥ adesso + **15** min). |
| R-09 | Validatore a due livelli. **Blocco**: prezzi o premi che non sono nei dati della bottega, parole vietate, "cose da non dire" del profilo, testo vuoto, limiti della piattaforma (R-21). **Avviso**: limiti editoriali della scheda del canale (R-21). Testo con blocchi o avvisi → riscrive max **3** volte; dopo, con un blocco il post è `da_rivedere`, con i soli avvisi no. Piano non valido → riscrive max **3** volte, poi vale come errore tecnico (R-35). |
| R-10 | Profilo compilato una volta; ai rientri si conferma o si modifica. |
| R-11 | All'invio la campagna salva la fotografia del profilo; generazione e rigenerazioni usano quella. |
| R-12 | Una sola bozza per artigiano; campagne non `annullata/conclusa/respinta/scaduta` non sovrapposte. |
| R-13 | Gruppo: da **1** a **20** foto (`caricate`) oppure `n_immagini` da **1** a **20** (`create_ai`); descrizione obbligatoria all'invio. Invio solo con almeno **4** foto caricate in tutto. Foto: JPG/PNG/WEBP, ≤ **10 MB**, lato corto ≥ **1080 px**. `da_usare_il`, se c'è, cade dentro il periodo della campagna. |
| R-14 | Si approva la campagna in blocco: tutti i post `da_approvare`; quelli con la data già passata diventano `scaduto` (R-06); `scartato` e `scaduto` restano come sono. Mai con un post `da_rivedere`, con un intervento in corso (R-31) o senza post da approvare. Avvisi del validatore e spunte mancanti non bloccano. |
| R-15 | Respinta o scaduta = chiusa; non blocca il periodo; l'artigiano ne crea una nuova. |
| R-16 | In campagna attiva o sospesa nessuna modifica ai post e nessun intervento sul singolo post: si sospende, si riattiva o si annulla (R-33). Unica eccezione: riprogrammare un post fallito (R-34). |
| R-17 | Il ritocco vale solo per il post su cui si lavora; l'originale resta. |
| R-18 | Le foto non idonee restano fuori dai post: l'AI non prova a salvarle. Respingi con motivo `foto` e le foto da rifare segnate quando quelle buone sono poche. Respingi richiede sempre motivo (`foto` / `altro`) e nota; vale da `in_revisione` e da `piano_da_rivedere`. Un post non si toglie: i post calano solo con un canale tolto o per scadenza. |
| R-19 | L'AI crea immagini per i gruppi `create_ai`, sempre in aggiunta alle foto caricate (R-13), e come riempitivo (R-28). Gruppo, descrizione e `n_immagini` si salvano fin da subito; la generazione li ignora. Creazione delle immagini, ritocco e rigenerazione con un prompt **non sono ancora pianificati**: non costruirli finché non c'è un task. Nel frontend il pulsante per aggiungere un gruppo `create_ai` resta nascosto fino ad allora. |
| R-20 | Piano debole: su un canale le foto disponibili sono meno della **metà** dei post chiesti, oppure un gruppo `caricate` non ha nessuna foto idonea. La campagna si ferma in `piano_da_rivedere`. Anche il piano debole ha i post chiesti, con i riempitivi (R-28). Senza nessuna foto disponibile Prosegui non è ammesso. |
| R-21 | Scheda per canale, numeri di prova. Limiti editoriali (avviso): Facebook **500** caratteri e **3** hashtag; Instagram **600** caratteri e **5** hashtag. Limiti della piattaforma (blocco): Facebook **5000** caratteri e **30** hashtag; Instagram **2200** caratteri e **30** hashtag. Max **10** foto per post su entrambi. |
| R-22 | Canali della campagna: almeno uno, tra `facebook` e `instagram`, solo con account `collegato` (creazione e modifica → 422; invio → 409). La frequenza vale per canale. |
| R-23 | Una foto con la stella (`da_usare`), se idonea, è sempre in un post del piano; se non è idonea resta fuori, con il motivo. Una foto con la stella non è mai un doppione: se l'analisi la segna `simile_a` un'altra, `simile_a` passa all'altra. |
| R-24 | Generazione a tappe: analisi, piano e versioni dei post si salvano man mano; una nuova esecuzione, Riprova e Prosegui non rifanno ciò che è già salvato. Il ritocco tocca solo le foto usate dal piano. |
| R-25 | Avvisi nel dettaglio della campagna, non bloccano l'invio: `foto_poche` se le foto caricate sono meno dei post chiesti per canale (quelli che mancano saranno riempitivi, R-28); `riempitivi_molti` se i post che mancano sono più di **1** ogni **2** foto caricate; `frequenza_alta` se post/settimana × **4** supera il massimo della fascia `foto_policy.quantita_mese` (meno_5 → **4**, da5_a12 → **12**, da12_a20 → **20**, oltre_20 → nessun limite; senza fascia nessun avviso). |
| R-26 | La frequenza è un impegno: su ogni canale escono i post chiesti (R-05), non meno. Il prezzo si misura su post/settimana × canali della campagna. Importo e fatturazione sono fuori dall'MVP: nessun dato e nessuna schermata sul prezzo. |
| R-27 | **Archivio della bottega**, dalla 2a: non costruirlo prima (le tabelle nascono già pronte, plan §2). Sono le foto `caricata` e `idonea` di un profilo: quelle delle sue campagne chiuse (`conclusa`, `annullata`, `scaduta`, `respinta`), usate o no, e quelle caricate dal profilo in un gruppo senza campagna. Restano fuori le foto segnate in una decisione `respinta`. Per un canale, una foto d'archivio mai pubblicata lì conta tra le foto disponibili di R-05; una già pubblicata lì torna solo dopo **90** giorni, come riempitivo (R-28). |
| R-28 | **Riempitivi**: i post chiesti che le foto disponibili non coprono hanno `riempitivo`. Sprint 1: solo `cartolina`, immagine **1080 × 1080** px composta dal sistema con il nome della bottega (dalla 2a il logo, se c'è) e il tema dell'uscita. Dalla 2a anche `archivio` (foto già pubblicata su quel canale, R-27). `immagine_ai` quando la creazione delle immagini avrà un task (R-19). Ordine di preferenza, tra i tipi che esistono: `immagine_ai` dal gruppo `create_ai` della campagna, se c'è, fino a `n_immagini`; `archivio` o `cartolina`; `immagine_ai` con una frase o una riflessione ricavata dal profilo, senza prodotti. Nessun tetto: i post restano quelli chiesti. Un riempitivo solo dove le foto disponibili non bastano; su un canale con riempitivi nessun carosello. Ogni riempitivo ha il suo testo, scritto e validato come per gli altri post. Le foto che il piano non usa restano in archivio. |

| R-29 | **Accesso.** Dopo l'accesso: artigiano → pagina Campagna (dalla 2a pagina Profilo, se non ha un profilo); operatore e admin → campagne da approvare (dallo sprint 3 l'ingresso). La sessione scade dopo un periodo senza uso: **7** giorni per l'artigiano, **12** ore per operatore e admin; ogni richiesta la rinnova. L'admin passa ogni controllo di ruolo dell'operatore, non quelli dell'artigiano. Il contatto del consorzio (nome, telefono, email) sta nella configurazione e si legge senza sessione. Nessun recupero della password per email: la cambia il consorzio (comando `cambia-password`; dallo sprint 3 R-37). |
| R-30 | **Modifica a mano e spunta** (dalla 2b), solo in `in_revisione` su un post `da_approvare` senza intervento in corso. Modifica: testo e hashtag; nasce una versione `modifica_operatore` con l'autore, validata; con un blocco → 422 e nessuna versione; testo uguale a prima → 422. Spunta "va bene": chi e quando, visibile a tutti gli operatori; si azzera a ogni nuova versione e a ogni cambio di data; non si mette su un post `da_rivedere`. |
| R-31 | **Intervento in corso**: alla richiesta di un intervento AI il post salva il tipo e l'ora; si spegne quando nasce la versione o alla terza esecuzione fallita (post invariato, ciclo non contato). Un job che trova la campagna fuori da `in_revisione` o il post non `da_approvare` non fa nulla. Un intervento partito da più di **10** minuti vale come fallito: non blocca più e si può rilanciare. Con un intervento in corso sul post nessun altro intervento → 409. |
| R-32 | **Nota interna** (dalla 2b): in ogni stato dopo l'invio, quante se ne vuole; decisione con esito `nota`; la leggono solo gli operatori; nessuno stato, nessuna email. Negli elenchi dell'operatore compare l'ultima. Sostituisce "rimanda". |
| R-33 | **Sospendi, riattiva, annulla** (dalla 2b), ognuna con la sua decisione. Riattiva riceve i post in arretrato (approvati con la data passata) da pubblicare adesso: gli altri diventano `annullato`. Annulla porta ad `annullato` tutti i post `approvato`. Un post `annullato` è chiuso e non si pubblica. |
| R-34 | **Riprogramma** (dalla 2b): un post `fallito`, in campagna attiva o sospesa, torna `approvato` con una nuova data e ora dentro il periodo e ≥ adesso + **15** min; il contenuto non cambia. **Conclusione**: la campagna attiva è `conclusa` quando ogni post è `pubblicato`, `fallito`, `annullato`, `scartato` o `scaduto`; se c'è un post `fallito`, solo dopo la fine del periodo. |
| R-35 | **Errori tecnici dell'AI.** Ogni errore ha un tipo: `temporaneo` (tempo scaduto, rete, troppe richieste, servizio sovraccarico), `risposta` (vuota, troncata, non nel formato chiesto), `configurazione` (chiave, credito, modello), `richiesta` (foto troppo pesante, testo troppo lungo, file mancante), `rifiuto` (filtro del provider). `temporaneo` e `risposta` → nuova esecuzione, **3** in tutto, poi `generazione_fallita`. `configurazione` → `generazione_fallita` subito. `richiesta` o `rifiuto` su una sola foto → la foto diventa non idonea, con il motivo, e si continua; sul testo di un post → versione con testo vuoto e un blocco (`da_rivedere`), e si continua. Di ogni errore che ferma un'esecuzione si salvano tipo, messaggio, tappa e canale; l'operatore legge l'ultimo accanto a Riprova. Dalla 2b una campagna ferma da **30** minuti in `inviata` o `in_generazione` passa a `generazione_fallita` (tipo `temporaneo`). |
| R-36 | **Interventi sul piano** (sprint 3), solo in `in_revisione`. Cambia foto: con una foto `idonea` dello stesso gruppo che non è in un altro post dello stesso canale; nasce una versione `cambio_foto` con lo stesso testo; non vale per i riempitivi. Sposta: nuova data e ora dentro il periodo e ≥ adesso + **15** min; il testo resta. Nessuna delle due fa partire l'AI. **Ritaglio**: una sola funzione per canale, usata da anteprima e pubblicazione, con le proporzioni della scheda; ritaglia al centro e solo se la foto è fuori dalle proporzioni ammesse; in un carosello valgono quelle della prima foto. |
| R-37 | **Nuovo artigiano e password provvisoria** (sprint 3). Anagrafica: obbligatori nome bottega, referente, città, email di accesso, codice consorzio; telefono facoltativo; `iscritto_il` = oggi se vuoto; stato iniziale `attiva`; il codice ART lo assegna il sistema. La password la genera il sistema e la mostra una sola volta; al primo accesso l'utente deve cambiarla (`utente.deve_cambiare_password`). Lo stesso vale per "Nuova password provvisoria" nella pagina artigiano. Iscrizione `sospesa`: l'artigiano entra e legge, ma l'invio → 409; le campagne approvate continuano. |
| R-38 | **Elenchi dell'operatore.** Campagne da approvare: ordinate per "entro quando", cioè la data del primo post `da_approvare` oppure le 00:00 dell'inizio se il piano non c'è. Pagina artigiano: le ultime **3** campagne chiuse, per data di chiusura; le altre nella pagina delle chiuse. Elenco artigiani: codice, bottega, referente, città, iscrizione, stato dell'account per canale, campagne da approvare e in corso, prossima scadenza; ricerca e filtri nel browser. |
| R-39 | **Metriche** (sprint 4). Filtri: artigiano, campagna, periodo (`dal`, `al`, sulla data di pubblicazione; **30** giorni se vuoto). Per ogni post l'ultima rilevazione; i totali sono la somma delle ultime rilevazioni, anche divisi per canale. Post `fallito` e `annullato` fuori dalla tabella; a parte il conteggio dei falliti. Nessun grafico. Report settimanale agli operatori; all'artigiano un riepilogo quando la campagna è `conclusa`. |

## 6. Criteri di accettazione
Dato / Quando / Allora in forma breve. `S` = sprint in cui diventa verde. Il test porta l'ID nel nome (`test_ca09_...`).

| ID | S | Dato → Quando → Allora |
|---|---|---|
| CA-01 | 1 | utente attivo → login corretto → entra con il suo ruolo |
| CA-02 | 1 | utente → password errata → rifiutato, senza dire quale dato è sbagliato |
| CA-03 | 1 | artigiano → funzione operatore → 403 |
| CA-04 | 1 | artigiano → campagna o foto di un altro → 404 |
| CA-05 | 2a | artigiano senza profilo → entra → pagina Profilo, passo 1 |
| CA-06 | 2a | artigiano con profilo → rientra → pagina Campagna con Bentornato; "Va bene così" non salva il profilo, "Modifica" apre la pagina Profilo |
| CA-07 | 2a | passo 9 → manca un obbligatorio → non salva e lo indica |
| CA-08 | 2a | bozza aperta → rientra → pagina Campagna dal passo 10 con dati, canali, gruppi e foto |
| CA-09 | 1 | → crea o invia con inizio < oggi + 3 giorni → 422 (anche bozza ferma) |
| CA-10 | 1 | → durata > 92 giorni, < 7 giorni o fine ≤ inizio → 422 |
| CA-11 | 1 | bozza esistente → nuova bozza → 409 |
| CA-12 | 1 | campagna attiva → periodo sovrapposto → 409; se la precedente è respinta o scaduta → ok |
| CA-13 | 1 | bozza → foto non immagine, > 10 MB o lato < 1080 px, oppure ventunesima foto di un gruppo → 422 con motivo |
| CA-14 | 1 | bozza con meno di 4 foto caricate, o con un gruppo senza descrizione → invio → 422 |
| CA-15 | 1 | bozza completa → invio → inviata, frequenza e obiettivo copiati, snapshot salvato |
| CA-16 | 2a | campagna inviata → profilo modificato → generazione e Riprova usano lo snapshot |
| CA-17 | 1 | 14 giorni, 3 post/sett., 2 canali, un gruppo di 5 foto idonee e diverse → generazione → 6 uscite, 6 post per canale (5 con una foto, 1 cartolina), nessuna foto due volte sullo stesso canale |
| CA-18 | 1 | testo con un blocco → 3 riscritture ancora con un blocco → post `da_rivedere`; con i soli avvisi → non `da_rivedere`, avvisi salvati nella versione |
| CA-19 | 1 | errore `temporaneo` dell'AI a ogni esecuzione → 3 esecuzioni → `generazione_fallita`, con tipo, messaggio, tappa e canale salvati; Riprova → inviata e riparte |
| CA-20 | 1 | generazione riuscita → piano salvato, post `da_approvare`, campagna `in_revisione` |
| CA-21 | 1 | in revisione senza post da rivedere → approva → post `da_approvare` approvati, campagna attiva, riga approvazione per post; i post con la data già passata diventano `scaduto`; avvisi del validatore → approva ammesso |
| CA-22 | 1 | post `da_rivedere` o intervento in corso (dalla 2b) → approva → 409 |
| CA-23 | 2b | campagna dopo l'invio → nota interna → stato invariato, decisione `nota`, nessuna email; l'artigiano non la vede |
| CA-24 | 2b | in revisione → respingi senza motivo o nota → 422 |
| CA-25 | 2b | in revisione → respingi `foto` con 2 foto segnate → respinta, post scartati, email con motivo, nota, 2 miniature |
| CA-26 | 2b | post → rigenera da zero → nuova versione, stesse foto, validata |
| CA-27 | 2b | post → rigenera da proposta senza testo → 422; con testo → nuova versione, stesse foto |
| CA-28 | 2b | post con 3 rigenerazioni → quarta → 409; la modifica a mano resta ammessa |
| CA-29 | 2b | campagna attiva o sospesa → modifica a mano, rigenerazione o spunta su un post → 409 |
| CA-30 | 2b | in revisione → passa la data di un post → quel post `scaduto`, campagna ancora approvabile; restano `da_approvare` meno della metà dei post chiesti → campagna `scaduta`, post rimasti scaduti, email; campagna senza piano → `scaduta` alle 00:00 del giorno di inizio |
| CA-31 | 2b | in revisione o `piano_da_rivedere` → artigiano apre → nessun piano e nessun post; respinta → vede motivo, nota, foto |
| CA-32 | 2b | attiva → sospendi → non pubblica; riattiva con post in arretrato → quelli scelti tornano pubblicabili, gli altri `annullato`; annulla → post `approvato` annullati, non pubblica più; ogni azione ha la sua decisione |
| CA-33 | 3 | generazione → ogni foto ha versione ritoccata e l'originale resta |
| CA-34 | 3 | foto usata su 2 canali → ritocca per un post → cambia solo quello |
| CA-35 | 3 | 3 ritocchi → quarto → 409; scegli originale → ok senza consumare cicli |
| CA-36 | 1 | post approvato con data raggiunta → due tick → pubblicato una volta sola |
| CA-37 | 1 | post da approvare con data raggiunta → tick → non pubblicato |
| CA-38 | 1 | errore temporaneo del social ×3 → post `fallito`, visibile all'operatore in Vedi campagna |
| CA-39 | 1 | attiva → ogni post `pubblicato`, `scartato` o `scaduto` → conclusa; con un post `fallito` → resta attiva fino alla fine del periodo, poi conclusa |
| CA-40 | 3 | permesso scaduto o account scollegato dopo l'invio → prima pubblicazione → sospesa + avvisi |
| CA-41 | 3 | campagne in stati diversi → pagina artigiano → ognuna nella sezione giusta (§4); delle chiuse solo le ultime 3, le altre nella pagina delle campagne chiuse |
| CA-42 | 3 | in revisione o `piano_da_rivedere`, inizio tra < 48 h → tick orario → un promemoria, una volta |
| CA-43 | 3 | nome diverso tra anagrafica e profilo → pagina artigiano → differenza segnalata |
| CA-44 | 4 | post pubblicato → lettura giornaliera → metriche salvate e visibili |
| CA-45 | 4 | sistema completo → invio e approvazione → post pubblicati (E2E nel browser) |
| CA-46 | 1 | bozza → gruppo `create_ai` con descrizione e `n_immagini` → salvato e restituito nel dettaglio; non conta per le 4 foto dell'invio (CA-14) |
| CA-47 | 1 | → gruppo `create_ai` con `n_immagini` fuori da 1–20, foto caricata in un gruppo `create_ai`, o `da_usare_il` fuori dal periodo → 422 |
| CA-48 | 1 | canale senza account collegato → crea o modifica la bozza con quel canale → 422; account scollegato dopo → invio → 409 |
| CA-49 | 1 | su un canale foto disponibili sotto la metà dei post chiesti → generazione → `piano_da_rivedere`, nessun testo generato; Prosegui → riparte e arriva a `in_revisione` |
| CA-50 | 1 | generazione fallita dopo l'analisi → Riprova → le foto già analizzate non si rianalizzano |
| CA-51 | 1 | foto con la stella idonea → è in un post del piano; non idonea → resta fuori, con il motivo; quasi uguale a un'altra senza stella → il doppione è l'altra |
| CA-52 | 1 | piano con un carosello → post con più foto in ordine; pubblicato una volta con tutte le foto |
| CA-53 | 2b | in revisione con 2 canali → togli un canale con nota → i suoi post scartati; approva → gli altri approvati; togliere l'ultimo canale → 409; l'artigiano vede il canale tolto e la nota |
| CA-54 | 1 | bozza con foto caricate sotto i post chiesti per canale → dettaglio → avviso `foto_poche`, e `riempitivi_molti` se i post che mancano sono più di 1 ogni 2 foto caricate; profilo `meno_5` con frequenza `f3_4` → avviso `frequenza_alta`; l'invio resta ammesso |
| CA-55 | 2b | campagna pronta, ferma in `piano_da_rivedere`, in `generazione_fallita`, o post `fallito` → una notifica agli operatori per ogni evento |
| CA-56 | 3 | campagna attiva → il proprietario legge il calendario → strategia e soli post approvati, pubblicati, falliti o annullati, e il numero dei post scaduti; prima dell'approvazione → 409; campagna di un altro → 404 |
| CA-57 | 1 | su un canale foto disponibili meno dei post chiesti → generazione → i post del canale sono quelli chiesti; quelli che mancano sono `cartolina`, ognuno con la sua immagine di 1080 × 1080 px e il suo testo; su quel canale nessun carosello; approvato e arrivato alla data → pubblicato con la sua immagine |
| CA-58 | 1 | errore `configurazione` dell'AI → prima esecuzione → `generazione_fallita`, nessun'altra esecuzione |
| CA-59 | 1 | errore `richiesta` o `rifiuto` su una sola foto → la foto resta fuori con il motivo, la generazione arriva a `in_revisione` |
| CA-60 | 1 | operatore → Vedi campagna in `generazione_fallita` → legge tipo, messaggio, tappa e canale dell'ultimo errore |
| CA-61 | 1 | admin → funzione dell'operatore → ammesso; funzione dell'artigiano → 403 |
| CA-62 | 1 | sessione non usata oltre la durata del suo ruolo → 401; usata prima → resta valida e la scadenza si sposta |
| CA-63 | 1 | senza sessione → `GET /consorzio` → nome, telefono, email |
| CA-64 | 2b | post in revisione → modifica a mano → versione `modifica_operatore` con autore, validata, cicli invariati, spunta azzerata; con un blocco o senza cambiamenti → 422, nessuna versione |
| CA-65 | 2b | post → spunta → chi e quando salvati; nuova versione → spunta azzerata; post `da_rivedere` → spunta → 409 |
| CA-66 | 2b | rigenerazione fallita 3 volte → post invariato, ciclo non contato, intervento spento; intervento partito da più di 10 minuti → approva ammesso |
| CA-67 | 2b | post `fallito` in campagna attiva → riprogramma dentro il periodo → `approvato` con la nuova data, decisione `riprogrammato`; fuori dal periodo o nel passato → 422; post non fallito → 409 |
| CA-68 | 2b | campagna ferma da 30 minuti in `inviata` o `in_generazione` → tick → `generazione_fallita` con errore `temporaneo` |
| CA-69 | 2b | operatore → campagne da approvare → per ogni campagna conteggi dei post, entro quando e ultima nota interna, dalla più urgente |
| CA-70 | 2b | artigiano con più campagne → pagina Campagna → apre quella che chiede qualcosa (§4), con la riga di scelta |
| CA-71 | 3 | post in revisione → cambia foto con una idonea del gruppo libera su quel canale → versione `cambio_foto`, stesso testo; foto di un altro gruppo, non idonea o già sul canale → 422 |
| CA-72 | 3 | post in revisione → sposta dentro il periodo → nuova data, spunta azzerata; fuori dal periodo o nel passato → 422 |
| CA-73 | 3 | nuovo artigiano → password provvisoria mostrata una volta → al primo accesso deve cambiarla prima di ogni altra pagina |
| CA-74 | 3 | iscrizione sospesa → invio → 409; le campagne approvate continuano a uscire |
| CA-75 | 4 | metriche senza date → ultimi 30 giorni; per ogni post l'ultima rilevazione; falliti e annullati fuori dalla tabella |
