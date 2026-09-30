# Lavori aperti

Tutto ciò che è ancora da fare, decidere o verificare. Quando un punto si chiude, il risultato entra nelle note o in `ADR.md`, si chiede un assorbimento (vedi `LEGGIMI.md`) e il punto si toglie da qui.

## 1. Analisi (senza codice)

| ID | Task | Serve prima di | Assegnato a | Fatto quando | Stato |
|---|---|---|---|---|---|
| A-01 | **AI e immagini, prompt**: che cosa fa il ritocco (luce, colori, ritaglio, sfondo?), con quali modelli e costi; prompt di analisi foto, generazione post, rigenerazione "da zero" e "da proposta"; formato della risposta dell'AI | in parallelo allo sprint 1; pronto per il 2b (prompt di rigenerazione) e il 3 (ritocco) | | note-flusso.md §4 (2.1b) aggiornato, nuova ADR, prompt di esempio negli appunti | ☐ |
| A-02 | **Campi del profilo**: confermare con un artigiano o un operatore reale quali campi dei passi 1–9 servono davvero | sprint 2a | | elenco confermato in note-flusso.md §3; ADR se cambia qualcosa | ☐ |
| A-03 | **Libreria calendario** per Vedi campagna e dashboard artigiano | sprint 3 | | scelta con motivazione in note-architettura.md §1 e ADR | ☐ |
| A-04 | **Pagine statiche mancanti**: Vedi campagna, elenco artigiani, metriche (come `AdFlow-operatore-artigiano.html`) | Vedi campagna: sprint 2b · elenco: sprint 3 · metriche: sprint 4 | | pagine in `architettura/`, citate in note-flusso.md §5.2 | ☐ |

## 2. Domande aperte sul prodotto

- Quali campi del profilo servono davvero all'AI e quali solo all'operatore: da confermare con un artigiano reale prima di costruire la scheda definitiva (A-02).
- **Ritocco AI**: che cosa fa sulle immagini e con quali istruzioni; istruzioni per le rigenerazioni del testo (A-01).
- Numeri da tarare: durata massima (3 mesi), conversione della frequenza, 1080 px, anticipo di 3 giorni, promemoria 48 ore, cicli 3 + 3, 12 foto al mese, 2 post per foto.
- Anagrafica e accesso dal sito del consorzio: se si fa, cambia il login (ADR-05).
- Accordo di delega consorzio–artigiano per pubblicare sulle sue pagine (da far verificare a un professionista).
- Layout delle metriche nella dashboard artigiano (sprint 4).

## 3. Rischi da tenere d'occhio

1. **Testi AI ripetitivi** → prompt per tipo di prodotto, versioni rifiutate come contesto, validatore.
2. **Collo di bottiglia dell'operatore** (20 artigiani × 12 post = 240 post al mese) → approvazione in blocco, anticipo di 3 giorni; misurare nella demo il tempo di revisione per campagna.
3. **Costo delle chiamate AI** (analisi e ritocco foto, rigenerazioni) → cicli 3 + 3, stima dei costi, confronto tra provider.
4. **Troppo lavoro per 6 settimane** → la demo copre le fasi 1→3 e simula la pubblicazione; se il tempo stringe si tagliano i campi facoltativi della scheda, mai gli obbligatori.
5. **Multi-provider che si allarga** → nell'MVP due implementazioni: un provider reale e uno finto.
6. **"Funziona sul mio PC"** → versioni fissate (Python, Node, PostgreSQL), `.env.example`, istruzioni di avvio nel README; una sola persona non deve essere l'unica a saper avviare il progetto.
7. **Lavoro in parallelo di più persone** → task piccoli con dipendenze esplicite, un branch per task, `domain.py` e `models.py` toccati da un task alla volta (vedi `docs/agenti/tasks.md`).

## 4. Punti tecnici da verificare

- LiteLLM: supporto delle immagini per i modelli OpenAI scelti; formato dei nomi dei modelli.
- Modelli OpenAI per visione, testo e **ritocco immagini**, con costi (A-01).
- Modello locale: solo se serve davvero; l'hardware deve reggere la visione.
- Catcher email per lo sviluppo (proposta: Mailpit).
- Libreria per la vista calendario (sprint 3, A-03).
- Server proprio: dominio e certificato HTTPS per l'OAuth dei social.
