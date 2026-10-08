# Note sul flusso · AdFlow Suite

Appunti che spiegano il flusso disegnato nella cartella `architettura/` (diagrammi 01, 03, 04, 07, 09 e pagine statiche), con il perché delle decisioni. Materiale in continua rimodulazione. La versione breve per gli agenti è `docs/agenti/spec.md` (vedi `LEGGIMI.md`); l'architettura è spiegata in [`note-architettura.md`](note-architettura.md); le decisioni con il perché in [`ADR.md`](ADR.md); ciò che è ancora aperto sta in [`lavori-aperti.md`](lavori-aperti.md).

**Versione:** 5.7 del 07/10/2026 · **Autore:** B3 · Architetto software · Diagrammi in `architettura/diagrammi/` (sorgente `architettura/AdFlow-diagrammi.html`).

---

## 1. Problema e obiettivo

Gli artigiani di un consorzio non hanno tempo né competenze per pubblicare con regolarità sui social. AdFlow Suite trasforma **le loro foto reali** e **il racconto della loro bottega** in un calendario di post per Facebook e Instagram. Un **operatore del consorzio** controlla tutto prima che esca: nessun post viene pubblicato senza la sua approvazione.

In sintesi:
- l'artigiano compila una volta il **profilo della bottega** e, per ogni periodo, crea una **campagna**: sceglie i canali e carica le sue foto a **gruppi**; se vuole, aggiunge un gruppo di **immagini da creare** con l'AI;
- l'AI analizza le foto, scrive un **piano editoriale** (quali uscite, su quali canali, con quali foto, quando), ritocca le foto scelte, crea le immagini richieste e scrive **tutti i post del periodo**, uno per canale; un controllo a regole verifica il piano e i testi;
- l'operatore rivede la campagna: un post che non va lo sistema, a mano o con l'AI, poi **approva o respinge** la campagna intera;
- i post approvati si pubblicano da soli, alle date stabilite, sulla **pagina social dell'artigiano**; poi si raccolgono le metriche.

![Flusso generale](architettura/diagrammi/01-flusso-generale.png)

## 2. Attori

| Attore | Chi è | Cosa fa |
|---|---|---|
| **Artigiano** | Titolare di una bottega iscritta al consorzio | Compila il profilo, crea e invia le campagne con le foto (e, se vuole, con immagini create dall'AI), vede il piano approvato e le metriche |
| **Operatore** | Persona del consorzio | Gestisce anagrafica e account social degli artigiani, rivede le campagne, decide su ognuna |
| **Admin** | Amministratore del sistema | Crea operatori, configura il sistema |
| **Sistema** | Processi automatici | Genera i post, controlla scadenze, pubblica, raccoglie metriche, invia email |

C'è **un solo consorzio**.

---

## 3. Fase 1 · Profilo bottega e nuova campagna (artigiano)

Profilo e campagna sono **due pagine** (D-35): la pagina **Profilo bottega** con i passi 1–9 e la pagina **Campagna** con i passi 10–11 e il riepilogo con l'invio. La numerazione dei passi resta quella di prima, così i riferimenti non cambiano. Schemi di riferimento: `pagine/AdFlow-profilo-bottega.html` e `pagine/AdFlow-campagna.html`; diagramma 09.

| Pagina | Passi | Contenuto | Quando si salva |
|---|---|---|---|
| Profilo bottega | 1–9 | Identità, storia, prodotti (**tipo di prodotto** da elenco), pubblico e obiettivo, voce e vincoli ("cose da non dire mai"), presenza social attuale, politica foto, calendario eventi ricorrenti, logistica (canali, frequenza, orari) | Lasciando il passo 9 |
| Campagna | 10–11 | Nome, inizio, fine, commenti del periodo, **canali** della campagna; foto caricate a **gruppi** (da 1 a 20 foto), con una descrizione per gruppo, una data facoltativa e la stella sulle foto da usare per forza; gruppi di **immagini da creare** con l'AI | Lasciando il passo 10 nasce la **bozza**; ogni foto appena caricata; la descrizione mentre si scrive |
| Campagna · riepilogo | 12 | Rilettura, campi obbligatori mancanti evidenziati, avvisi sulla quantità di foto, un solo invio | Controlla e invia |

| # | Passo | Cosa succede |
|---|---|---|
| 1.0 | Accesso | L'artigiano entra con le sue credenziali. Se il profilo esiste va alla pagina Campagna, che si apre con il Bentornato; altrimenti alla pagina Profilo, passo 1 |
| 1.1 | Pagina Profilo · passi 1–9 *(una volta)* | Compila il profilo; salvandolo passa alla pagina Campagna |
| 1.1b | **Bentornato** *(ai rientri)* | In cima alla pagina Campagna, riepilogo del profilo: **Va bene così** → passo 10 senza salvare nulla; **Modifica** → pagina Profilo già compilata. Riprende la bozza aperta. Se l'ultima campagna è stata respinta mostra **motivo, richiesta di modifica e foto da rifare** (D-09, D-23, D-30) |
| 1.2 | Account social *(una volta, fuori dalle due pagine)* | L'artigiano autorizza la sua pagina insieme all'operatore. **Senza account collegato un canale non si può dichiarare** e la campagna non si invia (D-39) |
| 1.3 | Pagina Campagna · passo 10 | Inizio **almeno 3 giorni dopo oggi**, durata da **7 giorni** a **3 mesi**, periodo non sovrapposto ad altre sue campagne (D-14, D-25, D-42). **Canali della campagna**: uno o più tra quelli collegati; la pagina propone quelli del profilo (D-39) |
| 1.4 | Foto a gruppi · passo 11 | Foto reali caricate subito, in gruppi da **1 a 20 foto**. Per ogni gruppo una descrizione, obbligatoria all'invio, e una data facoltativa "da usare verso il…", dentro il periodo della campagna; su ogni foto la **stella** "da usare per forza"; linea guida per tipo di prodotto (Appendice A) (D-10, D-41) |
| 1.4b | Immagini AI · passo 11 | L'artigiano può aggiungere un **gruppo di immagini da creare**: scrive che cosa si deve vedere e quante immagini vuole (da 1 a 20). È un gruppo a sé, mai mescolato alle foto caricate, e non le sostituisce: le 4 foto caricate servono comunque (D-36, D-37, D-42). Le immagini create occupano i posti dei riempitivi (§4.3). *La creazione non è ancora costruita* (lavori-aperti.md A-05): fino ad allora nel programma il pulsante resta nascosto (ADR-80) |
| 1.5 | Controllo tecnico foto | Solo per le foto caricate. Al caricamento: JPG, PNG o WEBP, al massimo 10 MB, lato corto almeno 1080 px; altrimenti si ricarica. Luce e nitidezza le valuta l'AI in generazione: una foto non idonea resta fuori dai post e l'operatore ne vede il motivo (D-17, D-46) |
| 1.6 | Riepilogo e invio · passo 12 | Controlla gli obbligatori e i minimi (almeno 4 foto caricate), ricontrolla che i canali siano collegati, mostra gli **avvisi** sulla quantità di foto, copia nella campagna frequenza e obiettivo del profilo e ne salva una **fotografia**; la generazione parte da sola (D-12, D-13, D-18, D-48) |

**Obbligatori.** Profilo: nome bottega, referente, città, tipo di prodotto, clienti ideali, obiettivo, canali di pubblicazione. Campagna: nome, inizio, fine, commenti, almeno un canale. Foto: almeno un gruppo e almeno **4 foto caricate** in tutto; ogni gruppo con la sua descrizione; un gruppo di immagini da creare ha anche il numero di immagini (R-13, R-19).

**Perché la fotografia del profilo.** Il profilo può cambiare mentre una campagna è in corso. La campagna usa sempre il profilo com'era all'invio: la modifica vale dalla campagna successiva, e l'operatore vede esattamente ciò che ha ricevuto l'AI (D-13).

**Anticipo minimo.** L'inizio deve cadere almeno 3 giorni dopo oggi; il controllo si ripete all'invio, perché una bozza lasciata ferma può non rispettarlo più. Serve all'operatore per rivedere prima che i primi post scadano (D-25, ADR-95).

**Account social.** Un canale si dichiara solo se la pagina dell'artigiano è collegata; all'invio il controllo si ripete e, se manca, il messaggio è "social non connesso: contatta il consorzio". Se il permesso scade dopo l'invio, alla prima pubblicazione la campagna passa a "sospesa" e partono le notifiche (R-07).

**Canali e frequenza.** I canali si dichiarano sulla campagna: una campagna può uscire su un solo social o su più di uno. La frequenza del profilo vale **per canale**: "3 a settimana" su Facebook e Instagram sono 6 post a settimana. Il materiale è lo stesso per tutti i canali; cambiano lo stile, il formato, il numero dei post e il calendario (D-39, D-40). La frequenza è un **impegno**: sono i post a settimana che l'artigiano sceglie e paga, contati sul totale dei canali della campagna (ADR-81).

**Avvisi prima dell'invio.** Non bloccano (D-48):
- le foto caricate sono meno dei post chiesti per canale: "con queste foto 6 dei 12 post per canale saranno cartoline: aggiungine 6"; se i post senza foto sono più di uno ogni due foto caricate, l'avviso lo dice (§4.3);
- la frequenza è alta rispetto alle foto che l'artigiano dichiara nel profilo: i post a settimana per 4 superano il massimo della fascia dichiarata (meno di 5 foto al mese → 4; da 5 a 12 → 12; da 12 a 20 → 20);
- consiglio di caricare almeno due tipi di contenuto diversi (Appendice A).

I primi due li calcola il server e li dà alla pagina con il dettaglio della campagna (ADR-73, R-25).

## 4. Fase 2 · Generazione con AI (sistema)

| # | Passo | Cosa succede |
|---|---|---|
| 2.1 | Analisi dei gruppi | Per ogni gruppo l'AI guarda le foto insieme alla descrizione: soggetto, tipo di contenuto, qualità. Segna ogni foto come **idonea** o no, segna gli scatti quasi uguali (mai una foto con la stella: il doppione è l'altra), dà un **punteggio** e un **motivo**. Il risultato si salva foto per foto (§4.1, D-46) |
| 2.2 | Piano editoriale | L'AI, con un prompt da social media manager, scrive il piano: le **uscite** (un tema e un gruppo), per ogni canale i post, il formato (foto singola o carosello), le foto, giorno e ora. Quanti sono non lo decide lei: sono quelli scelti dall'artigiano (ADR-81). Lo sfasamento tra i canali lo decide lei; gli orari preferiti del profilo sono un'indicazione. Sta dentro i limiti di capacità (R-05); le foto con la stella, se idonee, entrano sempre (D-43, D-44, D-45) |
| 2.3 | Controllo del piano | A regole: post per canale uguali a quelli scelti, riempitivi solo dove le foto non bastano, limiti per canale rispettati, nessuna foto ripetuta sul canale, foto con la stella presenti, date dentro il periodo e mai nel passato. La data di un gruppo è un'indicazione per l'AI, non una regola del controllo: l'operatore la vede accanto all'uscita (ADR-74). Se non passa, l'AI lo riscrive (max 3). Se passa ma è **debole** (R-20), la campagna si ferma in "piano da rivedere" e decide l'operatore (D-47) |
| 2.3b | Cartoline | Per ogni post che il piano ha segnato come cartolina il sistema compone l'immagine, senza AI, e la salva come una foto (§4.3, ADR-88) |
| 2.4 | Ritocco foto | L'AI ritocca **solo le foto scelte dal piano**; l'originale resta sempre (D-31, D-49). *Che cosa fa il ritocco e con quali istruzioni lo decide un task di analisi* (lavori-aperti.md A-01) |
| 2.5 | Creazione immagini | Solo per i gruppi di immagini da creare, e solo per le immagini che il piano usa: l'AI trasforma la descrizione dell'artigiano in un prompt, partendo da profilo e campagna, poi crea l'immagine. In revisione l'operatore può ritoccarla o rigenerarla con un prompt (D-36, D-37). *Cicli, etichetta nel post, modello e costi da definire* (lavori-aperti.md A-05) |
| 2.6 | Generazione post | Per ogni post testo e hashtag nello stile del suo canale (§4.2), con le sue foto, il tema dell'uscita, le istruzioni per tipo di prodotto, la fotografia del profilo, eventi, chiusure e commenti del periodo (D-16, D-50) |
| 2.7 | Controllo a regole | Due livelli (ADR-91). **Blocchi**: parole vietate (comprese le "cose da non dire" del profilo), prezzi o premi inventati, limiti veri della piattaforma. **Avvisi**: i limiti editoriali del canale (lunghezza, numero di hashtag). Se il testo non va si riscrive (max 3); dopo, con un blocco il post è **"da rivedere"**, con i soli avvisi no: l'operatore li vede e decide |
| 2.8 | Campagna pronta | Post "da approvare", campagna "in revisione". Dalla 2b una notifica avvisa gli operatori; lo stesso quando la campagna si ferma in "piano da rivedere" o va in "generazione fallita" (ADR-77) |
| 2.9 | Errore tecnico dell'AI | Si riprova da soli (3 volte in tutto); ciò che è già salvato non si rifà. Se fallisce anche la terza: campagna "generazione fallita". L'operatore preme **Riprova**, che riparte da dove si era fermata, oppure toglie il canale che fallisce e prosegue con l'altro (R-09, R-24, D-49, D-51). Ogni errore ha un tipo, un messaggio, la tappa e il canale, e l'operatore li legge accanto a Riprova: gli errori temporanei e le risposte malformate si ritentano, quelli di configurazione fermano subito la generazione; un errore su una sola foto la lascia fuori con il motivo, e un testo rifiutato dal filtro del provider rende il post "da rivedere". Una campagna ferma da 30 minuti passa a "generazione fallita" (ADR-98) |

### 4.1 Come l'AI sceglie le foto

Dentro ogni gruppo, in quest'ordine (D-46):

1. **Idoneità tecnica**: nitidezza, luce, misura. È un filtro: la foto che non passa resta fuori.
2. **Vincoli del profilo**: se la politica foto dice "persone: mai", le foto con persone riconoscibili restano fuori.
3. **Stella dell'artigiano**: una foto con la stella, se idonea, entra sempre in un post.
4. **Pertinenza** con la descrizione del gruppo.
5. **Varietà**: gli scatti quasi uguali contano come uno e non finiscono in post diversi.
6. **Formato del canale**: verticale per Instagram, orizzontale per Facebook.

Ogni foto riceve un punteggio e un motivo, che l'operatore vede in Vedi campagna insieme alle foto rimaste fuori.

**Capacità di un gruppo.** L'**offerta** sono le foto idonee e diverse tra loro: venti scatti dello stesso tavolo valgono uno. La **domanda** è la frequenza per le settimane della campagna, per ogni canale. La capacità è il minore dei due, ma su un canale escono sempre i post scelti: quelli oltre la capacità sono riempitivi (§4.3). Una foto esce al massimo una volta per canale (R-05). Un carosello usa più foto in un post solo: più caroselli, meno post. È una scelta editoriale, non un modo per usare le foto in più: quelle che il piano non usa restano in archivio (ADR-85).
### 4.2 Scheda per canale

Un solo posto per ciò che distingue un canale: la leggono il prompt, il controllo a regole e le anteprime (D-50). Nell'MVP i canali sono Facebook e Instagram, solo con foto.

| | Facebook | Instagram |
|---|---|---|
| Testo | fino a 500 caratteri; può raccontare | fino a 600 caratteri; conta la prima riga |
| Hashtag | fino a 3 | fino a 5 |
| Link nel testo | si aprono | non si aprono: l'invito è "scrivici" o "link in bio" |
| Foto | orizzontale o proporzioni originali | verticale 4:5 |
| Foto per post | da 1 a 10 | da 1 a 10 |
| Stile | racconto, informazioni locali, eventi | immagine prima di tutto, frase d'apertura breve |

I numeri sono **di prova** (R-21): si confermano con lavori-aperti.md A-06.

### 4.3 Presenza costante: archivio e riempitivi

Deciso il 07/10/2026 (ADR-81…88). Si costruisce a tappe: nello sprint 1 la cartolina, così i post sono esatti da subito; nella 2a l'archivio della bottega, il logo e le foto d'archivio nel piano; le immagini AI quando la loro creazione avrà un task (lavori-aperti.md A-05). Ciò che resta da definire per la 2a è in lavori-aperti.md A-08.

L'artigiano sceglie e paga un ritmo, e uno scopo del progetto è la presenza costante. Per questo su ogni canale escono **sempre i post scelti**: quelli che le foto nuove non coprono li completa il piano.

| Che cosa | Da dove viene | Conta come |
|---|---|---|
| Foto della campagna | Caricata al passo 11 | Foto nuova |
| Foto d'archivio mai uscita su quel canale | Archivio della bottega | Foto nuova |
| Immagine chiesta dall'artigiano | Il gruppo di immagini da creare della campagna: decide lui che cosa si vede, anche un prodotto, e quante al massimo | Riempitivo, il primo che il piano usa |
| Foto d'archivio già uscita su quel canale | Archivio della bottega, dopo almeno 90 giorni | Riempitivo, secondo |
| Cartolina | Un'immagine quadrata composta dal sistema, senza AI: nome della bottega (dalla 2a il logo) e il tema dell'uscita | Riempitivo, secondo; nello sprint 1 è l'unico |
| Immagine AI con una frase o una riflessione | Ricavata dal profilo, sul materiale e sul mestiere; mai un prodotto | Riempitivo, ultimo |

**Ordine.** È una preferenza che il piano riceve; il controllo non la verifica.

**Nessun tetto, un avviso.** I riempitivi non tolgono mai post. Quando su un canale sono più di uno ogni due post con una foto nuova, cioè oltre un terzo dei post, l'artigiano lo legge al passo 12 e l'operatore in Vedi campagna: è il segnale che conviene aggiungere foto. Con 13 post scelti e 9 foto nuove i riempitivi sono 4, dentro la soglia; con 6 foto nuove sono 7, e l'avviso scatta. Su un canale che ha riempitivi il piano non fa caroselli: ogni foto buona vale un post. Il piano debole resta quello di prima (R-20): sotto la metà di foto la campagna passa dall'operatore prima dei testi, con i post comunque tutti presenti.

**Archivio della bottega.** Ogni foto caricata e idonea resta legata al profilo, usata o no, e ci entra quando la sua campagna si chiude: le foto in più, o quelle di una campagna scaduta, non si perdono e servono a quelle dopo. Vale canale per canale: su un canale dove la bottega non ha mai pubblicato, tutto l'archivio è nuovo. Nel profilo l'artigiano può aggiungere foto sempre valide (il laboratorio, le mani al lavoro, la vetrina) e il logo. Sono facoltativi: con l'archivio vuoto, come alla prima campagna, i riempitivi sono cartoline e immagini AI, che non ne hanno bisogno.

**Testo.** Ogni riempitivo ha un testo nuovo: è il testo a tenere viva l'attenzione quando l'immagine non è nuova.

**Immagini AI.** L'opzione per averle su richiesta è nella campagna: il gruppo di immagini da creare (passo 1.4b). Lì decide l'artigiano, e il piano le usa per prime. Senza quel gruppo le immagini AI sono solo frasi e riflessioni illustrate, senza prodotti: così non esce, a sua insaputa, un oggetto che la bottega non fa. Temi e stile vengono dal profilo: il programma non conosce il legno o la ceramica, li legge.

## 5. Fase 3 · Revisione e approvazione in blocco (operatore)

| # | Passo | Cosa succede |
|---|---|---|
| 3.1 | Dashboard operatore | Campagne da approvare di tutti gli artigiani, dalla più urgente; elenco artigiani; pagina artigiano con le campagne in tre sezioni e un solo pulsante **Vedi campagna**; promemoria 48 ore prima dell'inizio (D-38) |
| 3.2 | Vedi campagna | Si apre in ogni stato dopo l'invio (ADR-101). In cima la decisione e il piano; sotto tutte le uscite, ognuna con i post dei suoi canali, in elenco e in calendario: testo, hashtag, foto, tipo di riempitivo, avvisi del controllo, storico versioni; per ogni gruppo le foto rimaste fuori, con il motivo; profilo bottega (fotografia) in sola lettura; decisioni e note interne |
| 3.2b | Piano da rivedere | Se il piano è debole la campagna arriva all'operatore prima dei testi: vede il piano e le foto e sceglie **Prosegui** (si generano i post) oppure **Respingi** (D-47). Nello sprint 1 c'è solo Prosegui (ADR-79) |
| 3.3 | Sistemare i post | Un post non si toglie: si sistema (ADR-90). L'operatore lo **modifica a mano** (testo e hashtag, senza consumare cicli, ADR-89) oppure sceglie il motivo e il suo ciclo AI (tabella sotto). Ogni intervento crea una nuova versione, con il suo autore, che ripassa il controllo a regole. La spunta **"va bene"** segna i post già controllati (ADR-92). Dallo sprint 3 può anche cambiare una foto con un'altra del gruppo e spostare la data di un post; nessuna modifica fa partire l'AI da sola (ADR-99) |
| 3.4 | Decisione sulla campagna | **Approva**: tutti i post da approvare approvati, campagna attiva (non se un post è "da rivedere" o ha un intervento in corso; avvisi e spunte mancanti non bloccano). **Togli il canale**: i post di quel canale diventano scartati, con una nota che legge anche l'artigiano, e si approva il resto. **Nota interna**: quante se ne vuole, solo per gli operatori, nessun cambio di stato (ADR-94). **Respingi**: motivo e nota obbligatori, email all'artigiano (D-20, D-23, D-30, D-51) |
| 3.5 | Scadenza | Morbida (ADR-95): ogni post da approvare scade quando passa la sua data; la campagna è **scaduta** quando i post ancora approvabili sono meno della metà di quelli chiesti, con l'email all'artigiano. Una campagna senza piano scade alle 00:00 del giorno di inizio |
| 3.6 | Dopo l'approvazione | **Nessuna modifica** ai post e nessun intervento sul singolo post: si sospende o si annulla la campagna (D-34). Riattiva chiede che cosa fare dei post in arretrato; Annulla porta ad "annullato" i post non usciti (ADR-96). Unica eccezione: un post fallito si può riprogrammare (ADR-97) |
| 3.7 | Artigiano informato | Dopo l'approvazione vede il piano in sola lettura: la strategia in breve e il calendario dei post (D-52); email di riepilogo; email per respinta e scadenza |

### 5.1 Motivi del No e cicli

| Motivo | Dove agisce | Ciclo | Limite | Quando i cicli finiscono |
|---|---|---|---|---|
| **Foto scattate male** (buie, mosse, soggetto sbagliato) | Campagna intera | L'AI le lascia già fuori dai post (§4.1). Se quelle buone sono troppo poche: **Respingi** con motivo "foto", nota obbligatoria e foto da rifare segnate; email all'artigiano con le miniature. La campagna resta "respinta" nello storico; l'artigiano ne crea una nuova con foto nuove | — | — |
| **Foto ritoccate male dall'AI** | Singolo post | **Ritocca di nuovo**, con nota facoltativa: nuova versione della foto **solo per quel post**, anche se la stessa foto esce anche sull'altro canale | 3 ritocchi per post | Si sceglie la foto originale o una versione precedente (non consuma cicli) |
| **Testo o hashtag scritti male** | Singolo post | ① **Modifica a mano** di testo e hashtag: non consuma cicli · ② **Rigenera da zero**, con le stesse foto · ③ **Rigenera da un testo proposto** dall'operatore più indicazioni, con le stesse foto | 3 rigenerazioni per post (② e ③ insieme) | Resta la modifica a mano |
| **Foto idonea ma sbagliata per il post** (dallo sprint 3) | Singolo post | **Cambia foto** con un'altra idonea dello stesso gruppo, non ancora uscita su quel canale; il testo resta e va riletto | — | — |
| Altro | Campagna intera | **Respingi** con motivo "altro" e nota | — | — |

Le versioni rifiutate diventano esempi di "cosa non rifare" per l'AI (R-04). Un post "da rivedere" ha un blocco del controllo a regole: si sblocca con una modifica a mano o con una rigenerazione che lo toglie. Quando tutti i post vanno bene, l'operatore approva in blocco. Se un canale intero non va, lo toglie e approva l'altro (D-51).

### 5.2 Dashboard operatore

Otto pagine (D-38): **ingresso**, **campagne da approvare**, **elenco artigiani**, **nuovo artigiano**, **pagina artigiano**, **campagne chiuse**, **Vedi campagna**, **metriche**. Schemi in `pagine/` (mappa in `pagine/index.html`): tutti approvati, compresa Vedi campagna, ridisegnata sul modello a uscite (ADR-101, ADR-111); le domande in fondo alle pagine sono chiuse (ADR-89…110). La pagina artigiano mostra le campagne da approvare, quelle in corso e le prime dello storico; le altre stanno nella pagina delle campagne chiuse, raggiunta da un pulsante.

| Parte della pagina artigiano | Contenuto | Chi la scrive |
|---|---|---|
| Anagrafica | Codice artigiano, codice consorzio, nome bottega, referente, città, email di accesso, telefono, iscrizione | Solo l'operatore (D-28) |
| Account social | Stato del collegamento per canale, con Collega / Ricollega | Operatore insieme all'artigiano |
| Situazione | Bozza aperta (solo informativa), ultima modifica del profilo, conteggi dei post, link alle metriche | Sistema |
| Campagne | Tre sezioni (ADR-53); per ognuna periodo, canali, foto, post per stato, prossima scadenza, pulsante **Vedi campagna** | Sistema |
| Profilo bottega | Passi 1–9 in sola lettura (profilo di oggi) | Artigiano |

| Sezione | Stati della campagna |
|---|---|
| Da approvare | inviata, in generazione, piano da rivedere, generazione fallita (Riprova sta in Vedi campagna), in revisione; accanto, l'ultima nota interna |
| In corso | attiva, sospesa |
| Storico (le prime; le altre in una pagina a parte) | scaduta, conclusa, annullata, respinta |

Nome, referente e città stanno sia nell'anagrafica (dato ufficiale) sia nel passo 1 del profilo: se sono diversi, la pagina lo segnala.

### 5.3 Dashboard artigiano

L'artigiano vede **l'esito** del lavoro dell'operatore, mai il lavoro in corso. Non è una pagina a sé: dopo l'invio la pagina Campagna mostra una vista per stato, con il calendario e le metriche (ADR-55; schema in `pagine/AdFlow-campagna-stati.html`).

| Stato campagna | Cosa vede | Cosa può fare |
|---|---|---|
| bozza | La pagina Campagna con dati, canali, gruppi e foto salvati | Modifica, aggiunge o toglie foto e gruppi, invia |
| inviata / in generazione | "Generazione dei post in corso…" | Attendere |
| generazione fallita | Avviso di problema tecnico | Attendere: rilancia l'operatore |
| piano da rivedere / in revisione | Nessun piano e nessun post | Attendere |
| respinta | Motivo, richiesta di modifica, foto da rifare (anche per email e nel Bentornato) | Creare una nuova campagna |
| scaduta | "La campagna non è stata approvata in tempo" (anche per email) | Creare una nuova campagna |
| attiva / sospesa / conclusa | Il piano approvato: strategia in breve e calendario dei post approvati, pubblicati o falliti (D-52, ADR-78); se un canale è stato tolto, lo dice con la nota dell'operatore (ADR-76); un post fallito o annullato si legge "non pubblicato"; se la campagna è stata approvata dopo l'inizio, dice quanti post non sono usciti (ADR-95) | Consultare |
| annullata | "Campagna chiusa dal consorzio il…", con i post già usciti | Creare una nuova campagna |

**Regola di visibilità:** all'artigiano non compaiono mai post da approvare, scartati o scaduti, e il piano compare solo dopo l'approvazione.

**Più di una campagna.** La pagina ne mostra una alla volta, con una riga di scelta in cima: si apre quella che chiede qualcosa all'artigiano (la bozza, poi una respinta o scaduta non ancora sostituita, poi quella in corso, poi quella in lavorazione). "Nuova campagna" sta nella stessa riga; in fondo, l'elenco delle campagne passate (ADR-104).

## 6. Fase 4 · Pubblicazione e monitoraggio (sistema)

| # | Passo | Cosa succede |
|---|---|---|
| 4.1 | Controllo periodico (ogni minuto) | Prende i post approvati con data raggiunta |
| 4.2 | Registra il tentativo | Prima di pubblicare, così un nuovo tentativo non crea doppioni |
| 4.3 | Pubblica | Sulla pagina social dell'artigiano, con tutte le foto del post |
| 4.4 | Esito | OK: si salva il riferimento del post. Errore temporaneo: riprova (max 3). Definitivo: "fallito"; l'operatore lo vede in Vedi campagna, dalla 2b riceve una notifica e dallo sprint 3 lo trova tra le cose da sistemare (ADR-77). Un post fallito si può **riprogrammare**: nuova data e ora dentro il periodo, contenuto invariato (ADR-97). Permesso scaduto o account scollegato dopo l'invio: la campagna si sospende, avvisi a operatore e artigiano |
| 4.5 | Monitoraggio | Metriche lette ogni giorno, dashboard, report settimanale |
| 4.6 | Fine | Quando ogni post è chiuso (pubblicato, fallito, annullato, scartato o scaduto) la campagna è **conclusa**; se c'è un post fallito aspetta la fine del periodo, per lasciare il tempo di riprogrammarlo (ADR-97) |

![Pubblicazione](architettura/diagrammi/07-pubblicazione.png)

## 7. Stati

**Campagna:** bozza → inviata → in generazione → in revisione → **attiva** (approvata) → conclusa · in generazione → **piano da rivedere** → in generazione (Prosegui) oppure respinta · in generazione → generazione fallita → inviata (Riprova) · in revisione → **respinta** · inviata → generazione fallita (ferma da 30 minuti, ADR-98) · inviata / in generazione / piano da rivedere / generazione fallita / in revisione → **scaduta** (scadenza morbida, ADR-95) · attiva ⇄ sospesa · attiva / sospesa → annullata. Respinta e scaduta non bloccano il periodo.

**Post:** da approvare (eventualmente "da rivedere") → approvato (con la campagna) → pubblicato o fallito · fallito → approvato (riprogrammato) · da approvare → scaduto (quando passa la sua data, o con la campagna) · da approvare → scartato (con la campagna respinta, o con il suo canale tolto) · approvato → annullato (campagna annullata, o post saltato alla riattivazione).

![Stati della campagna](architettura/diagrammi/03-stati-campagna.png)

![Stati del post e versioni](architettura/diagrammi/04-stati-post-versioni.png)

## 8. Regole di processo

Le regole R-01…R-39, con i loro numeri, stanno solo nel canale agenti: `docs/agenti/spec.md` §5 (ADR-72). I rimandi "(R-05)" di queste note portano lì. Quando una regola cambia si cambia lì, insieme al testo di queste note che la spiega.

---

## 9. Criteri di accettazione

Stanno solo nel canale agenti: `docs/agenti/spec.md` §6 (CA-01…CA-75, forma Dato / Quando / Allora). Si rigenerano da questo documento con un assorbimento.

---

## 10. Decisioni di prodotto

Le decisioni sul flusso, con motivazione e alternative scartate, stanno in [`ADR.md`](ADR.md), il registro unico (ADR-72). I rimandi "(D-39)" di queste note sono gli alias scritti nell'ultima colonna di quel file.

## 11. MVP, demo e roadmap

| MVP | Demo del pitch | Roadmap |
|---|---|---|
| Fasi 1–4 complete con Instagram e Facebook, solo foto | Fasi 1→3 reali con un vero modello AI, in locale; pubblicazione simulata; metriche finte ma realistiche; cambio di provider AI da configurazione | Approvazione dell'artigiano, anagrafica e accesso dal sito del consorzio, riuso delle foto di una campagna respinta, date strutturate per gli eventi, video, LinkedIn/TikTok/X, orari scelti dalle metriche, più consorzi, calendario drag & drop, app mobile |

## 12. Glossario

- **Campagna**: un periodo di post di un artigiano su uno o più canali, creato dalla pagina Campagna e deciso in blocco dall'operatore.
- **Gruppo**: da 1 a 20 foto con una descrizione comune; è di foto caricate oppure di immagini da creare. I post nascono dai gruppi.
- **Stella**: segno dell'artigiano su una foto "da usare per forza".
- **Piano editoriale**: ciò che l'AI decide prima di scrivere i testi: uscite, post per canale, formato, foto, giorni e orari.
- **Uscita**: un tema e un gruppo, con un post per ogni canale su cui esce.
- **Carosello**: post con più foto.
- **Capacità**: quanti post può dare il materiale senza riempitivi: il minore tra i post scelti e le foto idonee e diverse.
- **Archivio della bottega**: le foto idonee di un artigiano, legate al profilo: quelle delle sue campagne, usate o no, e quelle che carica dal profilo (§4.3).
- **Riempitivo**: post senza una foto nuova, che tiene il ritmo quando le foto non bastano: foto d'archivio già uscita, cartolina o immagine AI di riempimento.
- **Cartolina**: immagine composta da un modello, con il logo o il nome della bottega e una frase.
- **Scheda del canale**: limiti e stile di un canale, letti da prompt, controllo a regole e anteprime.
- **Piano da rivedere**: stato di una campagna il cui piano è debole; decide l'operatore prima dei testi.
- **Immagine AI**: immagine creata dall'AI per un gruppo di immagini da creare; è diversa dal ritocco, che parte sempre da una foto caricata.
- **Versione**: ogni stesura di un post (o di una foto); le precedenti restano.
- **Fotografia del profilo**: copia del profilo salvata nella campagna al momento dell'invio.
- **Ciclo**: un giro di intervento AI su un post (rigenerazione del testo o ritocco della foto), con un limite.
- **Blocco e avviso**: i due livelli del controllo a regole. Il blocco ferma l'approvazione; l'avviso si vede soltanto.
- **Da rivedere**: post il cui testo ha ancora un blocco del controllo a regole dopo 3 riscritture.
- **Nota interna**: appunto di un operatore su una campagna, letto solo dagli operatori; ha preso il posto dell'etichetta "rimandata".
- **Spunta "va bene"**: segno di un operatore su un post già controllato; non lo approva.
- **Idempotenza**: ripetere un'operazione non produce doppioni.

## Appendice A · Linea guida foto per l'artigiano

**Le tue foto fanno i tuoi post.** Il sistema scrive i testi, ma sono le foto a far fermare le persone. Bastano uno smartphone e 10 minuti.

- **Quante:** almeno **4 foto** per poter inviare; per una campagna piena circa **12 foto per ogni mese**. Non servono foto diverse per ogni canale: le stesse escono su tutti. Più sono varie, meno i post si somigliano.
- **Cosa fotografare (alterna):** prodotto finito su sfondo semplice · dettaglio da vicino · le tue mani al lavoro · la bottega · il prodotto in uso · tu, se ti va.
- **Come scattare:** luce naturale vicino a una finestra, senza flash · obiettivo pulito, telefono dritto · spazio attorno al soggetto (la foto verrà ritagliata) · niente filtri, scritte o cornici.
- **Per ogni gruppo di foto, due righe** (valgono per tutte le foto del gruppo): *cos'è* (nome, materiale, tecnica, tempo di lavorazione) e *cosa vuoi dire* (es. "fatto a mano in 3 giorni", "ordinabile su misura"). Se il gruppo riguarda un evento, metti la data. Segna con la **stella** le foto che vuoi vedere uscire di sicuro.
- **Da evitare:** foto prese da internet · persone riconoscibili senza consenso scritto (mai minori) · clienti, marchi di altri, foto buie o mosse.

| Prodotto | Consiglio |
|---|---|
| Legno, mobili | Prodotto ambientato + dettaglio delle venature |
| Ceramica, vetro | Luce di lato; sfondo neutro |
| Gioielli, metalli | Foto molto ravvicinate; un oggetto accanto per la scala |
| Tessile, pelle | Dettaglio del tessuto; indossato solo con consenso |
| Alimentare | Etichetta leggibile; niente promesse sulla salute |

## Storico versioni

| Versione | Data | Cosa cambia |
|---|---|---|
| 5.7 | 07/10/2026 | Vedi campagna approvata (ADR-111); diagrammi 01, 02, 03, 04, 06, 07 e 10 riallineati e canale agenti assorbito (ADR-112): il lavoro riparte da T1-08 |
| 5.6 | 07/10/2026 | Revisione ridefinita (ADR-89…101): modifica a mano, un post non si toglie ma si sistema, controllo a due livelli, spunta "va bene", intervento in corso, nota interna al posto di Rimanda, scadenza morbida, riattiva e annulla con lo stato "annullato", post fallito riprogrammabile, errori tecnici dell'AI con il loro tipo, cambio foto e spostamento dallo sprint 3, Vedi campagna sul modello a uscite. Chiuse le domande delle altre pagine (ADR-102…109) |
| 5.5 | 07/10/2026 | Presenza costante (ADR-81…88), costruita a tappe dalla cartolina dello sprint 1: la frequenza è un impegno pagato sul totale dei post a settimana; archivio della bottega; su ogni canale escono sempre i post scelti; riempitivi in ordine (immagini chieste dall'artigiano, foto d'archivio o cartoline, immagini AI con frasi), senza tetto e con un avviso; il carosello non serve a usare le foto in più. Nuova §4.3 |
| 5.4 | 06/10/2026 | Chiusi nove buchi delle verifiche di coerenza (ADR-73…80): soglie degli avvisi, data del gruppo, stella e doppioni, canale tolto visto dall'artigiano, notifiche agli operatori, lettura del calendario, sprint 1 senza Respingi, pulsante delle immagini da creare |
| 5.3 | 06/10/2026 | Documento ridotto (ADR-72): le regole R-xx stanno solo in `docs/agenti/spec.md` §5 e le decisioni D-xx in `ADR.md`; la data del gruppo è un'indicazione per l'AI, non una regola del controllo |
| 5.2 | 06/10/2026 | Canali dichiarati sulla campagna e frequenza per canale; gruppo come entità, con stella e data; minimi della campagna; piano editoriale, uscite e carosello; capacità e scelta delle foto; piano da rivedere; generazione a tappe; approvazione unica con Togli il canale; scheda per canale; avvisi prima dell'invio (ADR-57…71) |
| 5.1 | 06/10/2026 | Immagini create dall'AI: descrizione obbligatoria, prompt da profilo e campagna, ritocco e rigenerazione dell'operatore (ADR-52); dashboard operatore in otto pagine, con lo storico delle campagne in una pagina a parte (ADR-53, ADR-54); pagine statiche in `pagine/`, approvate tranne Vedi campagna (ADR-55) |
| 5.0 | 01/10/2026 | Reset: la scheda bottega si divide in due pagine, Profilo e Campagna (ADR-47); immagini create dall'AI su richiesta dell'artigiano (ADR-48); backend a moduli e lavoro in sei corsie (ADR-49, ADR-50), spiegati in note-architettura.md §3 |
| 4.7 | 30/09/2026 | Motivi del No e cicli, ritocco AI delle foto, niente modifica a mano, nessuna modifica in campagna attiva (ADR-40…44). Si riparte da zero nel repository del team (ADR-45); documentazione in due canali, appunti e agenti (ADR-46) |
| 4.6 | 28/09/2026 | Approvazione in blocco, respinta e scaduta, anticipo 3 giorni, anagrafica, dashboard operatore (ADR-30…39) |
| 4.5 | 26/09/2026 | Scheda bottega unica con Bentornato (ADR-15…29) |
| 4.1–4.4 | 25/09/2026 | Stack, login con sessione, LiteLLM, dashboard artigiano (ADR-01…14) |
