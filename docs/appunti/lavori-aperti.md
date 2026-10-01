# Lavori aperti

Tutto ciò che è ancora da fare, decidere o verificare. Quando un punto si chiude, il risultato entra nelle note o in `ADR.md`, si chiede un assorbimento (vedi `LEGGIMI.md`) e il punto si toglie da qui.

## 1. Analisi (senza codice)

| ID | Task | Serve prima di | Assegnato a | Fatto quando | Stato |
|---|---|---|---|---|---|
| A-01 | **AI e immagini, prompt**: che cosa fa il ritocco (luce, colori, ritaglio, sfondo?), con quali modelli e costi; prompt di analisi foto, generazione post, rigenerazione "da zero" e "da proposta"; formato della risposta dell'AI | in parallelo allo sprint 1; pronto per il 2b (prompt di rigenerazione) e il 3 (ritocco) | | note-flusso.md §4 (2.1b) aggiornato, nuova ADR, prompt di esempio negli appunti | ☐ |
| A-02 | **Campi del profilo**: confermare con un artigiano o un operatore reale quali campi dei passi 1–9 servono davvero | sprint 2a | | elenco confermato in note-flusso.md §3; ADR se cambia qualcosa | ☐ |
| A-03 | **Libreria calendario** per Vedi campagna e dashboard artigiano | sprint 3 | | scelta con motivazione in note-architettura.md §1 e ADR | ☐ |
| A-04 | **Pagine statiche mancanti**: Vedi campagna, elenco artigiani, metriche (come `AdFlow-operatore-artigiano.html`) | Vedi campagna: sprint 2b · elenco: sprint 3 · metriche: sprint 4 | | pagine in `architettura/`, citate in note-flusso.md §5.2 | ☐ |
| A-05 | **Immagini create dall'AI** (ADR-48): da che cosa parte l'AI (profilo, descrizione della campagna, foto caricate?), quante immagini crea e come entrano nel calcolo dei post, come l'operatore le vede e le corregge (cicli, motivi del No), se il post deve dire che l'immagine è creata dall'AI, modello e costi | prima di costruire la generazione delle immagini; sprint da decidere | | note-flusso.md §3 (1.4b) e §4 (2.1c) aggiornati, R-05 e §5.1 completati, nuova ADR se serve | ☐ |

## 2. Domande aperte sul prodotto

- Quali campi del profilo servono davvero all'AI e quali solo all'operatore: da confermare con un artigiano reale prima di costruire la pagina Profilo definitiva (A-02).
- **Ritocco AI**: che cosa fa sulle immagini e con quali istruzioni; istruzioni per le rigenerazioni del testo (A-01).
- **Immagini create dall'AI**: tutto ciò che sta dopo la spunta è da decidere (A-05). In particolare: un'immagine AI di un prodotto artigianale può mostrare un oggetto che la bottega non fa davvero; chi controlla, e che cosa si dice a chi guarda il post?
- Numeri da tarare: durata massima (3 mesi), conversione della frequenza, 1080 px, anticipo di 3 giorni, promemoria 48 ore, cicli 3 + 3, 12 foto al mese, 2 post per foto.
- Anagrafica e accesso dal sito del consorzio: se si fa, cambia il login (ADR-05).
- Accordo di delega consorzio–artigiano per pubblicare sulle sue pagine (da far verificare a un professionista).
- Layout delle metriche nella dashboard artigiano (sprint 4).

## 2b. Struttura a moduli e corsie (ADR-49, ADR-50)

- **Firme dei contratti**: quelle di `docs/agenti/plan.md` §6 sono la prima stesura; si decidono insieme nel task T1-02, poi cambiano solo con un task della corsia 0.
- **Revisione di gruppo delle corsie 1–5**: fissare il momento (ogni giorno? a fine task?).
- **Corsia 1 leggera nello sprint 1** (il profilo arriva dal seed): può dare una mano alla corsia 5 o tenere la penna nei task comuni.
- **Brief dei task più delicati** da scrivere prima di partire: T1-02 contratti, T1-22 API bozza, T1-24 invio, T1-34 generazione, T1-43 pubblicazione.

## 2c. Buchi trovati nella verifica di coerenza del 01/10/2026

Punti in cui i documenti promettono qualcosa che nessun task, endpoint o criterio realizza. Non sono stati chiusi: ognuno aspetta una decisione, poi una riga in `ADR.md` o nelle note e un assorbimento.

| ID | Buco | Dove si vede | Che cosa manca | Serve prima di |
|---|---|---|---|---|
| B-01 | **Riprogrammare un post fallito** | note-flusso.md §6 (passo 4.4), diagramma 04; la transizione `fallito → approvato` esiste | L'endpoint dell'operatore, un criterio di accettazione, lo sprint | sprint 2b |
| B-02 | **Email "campagna pronta" all'operatore** | note-flusso.md §4 (passo 2.5), diagramma 01 | Il tipo di notifica, un criterio di accettazione, lo sprint | sprint 2b (notifiche) |
| B-03 | **Avviso all'operatore per un post fallito** | note-flusso.md §6 (passo 4.4), diagramma 07 | Nello sprint 1 il post fallito si vede solo in Vedi campagna (CA-38): confermare che basti; decidere il tipo di notifica quando nascono (2b) | chiusura dello sprint 1 |
| B-04 | **Calendario dell'artigiano** (post approvati e pubblicati) | note-flusso.md §5.3 | L'endpoint: il dettaglio della campagna non contiene i post; il modulo in cui vive (regola 5 dei confini) | sprint 3 |
| B-05 | **Consenso delle persone nelle foto** | Appendice A di note-flusso.md; nel profilo c'è solo la politica generale (`foto_policy.persone`) | Decidere se serve un campo per la singola foto o per il gruppo | sprint 2a |
| B-06 | **Immagini create dall'AI: invio senza foto** | note-flusso.md R-13 e R-19; pagina statica Campagna | Finché A-05 non è chiusa la spunta si salva soltanto e l'invio richiede un gruppo di foto: la pagina deve dirlo all'artigiano? | sprint 1 (T1-52) |

## 3. Rischi da tenere d'occhio

1. **Testi AI ripetitivi** → prompt per tipo di prodotto, versioni rifiutate come contesto, validatore.
2. **Collo di bottiglia dell'operatore** (20 artigiani × 12 post = 240 post al mese) → approvazione in blocco, anticipo di 3 giorni; misurare nella demo il tempo di revisione per campagna.
3. **Costo delle chiamate AI** (analisi e ritocco foto, creazione di immagini, rigenerazioni) → cicli 3 + 3, stima dei costi, confronto tra provider.
4. **Troppo lavoro per 6 settimane** → la demo copre le fasi 1→3 e simula la pubblicazione; se il tempo stringe si tagliano i campi facoltativi del profilo, mai gli obbligatori.
5. **Multi-provider che si allarga** → nell'MVP due implementazioni: un provider reale e uno finto.
6. **"Funziona sul mio PC"** → versioni fissate (Python, Node, PostgreSQL), `.env.example`, istruzioni di avvio nel README; una sola persona non deve essere l'unica a saper avviare il progetto.
7. **Lavoro in parallelo di più persone** → task piccoli con dipendenze esplicite, un branch per task, sei corsie con cartelle di proprietà (ADR-49, ADR-50); tabelle e migrazioni solo nella corsia comune (vedi `docs/agenti/tasks.md`).
8. **Confini tra i moduli che si sfaldano** (import in avanti, `models` di un altro modulo, stato cambiato fuori dal proprietario) → regole di note-architettura.md §3.5, test dei confini, revisione delle PR.
9. **La fase comune si allunga** (sei task fatti in cinque, prima che parta il lavoro in parallelo) → ordine fisso T1-01…06, una persona scrive e le altre seguono, niente discussioni fuori dal task in corso.

## 4. Punti tecnici da verificare

- LiteLLM: supporto delle immagini per i modelli OpenAI scelti; formato dei nomi dei modelli.
- Modelli OpenAI per visione, testo e **ritocco immagini**, con costi (A-01); modello per la **creazione di immagini** (A-05).
- Regole di Meta sulle immagini create dall'AI (etichetta obbligatoria?) (A-05).
- Modello locale: solo se serve davvero; l'hardware deve reggere la visione.
- Catcher email per lo sviluppo (proposta: Mailpit).
- Libreria per la vista calendario (sprint 3, A-03).
- Server proprio: dominio e certificato HTTPS per l'OAuth dei social.
- Struttura a moduli (ADR-49): Procrastinate deve poter accodare un job per nome senza importare il modulo che lo definisce; Alembic deve vedere tutte le tabelle tramite `app/tabelle.py`; il test dei confini basta scritto a mano o serve una libreria (es. import-linter)?
