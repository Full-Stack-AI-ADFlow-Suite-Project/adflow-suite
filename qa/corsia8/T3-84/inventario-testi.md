# T3-84 · Inventario completo prima → dopo

Inventario iniziale preparato prima delle modifiche; questa tabella finale confronta ogni testo letterale o JSX effettivamente cambiato con il commit di partenza `299b582ed3178971b3a65db1e731acdbf97bc7c3`. Le sole differenze di formattazione e gli spazi JSX equivalenti di Prettier non sono conteggiati come riscritture. I frammenti dinamici sono riportati senza modificare le espressioni del codice. Le righe ripetute sono raggruppate con il loro conteggio.

Sono state passate in rassegna tutte le pagine e i componenti. I testi non elencati restano uguali: sono già chiari, fissi (§1.4), di codice congelato, dati di esempio o provengono da API (`PASSI`, `SCELTE`, `ETICHETTE`, errori backend). I titoli con aria-label omonimi non sono stati cambiati.

## docs/pagine/AdFlow-campagna-stati.html

| Prima | Dopo | Occorrenze |
|---|---|---:|
| 6 foto in 3 gruppi | 6 foto in 3 serie | 1 |
| Risposta per il consorzio (facoltativa) | Cosa vuoi rispondere al consorzio? (facoltativa) | 1 |

## docs/pagine/AdFlow-campagna.html

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Ogni volta che serve un nuovo periodo di pubblicazioni: durata, canali, descrizione e foto a gruppi (sezioni 10 e 11), poi il riepilogo con un unico invio all'operatore. Il profilo si compila nella pagina | Ogni volta che serve un nuovo periodo di pubblicazioni: periodo, social, cosa vuoi raccontare e foto da raccontare insieme (sezioni 10 e 11), poi il riepilogo con un unico invio all'operatore. Il profilo si compila nella pagina | 1 |
| La pagina Campagna si apre con questo riepilogo del profilo già salvato. Chi non ha ancora un profilo viene portato prima alla pagina Profilo bottega. | Ritrovi qui il riepilogo della pagina Profilo bottega. Controlla che sia aggiornato prima di preparare la campagna. | 1 |
| Solo se l'ultima campagna è stata respinta. | L’ultima campagna è stata respinta. | 1 |
| 10 · Durata e canali · Di che campagna si tratta | 10 · Durata e canali · Cosa vuoi far conoscere con questa campagna? | 1 |
| Nome della campagna * | Come vuoi chiamare la campagna? * | 1 |
| Inizio * | Quando vuoi iniziare? * | 1 |
| Fine * | Quando vuoi concludere? * | 1 |
| Canali di questa campagna * | Su quali social vuoi far uscire i post? * | 1 |
| Descrizione e commenti della campagna * | Cosa vuoi raccontare ai tuoi clienti in questo periodo? * | 1 |
| 11 · Foto della campagna · Le foto di questo periodo | 11 · Foto della campagna · Quali foto vuoi usare in questo periodo? | 1 |
| Le foto si caricano a gruppi: da 1 a 20 foto per gruppo, con una descrizione. Sono facoltative: senza foto la campagna esce tutta con immagini create dall'AI (ADR-114). | Riunisci da 1 a 20 foto che vuoi raccontare insieme. Puoi anche proseguire senza foto: per i post mancanti creiamo un’immagine con l’AI (ADR-114). | 1 |
| 3 gruppi · 6 foto in totale | 3 serie · 6 foto in totale | 1 |
| e diverse tra loro: le stesse escono su tutti i canali. Se sono meno, per i post che mancano creiamo un'immagine con l'AI: i post che hai scelto escono sempre tutti (ADR-81). Se sono di più, usiamo le migliori. Meglio se di almeno due tipi: pezzo finito, dettaglio, lavorazione, tu al lavoro, il pezzo in uso, un evento. Esempio: 6 caricate in 3 gruppi. | e diverse tra loro: le stesse escono su tutti i canali. Se sono meno, per i post che mancano creiamo un'immagine con l'AI: i post che hai scelto escono sempre tutti (ADR-81). Se sono di più, usiamo le migliori. Meglio se di almeno due tipi: pezzo finito, dettaglio, lavorazione, tu al lavoro, il pezzo in uso, un evento. Esempio: 6 foto in 3 serie. | 1 |
| Gruppo 1 · 2 foto | Serie di foto 1 · 2 foto | 1 |
| Rimuovi gruppo | Rimuovi queste foto | 3 |
| Descrizione o richieste per queste foto * | Cosa mostrano queste foto e cosa vuoi raccontare? * | 3 |
| Da usare verso il (facoltativa) | C’è un giorno in cui vuoi che escano? (facoltativo) | 3 |
| Solo se le foto riguardano una data precisa, dentro il periodo della campagna: un evento, una consegna, una festa. | Puoi indicare una data preferita nel periodo della campagna. Le date dei post le propone l’AI. | 1 |
| Gruppo 2 · 3 foto | Serie di foto 2 · 3 foto | 1 |
| Gruppo 3 · 1 foto | Serie di foto 3 · 1 foto | 1 |
| + Aggiungi un gruppo di foto | + Aggiungi una serie di foto | 1 |
| 12 · Riepilogo · Rivedi prima di inviare | 12 · Riepilogo · Hai controllato tutto prima di inviare? | 1 |
| 6 foto in 3 gruppi | 6 foto in 3 serie | 2 |
| Logistica | Quanti post usciranno? | 1 |
| ). Gli avvisi arrivano dal server (ADR-73, spec R-25). Blocchi, con il campo evidenziato: la dichiarazione non spuntata (spec R-41); un gruppo senza descrizione; un canale non più collegato ("Instagram non è collegato: contatta il consorzio"). Nessun minimo di foto. | ). Gli avvisi arrivano dal server (ADR-73, spec R-25). Blocchi, con il campo evidenziato: la dichiarazione non spuntata (spec R-41); una serie di foto senza un racconto; un canale non più collegato ("Instagram non è collegato: contatta il consorzio"). Nessun minimo di foto. | 1 |

## docs/pagine/AdFlow-operatore-campagna.html

| Prima | Dopo | Occorrenze |
|---|---|---:|
| &lt;div class="panel"&gt;&lt;p&gt;&lt;b&gt;Cicli AI finiti ( | &lt;div class="panel"&gt;&lt;p&gt;&lt;b&gt;Limite di rigenerazioni raggiunto ( | 1 |
| ).&lt;/b&gt; L'AI non può più riscrivere questo post: resta la modifica a mano.&lt;/p&gt; &lt;div class="row"&gt;&lt;button type="button" class="btn small primary" data-act="apri" data-pan="modifica" data-id=" | ).&lt;/b&gt; È disponibile la modifica a mano.&lt;/p&gt; &lt;div class="row"&gt;&lt;button type="button" class="btn small primary" data-act="apri" data-pan="modifica" data-id=" | 1 |
| . Nasce una versione con lo stesso testo: rileggilo. | . Il testo non cambia: va ricontrollato dopo la sostituzione. | 1 |
| nuova, dall’artigiano: guardala tu | Nuova foto dell’artigiano: da controllare | 1 |
| &lt;div class="panel"&gt; &lt;p&gt;&lt;b&gt;Il post non esce più e non torna indietro.&lt;/b&gt; La nota resta nelle decisioni della campagna; l'artigiano legge "non pubblicato".&lt;/p&gt; &lt;div&gt;&lt;label for="an- | &lt;div class="panel"&gt; &lt;p&gt;&lt;b&gt;Il post non sarà pubblicato. L’annullamento è definitivo.&lt;/b&gt; La nota resta nelle decisioni della campagna; l'artigiano legge "non pubblicato".&lt;/p&gt; &lt;div&gt;&lt;label for="an- | 1 |
| "&gt;Perché non deve uscire? *&lt;/label&gt;&lt;textarea id="an- | "&gt;Motivo dell’annullamento *&lt;/label&gt;&lt;textarea id="an- | 1 |
| &lt;div class="avviso quiet"&gt;Esce tra meno di 15 minuti: non si tocca più.&lt;/div&gt; | &lt;div class="avviso quiet"&gt;Pubblicazione tra meno di 15 minuti: modifiche non più disponibili.&lt;/div&gt; | 1 |
| &gt;Foto scattate male&lt;/label&gt; &lt;label class="choice"&gt;&lt;input type="radio" name="motivo" value="altro" | &gt;Foto insufficienti o di qualità non adatta&lt;/label&gt; &lt;label class="choice"&gt;&lt;input type="radio" name="motivo" value="altro" | 1 |
| &lt;div class="form"&gt;&lt;h3&gt;Chiedi all'artigiano&lt;/h3&gt; &lt;p class="hint"&gt;Per ciò che può dare solo l'artigiano: una foto da sostituire, fino a 3, o una conferma (un prezzo, una certificazione). La campagna resta in revisione: puoi approvare o respingere quando vuoi. Avvisa tu l'artigiano, a voce o con un messaggio: il sistema non manda email. Lui risponde dalla sua pagina Campagna.&lt;/p&gt; | &lt;div class="form"&gt;&lt;h3&gt;Chiedi all'artigiano&lt;/h3&gt; &lt;p class="hint"&gt;Per ciò che può dare solo l'artigiano: una foto da sostituire, fino a 3, o una conferma (un prezzo, una certificazione). La campagna resta in revisione. La richiesta non blocca l’approvazione né il rifiuto. Avvisa tu l'artigiano, a voce o con un messaggio: il sistema non manda email. Lui risponde dalla sua pagina Campagna.&lt;/p&gt; | 1 |
| post per canale in 14 giorni&lt;/dd&gt;&lt;/div&gt; &lt;/dl&gt;&lt;/div&gt; &lt;div class="card"&gt;&lt;div class="tab"&gt;Profilo bottega · fotografia del 03/11/2026&lt;/div&gt;&lt;h3&gt;Ciò che ha ricevuto l'AI&lt;/h3&gt; &lt;dl style="margin:0"&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Bottega&lt;/dt&gt;&lt;dd&gt;Falegnameria Bianchi · Mario Bianchi · Bra (CN)&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Tipo di prodotto&lt;/dt&gt;&lt;dd&gt;Legno e mobili&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Obiettivo&lt;/dt&gt;&lt;dd&gt;Farmi conoscere&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Clienti ideali&lt;/dt&gt;&lt;dd&gt;Coppie che stanno arredando casa, 30-50 anni, zona Cuneo e Torino.&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Tono · cortesia&lt;/dt&gt;&lt;dd&gt;Caldo e familiare · do sempre del tu&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Cose da non dire mai&lt;/dt&gt;&lt;dd&gt;Niente prezzi dei concorrenti, niente sconti non autorizzati dal consorzio.&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Orari&lt;/dt&gt;&lt;dd&gt;La sera e nel weekend&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Eventi&lt;/dt&gt;&lt;dd&gt;Porte aperte in bottega · 21 novembre 2026&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Dichiarazione&lt;/dt&gt;&lt;dd&gt;"Le foto mostrano prodotti della mia bottega; le persone riconoscibili hanno dato il consenso" · confermata il 03/11/2026 (R-41)&lt;/dd&gt;&lt;/div&gt; &lt;/dl&gt; &lt;p class="note"&gt;È il profilo com'era all'invio, non quello di oggi (R-11).&lt;/p&gt;&lt;/div&gt; &lt;div class="card"&gt;&lt;div class="tab"&gt;Storico&lt;/div&gt;&lt;h3&gt;Decisioni&lt;/h3&gt; | post per canale in 14 giorni&lt;/dd&gt;&lt;/div&gt; &lt;/dl&gt;&lt;/div&gt; &lt;div class="card"&gt;&lt;div class="tab"&gt;Profilo bottega al momento dell’invio del 03/11/2026&lt;/div&gt;&lt;h3&gt;Ciò che ha ricevuto l'AI&lt;/h3&gt; &lt;dl style="margin:0"&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Bottega&lt;/dt&gt;&lt;dd&gt;Falegnameria Bianchi · Mario Bianchi · Bra (CN)&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Tipo di prodotto&lt;/dt&gt;&lt;dd&gt;Legno e mobili&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Obiettivo&lt;/dt&gt;&lt;dd&gt;Farmi conoscere&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Clienti ideali&lt;/dt&gt;&lt;dd&gt;Coppie che stanno arredando casa, 30-50 anni, zona Cuneo e Torino.&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Tono · cortesia&lt;/dt&gt;&lt;dd&gt;Caldo e familiare · do sempre del tu&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Cose da non dire mai&lt;/dt&gt;&lt;dd&gt;Niente prezzi dei concorrenti, niente sconti non autorizzati dal consorzio.&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Orari&lt;/dt&gt;&lt;dd&gt;La sera e nel weekend&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Eventi&lt;/dt&gt;&lt;dd&gt;Porte aperte in bottega · 21 novembre 2026&lt;/dd&gt;&lt;/div&gt; &lt;div class="rev-line"&gt;&lt;dt&gt;Dichiarazione&lt;/dt&gt;&lt;dd&gt;"Le foto mostrano prodotti della mia bottega; le persone riconoscibili hanno dato il consenso" · confermata il 03/11/2026 (R-41)&lt;/dd&gt;&lt;/div&gt; &lt;/dl&gt; &lt;p class="note"&gt;È il profilo com'era all'invio, non quello di oggi (R-11).&lt;/p&gt;&lt;/div&gt; &lt;div class="card"&gt;&lt;div class="tab"&gt;Storico&lt;/div&gt;&lt;h3&gt;Decisioni&lt;/h3&gt; | 1 |

## docs/pagine/AdFlow-profilo-bottega.html

| Prima | Dopo | Occorrenze |
|---|---|---:|
| I dati anagrafici della bottega, per intestare correttamente profilo e campagne. | Presenta la tua bottega: useremo questi dati nel profilo e nelle campagne. | 1 |
| Nome della bottega o attività * | Come si chiama la tua bottega? * | 1 |
| Nome del referente * | Come ti chiami? * | 1 |
| Città / paese * | Dove si trova la tua bottega? * | 1 |
| Da quanti anni esiste l'attività | Da quanti anni è aperta la tua bottega? | 1 |
| Sito web o altro profilo online (opzionale) | Hai un sito web? | 1 |
| Il materiale grezzo con cui l'AI scriverà i testi: più è concreto, meno i post sembreranno generici. | Racconta il tuo lavoro con esempi concreti: aiuteranno l’AI a scrivere post che parlano di te. | 1 |
| In poche parole, cosa fai e cosa rende unico il tuo lavoro? | Qual è la tua storia? | 1 |
| Come è nata la tua attività? | Come è nata la tua bottega? | 1 |
| Valori che vuoi che si sentano sempre nei post | Cosa ti sta a cuore nel tuo lavoro? | 1 |
| Guida il tono dei testi, gli hashtag e le linee guida per le foto. | Racconta cosa realizzi e cosa ti sta a cuore: guiderà i testi, gli hashtag e le foto. | 1 |
| Tipo di prodotto principale * | Che cosa realizzi? * | 1 |
| Descrivi la tua gamma di prodotti | Quali prodotti e lavorazioni proponi? | 1 |
| Fascia di prezzo | In quale fascia di prezzo vendi? | 1 |
| Prodotti stagionali o legati a ricorrenze | Cosa realizzi per le stagioni e le ricorrenze? | 1 |
| Chi sono i tuoi clienti ideali? * | Chi vorresti raggiungere con i tuoi post? * | 1 |
| Obiettivo principale dei social * | Cosa vuoi ottenere sui social? * | 1 |
| Zona geografica di riferimento (opzionale) | Da dove arrivano i tuoi clienti? | 1 |
| Tono di voce (scegli 1 o 2) | Come parli di solito ai tuoi clienti? | 1 |
| Come ti rivolgi ai clienti | Dai del tu o del lei ai tuoi clienti? | 1 |
| Cose da non dire mai | Cosa vuoi evitare di dire nei post? | 1 |
| Canali attivi oggi | Quali social usi già? | 1 |
| Nome utente o link dei profili esistenti | Quali sono le tue pagine e i tuoi profili? | 1 |
| Cosa ha funzionato bene finora, se lo sai (opzionale) | Cosa funziona già sui tuoi social? | 1 |
| Foto nuove disponibili ogni mese, in media | Quante foto puoi preparare al mese? | 1 |
| Chi scatterà le foto | Chi scatta le tue foto? | 1 |
| Persone riconoscibili nelle foto (te compreso, dipendenti, clienti) | Nelle tue foto ci sono persone riconoscibili? | 1 |
| Le foto si caricano in ogni campagna, a gruppi. Se in una campagna le foto non bastano per i post a settimana che hai scelto, per quelli che mancano creiamo un'immagine con l'AI: ambienti, materiali, attrezzi e atmosfere, mai un prodotto che non è tuo. Se hai un logo, caricalo come una foto qualsiasi. | In ogni campagna puoi caricare le tue foto, raccolte in serie. Se in una campagna le foto non bastano per i post a settimana che hai scelto, per quelli che mancano creiamo un'immagine con l'AI: ambienti, materiali, attrezzi e atmosfere, mai un prodotto che non è tuo. Se hai un logo, caricalo come una foto qualsiasi. | 1 |
| Nome evento | Come si chiama l’evento 1? | 1 |
| Quando | Quando si svolge l’evento 1? | 1 |
| Tipo | Di che tipo è l’evento 1? | 1 |
| Periodi di chiusura ricorrenti | Quando chiude la tua bottega? | 1 |
| Canali su cui vuoi essere presente * | Su quali social vuoi pubblicare? * | 1 |
| Post a settimana, per ogni canale, che ti sembrano sostenibili da rivedere | Quanti post vuoi a settimana su ogni social? | 1 |
| Giorno o orario in cui i tuoi clienti sono più attivi (opzionale) | Quali sono i tuoi orari e le tue disponibilità? | 1 |

## frontend/src/pages/Accesso.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Errore inatteso. | Impossibile completare l’operazione. Riprova. | 1 |

## frontend/src/pages/Calendario.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere il calendario. | Impossibile caricare il calendario. Riprova. | 1 |

## frontend/src/pages/artigiano/Archivio.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere l'archivio foto. | Impossibile caricare l’archivio foto. Riprova. | 1 |

## frontend/src/pages/artigiano/Campagne.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere le campagne. | Impossibile caricare le campagne. Riprova. | 1 |

## frontend/src/pages/artigiano/Ingresso.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere il calendario. | Impossibile caricare il calendario. Riprova. | 1 |
| Non sono riuscita a leggere le campagne. | Impossibile caricare le campagne. Riprova. | 1 |

## frontend/src/pages/artigiano/campagna/Bentornato.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Il riepilogo del profilo già salvato. Chi non ha un profilo viene portato prima alla pagina Profilo bottega. | Ritrovi qui il riepilogo della pagina Profilo bottega. Controlla che sia aggiornato prima di preparare la campagna. | 1 |
| Solo se l'ultima campagna è stata respinta. | L’ultima campagna è stata respinta. | 1 |

## frontend/src/pages/artigiano/campagna/Bozza.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Errore inatteso. | Impossibile completare l’operazione. Riprova. | 1 |

## frontend/src/pages/artigiano/campagna/Passo10.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Il nome non può essere vuoto. | Dai un nome alla tua campagna. | 1 |
| L'inizio deve cadere almeno 3 giorni dopo oggi. | Scegli una data di inizio almeno 3 giorni dopo oggi. | 1 |
| La campagna dura almeno 7 giorni. | Scegli un periodo di almeno 7 giorni. | 1 |
| La campagna dura al massimo 3 mesi. | Scegli un periodo di massimo 3 mesi. | 1 |
| La descrizione non può essere vuota. | Racconta cosa vuoi far conoscere con questa campagna. | 1 |
| Di che campagna si tratta | Cosa vuoi far conoscere con questa campagna? | 1 |
| Nome della campagna | Come vuoi chiamare la campagna? | 1 |
| Inizio | Quando vuoi iniziare? | 1 |
| Fine | Quando vuoi concludere? | 1 |
| Canali di questa campagna * | Su quali social vuoi far uscire i post? * | 1 |
| La pagina propone i canali del profilo; si possono scegliere solo quelli collegati. La frequenza del profilo vale per ogni canale. | Ritrovi i social scelti nel profilo: puoi usare quelli collegati. Il numero di post a settimana vale per ciascun social. | 1 |
| Descrizione e commenti della campagna | Cosa vuoi raccontare ai tuoi clienti in questo periodo? | 1 |

## frontend/src/pages/artigiano/campagna/Passo11.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Errore inatteso. | Impossibile completare l’operazione. Riprova. | 2 |
| Le foto di questo periodo | Quali foto vuoi usare in questo periodo? | 1 |
| Le foto si caricano a gruppi: da 1 a 20 per gruppo, con una descrizione. Sono facoltative: per i post che le foto non coprono creiamo un'immagine con l'AI, e i post che hai scelto escono sempre tutti. Se le foto sono di più, usiamo le migliori. JPG, PNG o WEBP, fino a | Riunisci da 1 a 20 foto che vuoi raccontare insieme. Puoi anche proseguire senza foto: per i post mancanti creiamo un’immagine con l'AI, e i post che hai scelto escono sempre tutti. Se le foto sono di più, usiamo le migliori. JPG, PNG o WEBP, fino a | 1 |
| + Aggiungi un gruppo di foto | + Aggiungi una serie di foto | 1 |
| gruppi | serie | 1 |
| Gruppo | Serie di foto | 1 |
| Rimuovi gruppo | Rimuovi queste foto | 1 |
| Descrizione o richieste per queste foto | Cosa mostrano queste foto e cosa vuoi raccontare? | 1 |
| La descrizione manca. | Racconta cosa mostrano queste foto. | 1 |
| Da usare verso il (facoltativa) | C’è un giorno in cui vuoi che escano? (facoltativo) | 1 |
| Solo se le foto riguardano una data precisa, dentro il periodo della campagna. | Puoi indicare una data preferita nel periodo della campagna. Le date dei post le propone l’AI. | 1 |

## frontend/src/pages/artigiano/campagna/Passo12.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Il gruppo | Racconta cosa mostrano le foto della serie | 1 |
| non ha la descrizione. | . | 1 |
| Errore inatteso. | Impossibile completare l’operazione. Riprova. | 1 |
| Rivedi prima di inviare | Hai controllato tutto prima di inviare? | 1 |
| Logistica | Quanti post usciranno? | 1 |
| gruppi | serie | 1 |
| Da sistemare prima dell'invio | Cosa manca per inviare la campagna? | 1 |

## frontend/src/pages/artigiano/campagna/viste/RichiestaConsorzio.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| La foto deve essere JPG, PNG o WEBP. | Scegli una foto JPG, PNG o WEBP. | 1 |
| La foto supera 10 MB. | Scegli una foto che non superi 10 MB. | 1 |
| Non sono riuscito a caricare. | Impossibile caricare la foto. Riprova. | 1 |
| Non sono riuscito a inviare. | Impossibile inviare la risposta. Riprova. | 1 |
| Risposta per il consorzio | Cosa vuoi rispondere al consorzio? | 1 |

## frontend/src/pages/artigiano/campagna/viste/VistaStato.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| gruppi | serie | 1 |

## frontend/src/pages/artigiano/profilo/Profilo.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| I dati anagrafici della bottega, per intestare correttamente profilo e campagne. | Presenta la tua bottega: useremo questi dati nel profilo e nelle campagne. | 1 |
| Il materiale grezzo con cui l'AI scriverà i testi: più è concreto, meno i post sembreranno generici. | Racconta il tuo lavoro con esempi concreti: aiuteranno l’AI a scrivere post che parlano di te. | 1 |
| Guida il tono dei testi, gli hashtag e le linee guida per le foto. | Racconta cosa realizzi e cosa ti sta a cuore: guiderà i testi, gli hashtag e le foto. | 1 |
| Per chi lavori e cosa vuoi ottenere attraverso i canali social. | Racconta a chi ti rivolgi e cosa vuoi ottenere sui social: ci aiuta a parlare ai clienti giusti. | 1 |
| Come devono suonare i post e come ti rivolgi ai clienti. | Scegli come parlare ai tuoi clienti: i post seguiranno la voce della tua bottega. | 1 |
| Preferenze per le campagne, post a settimana e social già utilizzati. | Scegli dove pubblicare e quanti post preparare: queste preferenze guideranno le campagne. | 1 |
| Le foto reali alimentano ogni post: quanti scatti puoi fornire e chi fotografa. | Dicci quante foto puoi preparare e chi le scatta: ci aiuta a organizzare i post. | 1 |
| Date da tenere a mente, periodi di chiusura e orari di apertura. | Segnala fiere, ricorrenze e chiusure: ci aiuta a proporre le date per i post. | 1 |
| Non riesco a leggere il profilo. Riprova. | Impossibile caricare il profilo. Riprova. | 2 |
| Nome della bottega | Come si chiama la tua bottega? | 1 |
| Referente | Come ti chiami? | 1 |
| Città | Dove si trova la tua bottega? | 1 |
| Anni di attività | Da quanti anni è aperta la tua bottega? | 1 |
| Sito web | Hai un sito web? | 1 |
| Racconta la tua storia | Qual è la tua storia? | 1 |
| Come è nata la bottega | Come è nata la tua bottega? | 1 |
| Tipo di prodotto | Che cosa realizzi? | 1 |
| Fascia di prezzo | In quale fascia di prezzo vendi? | 1 |
| Prodotti e lavorazioni | Quali prodotti e lavorazioni proponi? | 1 |
| Valori della bottega | Cosa ti sta a cuore nel tuo lavoro? | 1 |
| Stagionalità | Cosa realizzi per le stagioni e le ricorrenze? | 1 |
| Clienti ideali | Chi vorresti raggiungere con i tuoi post? | 1 |
| Obiettivo | Cosa vuoi ottenere sui social? | 1 |
| Zona dei tuoi clienti | Da dove arrivano i tuoi clienti? | 1 |
| Tono della comunicazione | Come parli di solito ai tuoi clienti? | 1 |
| Come rivolgersi ai clienti | Dai del tu o del lei ai tuoi clienti? | 1 |
| Cose da non dire | Cosa vuoi evitare di dire nei post? | 1 |
| Canali preferiti | Su quali social vuoi pubblicare? | 1 |
| Post a settimana per ogni canale | Quanti post vuoi a settimana su ogni social? | 1 |
| Social già usati | Quali social usi già? | 1 |
| Pagine e profili social | Quali sono le tue pagine e i tuoi profili? | 1 |
| Cosa funziona già sui social | Cosa funziona già sui tuoi social? | 1 |
| Nome evento | Come si chiama l’evento | 1 |
|  | ? | 3 |
| Quando si svolge l'evento | Quando si svolge l’evento | 1 |
| Tipo evento | Di che tipo è l’evento | 1 |
| Periodi di chiusura | Quando chiude la tua bottega? | 1 |
| Orari e disponibilità | Quali sono i tuoi orari e le tue disponibilità? | 1 |

## frontend/src/pages/artigiano/profilo/passo7/Passo7.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Quante fotografie puoi fornire al mese? | Quante foto puoi preparare al mese? | 1 |
| Chi scatta le fotografie? | Chi scatta le tue foto? | 1 |
| Persone riconoscibili nelle foto | Nelle tue foto ci sono persone riconoscibili? | 1 |
| Le foto si caricano in ogni campagna, a gruppi. Se in una campagna le foto non bastano per i post a settimana che hai scelto, per quelli che mancano creiamo un'immagine con l'AI: ambienti, materiali, attrezzi e atmosfere, mai un prodotto che non è tuo. Se hai un logo, caricalo come una foto qualsiasi. | In ogni campagna puoi caricare le tue foto, raccolte in serie. Se in una campagna le foto non bastano per i post a settimana che hai scelto, per quelli che mancano creiamo un'immagine con l'AI: ambienti, materiali, attrezzi e atmosfere, mai un prodotto che non è tuo. Se hai un logo, caricalo come una foto qualsiasi. | 1 |

## frontend/src/pages/operatore/ArchivioArtigiano.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere l'archivio foto. | Impossibile caricare l’archivio foto. Riprova. | 1 |

## frontend/src/pages/operatore/Artigiani.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere gli artigiani. | Impossibile caricare l’elenco degli artigiani. Riprova. | 1 |

## frontend/src/pages/operatore/Artigiano.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere l'artigiano. | Impossibile caricare la scheda dell’artigiano. Riprova. | 1 |

## frontend/src/pages/operatore/CampagneArtigiano.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere le campagne. | Impossibile caricare le campagne. Riprova. | 1 |

## frontend/src/pages/operatore/DaApprovare.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere le campagne. | Impossibile caricare le campagne. Riprova. | 1 |

## frontend/src/pages/operatore/VediCampagna.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere la campagna. | Impossibile caricare la campagna. Riprova. | 1 |

## frontend/src/pages/operatore/campagna/Materiali.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Profilo bottega · fotografia | Profilo bottega al momento dell’invio | 1 |
| Nessuna fotografia: la campagna è ancora una bozza. | Profilo all’invio non disponibile: la campagna è ancora una bozza. | 1 |

## frontend/src/pages/operatore/campagna/PostCard.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Il post è chiuso: non torna indietro. | Post chiuso: non sono disponibili altre modifiche. | 1 |

## frontend/src/pages/operatore/vedi-campagna/decisioni/ChiediArtigiano.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| La campagna resta in revisione: puoi approvare o respingere quando vuoi. Avvisa tu l'artigiano: il sistema non manda email. | La campagna resta in revisione. La richiesta non blocca l’approvazione né il rifiuto. Avvisa tu l'artigiano: il sistema non manda email. | 1 |

## frontend/src/pages/operatore/vedi-campagna/decisioni/Respingi.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Foto: quelle buone sono poche o scattate male | Foto insufficienti o di qualità non adatta | 1 |
| Cosa deve rifare o correggere. | Indicare cosa rifare o correggere. | 1 |

## frontend/src/pages/operatore/vedi-campagna/decisioni/RiprogrammaPost.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non è stato pubblicato: puoi darle una nuova data. | Pubblicazione fallita. È possibile assegnare una nuova data. | 1 |

## frontend/src/pages/operatore/vedi-campagna/post/AnnullaPost.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Il post non esce più e non torna indietro. | Il post non sarà pubblicato. L’annullamento è definitivo. | 1 |
| Perché non deve uscire? | Motivo dell’annullamento | 1 |

## frontend/src/pages/operatore/vedi-campagna/post/AzioniPost.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Le 3 rigenerazioni sono finite: resta la modifica a mano. | Limite di 3 rigenerazioni raggiunto. È disponibile la modifica a mano. | 1 |
| Esce tra meno di 15 minuti: non si tocca più. | Pubblicazione tra meno di 15 minuti: modifiche non più disponibili. | 1 |

## frontend/src/pages/operatore/vedi-campagna/post/CambiaFoto.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a leggere le foto. | Impossibile caricare le foto. Riprova. | 1 |
| Non sono riuscita a cambiare. | Impossibile cambiare la foto. Riprova. | 1 |
| Il testo resta quello di adesso: dopo il cambio rileggilo. Le foto già usate da un altro post dello stesso canale non compaiono. | Il testo non cambia: va ricontrollato dopo la sostituzione. Sono escluse le foto già usate da un altro post dello stesso canale. | 1 |
| Nuova, dall'artigiano: guardala tu | Nuova foto dell’artigiano: da controllare | 1 |

## frontend/src/pages/operatore/vedi-campagna/post/ModificaMano.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a salvare. | Impossibile salvare la modifica. Riprova. | 1 |

## frontend/src/pages/operatore/vedi-campagna/post/Rigenera.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Non sono riuscita a rigenerare. | Impossibile rigenerare il testo. Riprova. | 1 |

## frontend/src/pages/operatore/vedi-campagna/post/Sposta.tsx

| Prima | Dopo | Occorrenze |
|---|---|---:|
| Dentro il periodo della campagna, almeno 15 minuti da adesso. | La nuova data deve rientrare nella campagna ed essere tra almeno 15 minuti. | 1 |

## Pagine verificate senza riscritture ulteriori

Accesso (etichette già chiare); Nuovo artigiano (istruzioni già concrete); liste e schede artigiani, campagne, archivio e calendario (nomi e azioni già chiari); anteprima, piano e storico delle versioni (etichette adeguate); navigazione e sezioni fisse. In alcune di queste pagine è stato uniformato soltanto il messaggio locale di errore, elencato sopra.

Le statiche Roadmap e le prove di stile non sono state riscritte. Il loro aggiornamento non appartiene alla revisione dei testi dell’MVP.
