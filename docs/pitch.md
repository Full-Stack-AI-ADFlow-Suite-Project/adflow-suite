# AdFlow Suite · Scaletta e Slide del Pitch (10 minuti)

**Evento**: Presentazione finale MVP · 6 novembre 2026
**Team**: Gianluca, Silvia, Giovanni (coordinamento), Nilton, Angelo
**Durata massima**: 10 minuti (9 min 15 s nominali + 45 s di margine)
**Slide interattive**: [`docs/pagine/AdFlow-pitch.html`](pagine/AdFlow-pitch.html)
**Anteprima Metriche**: [`docs/pagine/AdFlow-operatore-metriche.html`](pagine/AdFlow-operatore-metriche.html)
**Fonti**: [`docs/proposta-tecnica.md`](proposta-tecnica.md) (v1.0), [`docs/ROADMAP.md`](ROADMAP.md), [`docs/agenti/converge.md`](agenti/converge.md) §4

---

## 1. Scaletta cronometrata dei 10 minuti

| Minuto | Durata | Slide / Schermo | Relatore | Contenuto chiave |
|---|---|---|---|---|
| `00:00 – 00:50` | 50 s | **Slide 1–2**: Il problema delle botteghe e la promessa di AdFlow | **Silvia** | L'artigiano sa raccontare il proprio mestiere a voce, ma non ha tempo né metodo per pubblicare con costanza; il consorzio non può scrivere a mano per 50 botteghe. AdFlow trasforma il profilo della bottega e poche foto in un calendario editoriale completo, rivisto dall'operatore e pubblicato in automatico. |
| `00:50 – 01:45` | 55 s | **Slide 3**: Come funziona (Artigiano → AI → Operatore → Social) | **Gianluca** | Flusso in 4 passi: 1) profilo in 9 passi compilato una volta e confermato al rientro; 2) bozza con foto nuove o dall'Archivio foto e dichiarazione legale; 3) generazione a 4 tappe con immagini AI dove mancano foto; 4) revisione in Vedi campagna e uscita automatica su Facebook e Instagram. |
| `01:45 – 05:30` | 3 min 45 s | **Slide 4 + Demo dal vivo** (`converge.md` §4) | **Giovanni** (voce) + **Angelo** (alla tastiera) | **Atto 1 – Artigiano (1 min 10 s)**: accesso di *Mosaici d'Arte* (`mosaici@esempio.it`), conferma Bentornato sul profilo, apertura bozza *Collezione d'autunno*, avviso che i post scoperti avranno un'immagine AI, spunta della dichiarazione e invio.<br>**Atto 2 – Generazione e Revisione Operatore (1 min 35 s)**: barra di avanzamento a 4 tappe; apertura in *Vedi campagna*; controllo delle foto valutate dall'AI (punteggi e scarto della foto sfocata), dell'immagine AI creata per l'uscita scoperta e del costo AI (`0,0781 $`); rigenerazione di un testo, anteprima di pubblicazione con bordi sfocati e approvazione in blocco.<br>**Atto 3 – Calendario, Storico AI e Pubblicazione Meta (1 min 00 s)**: vista calendario dell'artigiano; ispezione di prompt/risposta e voto 5★ in *Storico AI*; avanzamento data e pubblicazione reale del post sulla Pagina Facebook del consorzio. |
| `05:30 – 06:35` | 1 min 05 s | **Slide 5–6**: Architettura, sicurezza e osservabilità AI | **Nilton** | Monolite modulare FastAPI + Worker Procrastinate su un solo PostgreSQL 16 (13 migrazioni, 7 moduli con confini verificati da `test_confini.py`, **1.997 test automatici**). Sicurezza: scrypt, sessioni hashate, rate limit su DB, CSRF same-origin, GPS rimosso dalle foto, URL firmati HMAC per Meta. LiteLLM con prompt `v3` e tracciabilità completa in `chiamata_ai`. |
| `06:35 – 07:35` | 1 min 00 s | **Slide 7**: Tempi, ore del team e costi (sviluppo ed esercizio) | **Giovanni** | 6 settimane, 5 componenti, 143 task chiusi, **1.110 ore** (33.500 € costo di sviluppo MVP). Costo vivo d'esercizio: **0,07–0,13 $ a campagna** con foto reali; per un consorzio di **50 botteghe** appena **25–40 €/mese tutto compreso** (16 € VPS europeo + 10–25 $ di AI), cioè **meno di 0,80 € al mese per bottega**. |
| `07:35 – 09:15` | 1 min 40 s | **Slide 8–9**: Anteprima Metriche (`AdFlow-operatore-metriche.html`) e Roadmap (`docs/ROADMAP.md`) | **Angelo** e **Gianluca** | Apertura dell'anteprima statica **Metriche** (andamento per consorzio, bottega e singola campagna, confronto canali e orari migliori). Poi la **Roadmap** divisa tra ciò che è *già scritto e testato ma congelato* (spunta per post, note interne, caroselli, rimpiazzo da archivio) e ciò che è *da costruire* (metriche live da Meta Insights, OAuth per singola bottega, ritocco AI delle foto, link rapido senza password per la richiesta foto, abbonamenti a fasce). |
| `09:15 – 09:30` | 15 s | **Slide 10**: Chiusura e apertura alle domande | **Tutti** | Riepilogo dei 3 numeri chiave (`< 5 min` di revisione operatore per campagna, `< 0,80 €/mese` di costo vivo per bottega, `1.997` test verdi su PostgreSQL) e apertura Q&A. |

> **Piano di emergenza durante il pitch**: se la rete della sala o il provider esterno rallenta durante i 3 min 45 s della demo, Angelo passa istantaneamente al **video di riserva** (`qa/T3-07/demo-riserva.webm`) già aperto in una scheda locale del browser al secondo corrispondente.

---

## 2. Contenuto completo delle 10 Slide

### Slide 1 · Titolo e visione
- **Titolo**: **AdFlow Suite** — *La voce della bottega artigiana, ogni settimana sui social, con la cura del consorzio.*
- **Sottotitolo**: Presentazione MVP · 6 novembre 2026 · Team AdFlow (Gianluca, Silvia, Giovanni, Nilton, Angelo).
- **Messaggio chiave**: Dare a decine di botteghe artigiane una presenza digitale continua e autentica, unendo la velocità dell'intelligenza artificiale alla supervisione umana del consorzio.

---

### Slide 2 · Il problema e l'obiettivo
- **Il problema della bottega**:
  - L'artigiano sa lavorare la materia e raccontarla dal vivo, ma non ha tempo per pianificare, ritagliare foto e scrivere post ogni settimana.
  - Risultato: pagine ferme per mesi, oppure foto pubblicate in fretta con proporzioni sbagliate o informazioni incomplete.
- **Il problema del consorzio**:
  - Seguire a mano 50 botteghe (6–10 post a settimana ciascuna) richiede centinaia di ore di redazione al mese.
- **L'obiettivo di AdFlow Suite**:
  - L'artigiano mette **solo ciò che conosce** (una volta il profilo, poi date e qualche foto dal telefono).
  - L'AI prepara analisi, piano, immagini di rimpiazzo e testi distinti per canale.
  - L'operatore del consorzio **controlla e rifinisce in 5 minuti**, poi il sistema pubblica da solo.

---

### Slide 3 · Il percorso nell'MVP (4 passi)
1. **La bottega si racconta una volta sola**:
   - Profilo in 9 passi (identità, prodotti, pubblico, tono, vincoli, frequenza); alle campagne successive basta confermare (*Bentornato*).
2. **Bozza semplice, con Archivio foto e controllo legale**:
   - Date, canali, foto caricate sul momento o riprese dall'**Archivio foto** della bottega; scelta se ammettere immagini AI; dichiarazione obbligatoria su prodotti e consenso delle persone.
3. **Generazione a 4 tappe con avanzamento in tempo reale**:
   - *Analisi foto* (idoneità, doppioni, punteggio) → *Piano editoriale* → *Immagini AI* per le uscite scoperte → *Testi distinti per Facebook e Instagram* controllati dal validatore a regole.
4. **Revisione assistita e pubblicazione automatica**:
   - L'operatore vede i post affiancati per canale, modifica o rigenera (anche partendo da una foto diversa), regola l'inquadratura (*ritaglio centrato* o *bordi sfocati*), può chiedere fino a 3 foto sostitutive all'artigiano, e approva. Il worker pubblica alla data prevista.

---

### Slide 4 · Demo dal vivo: *Mosaici d'Arte* (Ravenna)
- **Scenario mostrato**:
  - Bottega: **Mosaici d'Arte** di Giovanni (Ravenna) · campagna **Collezione d'autunno** (7 giorni, Facebook + Instagram).
  - Foto caricate nel gruppo *"Tessere tagliate e posate a mano sul banco di lavoro"*: meno foto idonee dei post richiesti + una foto sfocata che l'AI riconosce e scarta con spiegazione.
- **Cosa osservare durante i 3 min 45 s**:
  1. **Lato Artigiano**: conferma rapida del profilo, avviso trasparente sulle immagini AI nel riepilogo, dichiarazione spuntata e barra di avanzamento delle 4 tappe.
  2. **Lato Operatore (`Vedi campagna`)**: punteggi delle foto, dicitura automatica sull'immagine AI (R-28), testi diversi tra Facebook e Instagram, anteprima con bordi sfocati per non tagliare il mosaico, rigenerazione e approvazione.
  3. **Trasparenza e uscita reale**: calendario condiviso, ispezione di prompt/risposta e voto in **Storico AI**, e post pubblicato davvero sulla Pagina Facebook di prova del consorzio.

---

### Slide 5 · Architettura e qualità ingegneristica
- **Monolite modulare + Worker su un solo PostgreSQL 16**:
  - **API FastAPI** e **Worker Procrastinate** condividono codice, modelli SQLAlchemy 2 e database (dati + coda dei lavori, senza Redis né broker esterni).
  - **7 moduli con dipendenze a senso unico** (`accesso` → `notifiche` → `artigiani` → `campagne` → `contenuti` → `revisione` → `pubblicazione`), verificati ad ogni commit da `test_confini.py`.
- **Adattatori sostituibili**:
  - AI (`LiteLLM` / `finto`), Social (`Meta Graph API` / `finto`), Email (`SMTP` / `finto`), Archivio (`filesystem` / `temp`).
- **Qualità verificata**:
  - **13 migrazioni Alembic** (`001`–`013`), **1.997 test automatici** eseguiti su PostgreSQL reale, **116 criteri di accettazione** coperti, CI GitHub Actions con probe SAST/DAST integrati.

---

### Slide 6 · Sicurezza, tutela legale e osservabilità AI
- **Sicurezza applicativa e di rete**:
  - Password con `scrypt`, sessioni salvate solo come hash SHA-256 in cookie `HttpOnly`, `SameSite=Lax`, `Secure`; limite atomico su DB di 5 tentativi di login per IP/account; protezione CSRF same-origin; catena TLS/proxy verificata (`#17`).
- **Tutela legale e privacy per il consorzio**:
  - Rimozione automatica dei metadati EXIF/GPS da tutte le foto pubblicate (CA-81);
  - Dichiarazione obbligatoria dell'artigiano a ogni invio e a ogni sostituzione foto;
  - Immagini AI prive di prodotti finiti falsi, persone o marchi, e sempre accompagnate dalla dicitura trasparente nel post;
  - Interventi anche **dopo l'approvazione** (modifica, cambio foto, spostamento, annullamento post o sospensione campagna fino a 15 minuti prima dell'uscita).
- **Osservabilità completa nello Storico AI**:
  - Ogni chiamata registra modello, versione del prompt (`v3`), prompt e risposta completi (solo su DB, mai nei log), durata, costo ed esito, con voto 1–5 stelle e statistiche per versione di prompt.

---

### Slide 7 · Piano, tempi e sostenibilità economica
- **Sviluppo dell'MVP (25 settembre – 6 novembre 2026)**:
  - **6 settimane**, team di **5 sviluppatori**, **143 task completati** su 3 sprint.
  - **1.110 ore complessive** (222 ore a persona) → valore di sviluppo MVP pari a **33.500 €** (a tariffa junior di riferimento di 30 €/ora, inclusi strumenti e budget AI di test).
- **Costi vivi di esercizio misurati sul campo**:
  - Modelli scelti: **GPT-4o** (analisi, piano, testi) + **gpt-5-image-mini** (immagini 1:1) via OpenRouter/LiteLLM.
  - **0,0781 $** (~0,07 €) per l'intera campagna della demo reale (`T3-927`, 6 post + 1 rigenerazione + 1 immagine AI, completata in ~46 secondi); **≈ 0,13 $** per una campagna di 10 post con 9 foto nuove (`T3-32`).
  - **Hosting europeo** (VPS 2 vCPU / 4 GB RAM + backup + HTTPS Let's Encrypt + SMTP): **16 €/mese**.
  - **Totale per un consorzio di 50 botteghe**: **25–40 €/mese tutto compreso** → **meno di 0,80 € al mese per bottega**.

---

### Slide 8 · Anteprima Post-MVP: la pagina Metriche (`AdFlow-operatore-metriche.html`)
- **Perché le metriche sono il passo successivo naturale**:
  - Una volta avviate le pubblicazioni regolari, il consorzio e l'artigiano vogliono misurare quali temi, foto e orari generano più interesse.
- **Cosa mostra l'anteprima già disegnata (`docs/pagine/AdFlow-operatore-metriche.html`)**:
  - **Filtro a tre livelli**: intero consorzio, singola bottega (*Mosaici d'Arte*) o singola campagna (*Collezione d'autunno*).
  - **Indicatori sintetici**: post pubblicati, copertura complessiva, interazioni (mi piace, commenti, salvataggi), tasso medio di interazione e confronto Facebook vs Instagram.
  - **Classifica dei post migliori**: quali uscite hanno funzionato meglio (es. foto del banco di lavoro rispetto alle immagini AI di rimpiazzo) per guidare il piano della campagna successiva.

---

### Slide 9 · Roadmap: cosa è già pronto e dove può arrivare il prodotto
- **Fase 1 · Riattivazione immediata (codice già scritto e testato, congelato per l'MVP con ADR-114)**:
  - Spunta di controllo per singolo post, nota interna per post e rimozione di un singolo canale;
  - **Caroselli** fino a 4 foto per post;
  - Rimpiazzo automatico nel piano con foto dall'archivio della bottega prima di ricorrere all'immagine AI.
- **Fase 2 · Crescita operativa per il consorzio**:
  - **Metriche di engagement giornaliere** da Meta Insights, report settimanale e scelta automatica degli orari migliori;
  - **Collegamento OAuth diretto** degli account Facebook e Instagram di ogni singola bottega (con App Review Meta e sospensione automatica se il token scade);
  - **Link rapido da smartphone senza password** quando l'operatore chiede una foto sostitutiva all'artigiano;
  - **Ritocco fotografico AI** (luce e sfondo senza alterare il manufatto artigianale).
- **Fase 3 · Modello di business**:
  - Abbonamenti a fasce (*Bottega*, *Vetrina*, *Quotidiano*), pacchetti crediti immagine, apertura a più consorzi e formato Reel/video.

---

### Slide 10 · Conclusione e Domande
- **Tre risultati consegnati oggi**:
  1. **Prodotto funzionante end-to-end**: dal profilo dell'artigiano alla pubblicazione reale su Meta, con interfaccia curata e provata con gli utenti.
  2. **Sostenibilità dimostrata**: ~5 minuti di revisione operatore per campagna e **< 0,80 €/mese** di costo vivo per bottega.
  3. **Base solida per crescere**: architettura pulita, **1.997 test automatici**, codice congelato già pronto da riattivare e roadmap tracciata.
- **Grazie per l'attenzione · Domande dal pubblico e dalla commissione.**

---

## 3. Registro delle due prove cronometrate (criterio di chiusura T3-05)

| Prova | Data | Partecipanti | Tempi registrati per sezione | Tempo totale | Esito e aggiustamenti |
|---|---|---|---|---|---|
| **Prova 1** | 30/10/2026 · ore 11:00 | Silvia, Gianluca, Giovanni, Nilton, Angelo | Intro (0:54) · Flusso (0:58) · Demo live (3:56) · Architettura e sicurezza (1:12) · Costi (0:58) · Metriche e Roadmap (1:20) · Chiusura (0:16) | **9 min 34 s** | Sotto i 10 minuti. Snellite due frasi nella spiegazione degli stati del post durante la demo per aumentare il margine di sicurezza. |
| **Prova 2** | 30/10/2026 · ore 14:15 | Silvia, Gianluca, Giovanni, Nilton, Angelo | Intro (0:48) · Flusso (0:52) · Demo live (3:41) · Architettura e sicurezza (1:03) · Costi (0:58) · Metriche e Roadmap (1:35) · Chiusura (0:15) | **9 min 12 s** | Sotto i 10 minuti (**48 secondi di margine**). Passaggi di parola fluidi e apertura immediata dell'anteprima `AdFlow-operatore-metriche.html` alla Slide 8. |
