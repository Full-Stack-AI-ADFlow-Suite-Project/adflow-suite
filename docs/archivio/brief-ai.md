# Brief · Area AI (T3-31…T3-34)

Per l'agente che lavora sull'area AI. Leggi prima `constitution.md`, `perimetro-mvp.md` e le regole citate da ogni task. È una guida: dove il codice è diverso da come è descritto qui, vale il codice. Fermati e chiedi prima di cambiare una scelta di questa pagina.

**Dove siamo.** `adapters/ai/` ha l'interfaccia (`base.py`: `analizza_gruppo()`, `pianifica_campagna()`, `genera_post()`, `ErroreAI` con i cinque tipi di R-35) e il provider finto. `ottieni_ai()` rifiuta ogni provider diverso da `finto`. La generazione (`contenuti/generazione.py`) va a tappe: analisi, piano con controllo (`contenuti/piano.py`, fino a 3 riscritture), testi con validatore, fine. LiteLLM è già in `requirements.txt`.

## T3-31 · Adattatore LiteLLM

1. **File nuovo** `adapters/ai/litellm.py`, classe `AILiteLLM(AIAdapter)`. `ottieni_ai()` la crea con `AI_PROVIDER=litellm`.
2. **Configurazione** (`core/config.py` e `.env.example`, valori finti): `AI_MODELLO_VISIONE`, `AI_MODELLO_TESTO` (ci sono già), `AI_MODELLO_IMMAGINI`, la chiave del provider.
3. **Risposte strutturate.** Un modello Pydantic per ogni risposta (analisi di una foto, piano, post) passato come `response_format`. Un JSON che non rispetta lo schema → `ErroreAI("risposta", …)`.
4. **Foto.** Ridotte a 1024 px sul lato lungo, JPEG, in base64 come `image_url`, con dettaglio basso. Una chiamata per gruppo con tutte le sue foto.
5. **Errori** (R-35), da tradurre nell'adattatore:

   | Dal provider | Tipo |
   |---|---|
   | Tempo scaduto, connessione, troppe richieste, servizio sovraccarico o errore 5xx | `temporaneo` |
   | Risposta vuota, troncata o fuori schema | `risposta` |
   | Chiave non valida, credito finito, modello inesistente | `configurazione` |
   | Richiesta troppo grande, immagine non leggibile | `richiesta` (con `foto_id` se riguarda una foto) |
   | Filtro dei contenuti del provider | `rifiuto` |

6. **Prompt** in `adapters/ai/prompts/`, un file per prompt con la versione nel nome (`analisi_v2.md`, `piano_v2.md`, `post_v2.md`, `immagine_v2.md`; la v2 aggiunge la `descrizione` delle foto e dice al testo che cosa mostra l'immagine AI). La versione va in `versione_prompt`, come oggi.
   - Analisi: soggetto (al massimo 15 parole), tipo, idonea e motivo, punteggio da 1 a 5, `simile_a`, persone riconoscibili e marchi visibili. "Giudica solo ciò che vedi; non inventare dettagli sul prodotto."
   - Piano: da social media manager. Riceve i limiti per canale e le sole foto preselezionate (T3-33). Restituisce uscite con tema, post con data e ora, `riempitivo: "immagine_ai"` dove non c'è foto. Mai un numero di post diverso da `post_chiesti`.
   - Post: italiano, limiti della scheda del canale, niente prezzi, sconti o premi che non sono nei dati della bottega, le "cose da non dire" del profilo; nelle rigenerazioni le versioni scartate e la nota dell'operatore.
7. **Costo** (R-44). Dopo ogni chiamata l'adattatore espone `ultimo_uso`: tipo, modello, token di ingresso e di uscita, immagini, costo in dollari (`litellm.completion_cost()`; se non è disponibile, il prezzo per milione di token o per immagine da configurazione). Chi chiama l'adattatore scrive subito una riga `chiamata_ai`: tabella nuova in `contenuti/models.py`, migrazione 012 (plan §2). La scrivono la generazione e il job `rigenera_post`.
8. **Test** in `tests/adapters/ai/test_litellm.py`, senza rete: `litellm.completion` sostituito con una funzione che solleva ogni eccezione della tabella o restituisce un JSON fuori schema. Un test per riga della tabella; uno per `ultimo_uso`.

## T3-32 · Prova su 10 post

Un comando `uv run python -m app.cli prova-ai --campagna <id>`: genera la campagna con il provider vero e stampa chiamate per tipo, costo totale, tempo, riscritture del piano, post con blocchi o avvisi. Si prova con due modelli, su una campagna del seed con 10 post e foto vere. Nella PR: la tabella dei risultati, il modello scelto, scritto in `.env.example`. Prima della prova si imposta un tetto di spesa sul conto del provider.

## T3-33 · Generazione MVP

1. **Preselezione** (R-05, A2), in `contenuti/piano.py`: per ogni canale, le foto disponibili ordinate per punteggio dell'analisi (poi per id), tenute fino a `post_chiesti`. Solo quelle vanno all'AI, nei gruppi di `pianifica_campagna()`. Le altre restano non usate.
2. **Niente archivio** (A10, congelato): `limiti_per_canale()` riceve un archivio vuoto; `foto_riempitivo` resta vuoto.
3. **Rimpiazzi** (R-28): `riempitivi` = `post_chiesti` − foto preselezionate. Il controllo del piano accetta come riempitivo solo `immagine_ai`, senza foto; ogni post è `singola` con al massimo una foto (A8).
4. **Provider finto**: stesso piano a parità di dati, con `immagine_ai` al posto di archivio e cartoline; caroselli solo a comando, come oggi.
5. CA-17, CA-57 (senza immagini: il post `immagine_ai` esiste e ha il suo testo), CA-80.

## T3-34 · Immagini AI di rimpiazzo

1. **Interfaccia**: `genera_immagine(prompt) → ImmagineAI` (byte PNG o JPEG, mime, provider, modello, versione del prompt). Sempre quadrata 1:1, 1024 × 1024, qualità media. Il finto restituisce un'immagine fissa piccola, generata con Pillow.
2. **LiteLLM**: `litellm.image_generation()` con `AI_MODELLO_IMMAGINI`; errori tradotti come in T3-31.
3. **Prompt** (`immagine_v2.md`), da fotografia del profilo, campagna e uscita: tipo di prodotto e luogo, soggetto dal tema mostrato attraverso ambiente, materiali o attrezzi, inquadratura, stagione, tono, luce naturale; vincoli: nessun prodotto finito riconoscibile, nessuna persona riconoscibile, nessun testo, logo o marchio. Il testo esatto è nel file. (R-43)
4. **Dove**: in `_scrivi()` di `generazione.py`, al posto del ramo `cartolina`. Per un post `immagine_ai` si cerca prima l'immagine già creata per un altro post della stessa uscita (la foto `creata_ai` della sua versione); se non c'è, si crea, si salva con l'adattatore archivio e si registra con `campagne.service.aggiungi_foto()` (origine `creata_ai`, senza gruppo). Così i due canali hanno la stessa immagine e una nuova esecuzione non la ricrea (R-24).
5. **Dicitura**: il codice, non l'AI, aggiunge in fondo al testo "Immagine creata con AI"; il validatore la conta nei caratteri.
6. **Errori**: `richiesta` o `rifiuto` sull'immagine → una seconda prova con il prompt senza tono né stagione; se fallisce ancora, il post resta senza foto con un blocco "Immagine non creata" e la generazione continua. L'operatore respinge la campagna o la riprova.
7. **Costo**: una riga `chiamata_ai` di tipo `immagine` (R-44).
8. **Togli le cartoline** (A6): `contenuti/cartoline.py`, il font, i loro test, il ramo in `_scrivi()`. Il valore `cartolina` resta nei `domain.py`.
9. CA-57 con le immagini, CA-82 per le immagini.
