# Lavori aperti

Tutto ciò che è ancora da fare, decidere o verificare. Quando un punto si chiude, il risultato entra in `ADR.md` (se è una decisione) o nelle note, si chiede un assorbimento (vedi `LEGGIMI.md`) e il punto si toglie da qui.

## 1. Analisi (senza codice)

| ID | Task | Serve prima di | Assegnato a | Fatto quando | Stato |
|---|---|---|---|---|---|
| A-01 | **AI e immagini, prompt**: che cosa fa il ritocco (luce, colori, ritaglio, sfondo?), con quali modelli e costi; prompt di analisi dei gruppi, del **piano editoriale** (da social media manager: numero dei post, carosello, sfasamento, orari), di generazione dei post per canale, di rigenerazione "da zero" e "da proposta"; formato della risposta dell'AI | in parallelo allo sprint 1 (il piano serve a T1-31); pronto per il 2b (prompt di rigenerazione) e il 3 (ritocco) | | note-flusso.md §4 (2.1, 2.2, 2.4) aggiornato, nuova ADR, prompt di esempio negli appunti | ☐ |
| A-02 | **Campi del profilo**: confermare con un artigiano o un operatore reale quali campi dei passi 1–9 servono davvero Proposta della consulenza del 03/10/2026, non decisa: obbligatori solo nome, città, tipo di prodotto, pubblico ideale e obiettivo; il resto facoltativo. | sprint 2a | | elenco confermato in note-flusso.md §3; ADR se cambia qualcosa | ☐ |
| A-03 | **Libreria calendario** per Vedi campagna e dashboard artigiano | sprint 3 | | scelta con motivazione in `ADR.md` | ☐ |
| A-05 | **Immagini create dall'AI** (ADR-61). Definito il 06/10: un gruppo a sé, con la descrizione e il numero di immagini volute; l'AI ne fa un prompt partendo da profilo e campagna e crea, dopo il piano, solo le immagini che servono; l'operatore le ritocca o le rigenera con un prompt; stanno sempre accanto alle foto caricate. Piano in due fasi: ① creazione dentro la generazione, dopo T1-34; ② ritocca e rigenera con un prompt, dopo il ritocco foto dello sprint 3, con lo stesso contatore dei cicli. Resta: i cicli di ritocco e rigenerazione, se il post deve dire che l'immagine è creata dall'AI, modello e costi, la misura (molti modelli escono a 1024 px, sotto i 1080 di R-13: ingrandire o esentare?), lo sprint Proposta della consulenza del 03/10/2026, non decisa: etichetta permanente "Generato con AI" nell'interfaccia e in sovrimpressione sull'immagine, per le regole di Meta. La stessa consulenza proponeva un'immagine per ogni post e l'invio senza foto: non accolti (ADR-60, ADR-61). Dal 07/10 le immagini AI occupano i posti dei riempitivi (ADR-84): quelle del gruppo di immagini da creare, dove decide l'artigiano che cosa si vede, sono le prime che il piano usa; senza quel gruppo sono frasi e riflessioni ricavate dal profilo, senza prodotti, e vengono per ultime. Etichetta e regole di Meta valgono in tutti e due i casi. | prima di costruire la generazione delle immagini; sprint da decidere | | note-flusso.md §3 (1.4b) e §4 (2.5) aggiornati, nuova ADR se serve, task in `docs/agenti/tasks.md` | ☐ |
| A-06 | **Scheda per canale: i numeri** (ADR-69, R-21). Oggi sono di prova: 500 caratteri e 3 hashtag su Facebook, 600 e 5 su Instagram, 10 foto per post. Da confermare: i limiti, le proporzioni e il ritaglio per canale (una sola funzione per anteprima e pubblicazione), quante foto accetta un carosello pubblicato da programma, l'invito all'azione per canale. Dal 07/10 servono anche i limiti veri delle piattaforme (lunghezza massima del testo, numero massimo di hashtag), che per il controllo sono blocchi e non avvisi (ADR-91), e le proporzioni che un canale accetta senza ritaglio, comprese quelle di un carosello (ADR-100). I limiti della piattaforma oggi sono di prova: Facebook 5000 caratteri e 30 hashtag, Instagram 2200 e 30 | T1-33 parte con i numeri di prova; conferma prima della prova con Meta | | note-flusso.md §4.2 e R-21 con i numeri definitivi | ☐ |
| A-08 | **Presenza costante: archivio e riempitivi** (ADR-81…88, note-flusso.md §4.3). Deciso il 07/10: su ogni canale escono sempre i post scelti nel profilo; quelli che le foto nuove non coprono sono riempitivi, senza tetto, in quest'ordine: immagini chieste dall'artigiano, foto d'archivio o cartoline, immagini AI con frasi e riflessioni; più di un riempitivo ogni due foto nuove fa scattare un avviso; una foto già uscita torna sullo stesso canale dopo 90 giorni; le foto entrano in archivio a campagna chiusa, e quelle in più vanno lì, non nei caroselli; le tabelle nascono pronte con T1-08. Deciso anche come si costruisce (ADR-88): cartoline nello sprint 1, archivio e logo nella 2a, immagini AI con A-05; su un canale con riempitivi niente caroselli; il piano debole resta com'è. Lo sprint 1 è chiuso: non resta nulla da decidere. Resta per la 2a, quando entra l'archivio: quando il piano sceglie una foto d'archivio già uscita e quando una cartolina; se la cartolina ha modelli diversi e una frase sua, oltre al tema dell'uscita; che cosa riceve l'AI per scrivere il testo di una foto già uscita; il minimo di 4 foto caricate per chi ha già un archivio; le foto buone di una campagna respinta, che l'artigiano oggi ricarica e che in archivio sarebbero doppie; la stima per canale al passo 12, che chiede di sapere dove ogni foto è già uscita. Proposte del 07/10, non decise: una cartolina quando c'è qualcosa da annunciare (un evento, una chiusura, un augurio), una foto d'archivio negli altri casi; i testi già usati con quella foto arrivano all'AI come "cosa non rifare" | prima dei task della 2a | | i punti rimasti decisi, note-flusso.md §4.3 e R-27 aggiornati con l'assorbimento, task della 2a in `docs/agenti/tasks.md` | ☐ |

## 2. Domande aperte sul prodotto

- Quali campi del profilo servono davvero all'AI e quali solo all'operatore: da confermare con un artigiano reale prima di costruire la pagina Profilo definitiva (A-02).
- **Ritocco AI**: che cosa fa sulle immagini e con quali istruzioni; istruzioni per le rigenerazioni del testo (A-01).
- **Immagini create dall'AI**: da che cosa parte l'AI, quante ne crea e come interviene l'operatore sono definiti (ADR-61); il resto è da decidere (A-05). In particolare: un'immagine AI di un prodotto artigianale può mostrare un oggetto che la bottega non fa davvero; chi controlla, e che cosa si dice a chi guarda il post?
- **Carosello e cicli**: i 3 ritocchi per post valgono per il post intero o per ogni foto del carosello? Si decide con il ritocco (sprint 3).
- **Sfasamento e orari**: li decide l'AI nel piano, con gli orari del profilo come indicazione (ADR-62). Quando arrivano le metriche (sprint 4) gli orari si possono prendere dalle statistiche della pagina.
- **Tipi di contenuto** (pezzo finito, dettaglio, lavorazione, persona, pezzo ambientato, evento): oggi sono un consiglio all'artigiano e una voce dell'analisi dell'AI; decidere se l'artigiano li sceglie sul gruppo.
- Numeri da tarare: durata minima (7 giorni) e massima (3 mesi), conversione della frequenza, 1080 px, anticipo di 3 giorni, promemoria 48 ore, cicli 3 + 3, 12 foto al mese, minimo di 4 foto caricate, 20 foto per gruppo, soglia del piano debole (metà dei post chiesti), numeri della scheda per canale (A-06), la soglia dell'avviso sui riempitivi (uno ogni due foto nuove), la misura della cartolina (1080 px di lato) e i 90 giorni prima che una foto d'archivio torni sullo stesso canale (A-08).
- **Prezzo** (ADR-81): si paga per i post a settimana, sul totale dei canali. Da decidere: chi paga, l'artigiano o il consorzio; importo e fatturazione; che cosa succede al prezzo quando escono meno post di quelli scelti (post fallito e non riprogrammato, canale tolto, post scaduti perché la campagna è stata approvata dopo l'inizio: ADR-95, ADR-97); come l'artigiano cambia frequenza, e se la frequenza resta un campo del profilo o passa all'anagrafica gestita dall'operatore (tocca A-02).
- **Tra una campagna e l'altra** oggi non esce niente: la presenza costante chiede almeno un promemoria all'artigiano prima che la campagna finisca. Da decidere.
- Anagrafica e accesso dal sito del consorzio: se si fa, cambia il login (ADR-05).
- Accordo di delega consorzio–artigiano per pubblicare sulle sue pagine (da far verificare a un professionista).
- Layout delle metriche nella dashboard artigiano (sprint 4).

## 2b. Struttura a moduli e corsie (ADR-49, ADR-50)

- **Firme dei contratti**: quelle nuove o cambiate il 06/10 (`docs/agenti/plan.md` §6, segnate T1-09) sono la prima stesura; si approvano insieme in T1-09, poi cambiano solo con un task della corsia 0.
- **Revisione di gruppo delle corsie 1–5**: fissare il momento (ogni giorno? a fine task?).
- **Corsia 1 leggera nello sprint 1** (il profilo arriva dal seed): può dare una mano alla corsia 5 o tenere la penna nei task comuni.
- **Brief dei task più delicati** da scrivere prima di partire: T1-08 e T1-09 riallineamento, T1-22 API bozza, T1-24 invio, T1-34 generazione, T1-43 pubblicazione, T1-53 con la pagina statica di Vedi campagna (`pagine/AdFlow-operatore-campagna.html`).

## 2c. Buchi delle verifiche di coerenza ancora aperti

Punti in cui i documenti promettono qualcosa che nessun task, endpoint o criterio realizza. Le verifiche del 01/10 e del 06/10/2026 ne hanno trovati undici: nove sono chiusi (B-02, B-03, B-04, B-06…B-11: ADR-73…80). B-01, riprogrammare un post fallito, è chiuso con ADR-97. Resta questo, che chiede una decisione più larga.

| ID | Buco | Dove si vede | Che cosa manca | Serve prima di |
|---|---|---|---|---|
| B-05 | **Consenso delle persone nelle foto** | Appendice A di note-flusso.md; nel profilo c'è solo la politica generale (`foto_policy.persone`): con "mai" l'AI lascia fuori le foto con persone riconoscibili (note-flusso.md §4.1) | Decidere se serve un campo per la singola foto o per il gruppo Proposta della consulenza del 03/10/2026, non decisa: una casella obbligatoria su ogni gruppo, "Le foto includono persone? Confermo di avere il consenso". | sprint 2a |

## 2d. Scelte della corsia 0 ancora da chiudere (PR T1-01…T1-06)

Scelte prese nelle PR della corsia 0 con un "per ora": il codice funziona così, ma la forma definitiva è una decisione di tutto il team. Ognuna si chiude con un task della corsia 0.

| ID | Scelta | Com'è adesso e perché | Che cosa resta da decidere | Quando |
|---|---|---|---|---|
| C-02 | **`accoda()` fuori dalla transazione** | Il job si scrive subito: se la richiesta poi fallisce resta in coda, e il worker può prenderlo prima del `commit`. Per ora `accoda()` si chiama per ultima e il job controlla lo stato quando parte (per `genera_campagna` ci sono le 3 esecuzioni a 30 secondi) | Se accodare dentro la stessa transazione con `accoda(db, nome, …)`: cambia la firma approvata in T1-02 | da fissare |
| C-03 | **Doppi nomi dei job** | In `core/coda.py` ogni nome esiste due volte (`GENERA_CAMPAGNA` e `JOB_GENERA_CAMPAGNA`) | Tenere una sola forma | da fissare |
| C-04 | **Seed non interattivo** | Il seed chiede la password a terminale, come `crea-utente`: niente password nel codice, negli argomenti o in `.env` | Una variabile per lanciarlo senza terminale | quando servono E2E o demo |
| C-05 | **Seed senza `crea_utente()`** | Il seed scrive gli utenti direttamente, perché `crea_utente()` è uno stub fino a T1-13; la sua docstring dice già "e dal seed" | Far passare il seed dal service | quando T1-13 è su `main` |
| C-06 | **Forma di `profilo_bottega.orari`** | È un JSON senza forma fissata; il seed lo lascia vuoto | La forma del campo: ora lo legge il piano editoriale come indicazione | prima di T1-31 |
| C-07 | **Codice della corsia 0 da riallineare** alle decisioni del 06/10 e del 07/10 (ADR-57…70, 81…88, 89…112) | Tabelle, stati e contratti su `main` sono quelli di prima: una foto per versione di post, gruppo come etichetta, canali copiati dal profilo, `approva_post()` tutto o niente, etichetta "rimandata", nessun autore sulle versioni | I task T1-08 e T1-09 di `docs/agenti/tasks.md`, che ora comprendono anche le regole di revisione del 07/10; fino ad allora le corsie 1–5 non partono sui pezzi toccati | subito: è il punto da cui riparte il lavoro |

## 3. Rischi da tenere d'occhio

1. **Testi AI ripetitivi** → prompt per tipo di prodotto, versioni rifiutate come contesto, validatore. Con i riempitivi (ADR-82) il rischio cresce: la stessa foto torna con un testo nuovo.
2. **Collo di bottiglia dell'operatore**: con la frequenza per canale i post raddoppiano (20 artigiani × 24 post = 480 post al mese su due canali) → approvazione in blocco, uscite con le varianti dei canali affiancate, anticipo di 3 giorni, modifica a mano, avvisi che non bloccano, spunta "va bene" (ADR-89, 91, 92); misurare nella demo il tempo di revisione per campagna.
3. **Costo delle chiamate AI** (analisi, piano, ritocco foto, creazione di immagini, rigenerazioni) → ritocco e creazione solo sulle foto scelte dal piano, generazione a tappe che non rifà ciò che è salvato, cicli 3 + 3, stima dei costi, confronto tra provider.
4. **Troppo lavoro per 6 settimane** → la demo copre le fasi 1→3 e simula la pubblicazione; se il tempo stringe si tagliano i campi facoltativi del profilo, mai gli obbligatori.
5. **Multi-provider che si allarga** → nell'MVP due implementazioni: un provider reale e uno finto.
6. **"Funziona sul mio PC"** → versioni fissate (Python, Node, PostgreSQL), `.env.example`, istruzioni di avvio nel README; una sola persona non deve essere l'unica a saper avviare il progetto.
7. **Lavoro in parallelo di più persone** → task piccoli con dipendenze esplicite, un branch per task, sei corsie con cartelle di proprietà (ADR-49, ADR-50); tabelle e migrazioni solo nella corsia comune (vedi `docs/agenti/tasks.md`).
8. **Confini tra i moduli che si sfaldano** (import in avanti, `models` di un altro modulo, stato cambiato fuori dal proprietario) → regole di note-architettura.md §3.5, test dei confini, revisione delle PR.
9. **La fase comune si allunga** (sei task fatti in cinque, prima che parta il lavoro in parallelo) → ordine fisso T1-01…06, una persona scrive e le altre seguono, niente discussioni fuori dal task in corso.
10. **Un piano scritto dall'AI è meno prevedibile di una formula** → controllo automatico del piano, limiti di capacità verificabili, provider finto con un piano sempre uguale nei test, piano debole fermato dall'operatore.

## 4. Punti tecnici da verificare

- LiteLLM: supporto delle immagini per i modelli OpenAI scelti; formato dei nomi dei modelli.
- Modelli OpenAI per visione, testo e **ritocco immagini**, con costi (A-01); modello per la **creazione di immagini** e misura delle immagini che produce (A-05).
- Regole di Meta sulle immagini create dall'AI (etichetta obbligatoria?) (A-05).
- Meta: quante foto accetta un carosello pubblicato da programma su Instagram e su Facebook; proporzioni accettate (A-06).
- Modello locale: solo se serve davvero; l'hardware deve reggere la visione.
- Catcher email per lo sviluppo (proposta: Mailpit).
- Libreria per la vista calendario (sprint 3, A-03).
- Server proprio: dominio e certificato HTTPS per l'OAuth dei social.
- Struttura a moduli (ADR-49): il test dei confini basta scritto a mano o serve una libreria (es. import-linter)? Verificati nello sprint 1: Procrastinate accoda un job per nome senza importare il modulo che lo definisce (T1-05, test sulla coda vera); Alembic vede tutte le tabelle tramite `app/tabelle.py` (T1-03, `alembic check` senza differenze).
