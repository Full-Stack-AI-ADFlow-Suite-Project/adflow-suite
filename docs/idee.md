# Idee

**Non è un piano né un elenco di lavori.** Sono idee che possono restare tali: si possono fare, fare solo in parte o lasciare. Nessun agente le propone e nessun documento le cita. Se una viene fatta, si decide a parte come inserirla nel progetto e nella documentazione, e qui resta solo il suo stato.

Ogni scheda: che cos'è, perché potrebbe servire, fin dove ci si può spingere, stato libero (*idea*, *iniziata*, *fatta in parte*, *lasciata*, *fatta*).

## Limiti noti dello sprint 5

Elenco completo nella nota dello sprint 5 in `docs/agenti/tasks.md`. Uno per scheda, se e quando qualcuno ci lavora.

- **Disco pieno** nelle immagini AI (e nell'archivio foto, congelato), con il file troncato lasciato su disco. *Stato: idea.*
- **Byte NUL** nei filtri, nei form, nella `pagina` dello Storico AI e in `GET /foto/{id}/pubblica`; il test del NUL va riletto. *Stato: idea.*
- **Registro eventi**: i 429 e i 503 delle azioni AI segnati come `login_*`. *Stato: idea.*
- **«Riscrivi anche il testo»** in Cambia foto non blocca il post mentre scrive l'intervento. *Stato: idea.*
- **Intestazioni di sicurezza** assenti sui 500 non gestiti. *Stato: idea.*
- **Dipendenze vulnerabili**: `filelock` (serve `litellm` 4.x) e `black` (solo sviluppo). *Stato: idea.*
- **Costo delle immagini AI** nello Storico AI: prezzo di listino, non quello reale di OpenRouter. *Stato: idea.*
- **Piano con 1 foto e 3 post** che dà l'immagine AI a tutti e tre: da capire se è un difetto. *Stato: idea.*
- **Contrasto**: `npm run test:e2e` da rilanciare con la porta 8000 libera. *Stato: idea.*
- **Test instabile**: `test_api_download_foto_pubblica_firma_alterata_restituisce_404` fallisce circa una volta su 256 (se la firma finisce già con `99` resta valida). La correzione tocca solo il test. *Stato: idea.*
- **Test in locale** con database che non si chiamano `adflow_test`. *Stato: idea.*

## Frontend

Ciò che resta oltre la PR #170: ritocchi d'uso e di stile, pagine che la prova con le persone ha segnalato, telefono. Si può fermare a singole pagine. *Stato: idea.*

Rilievi dell'audit UI (critique Impeccable del 4/11/2026, report in `.impeccable/critique/`) ancora aperti. RL-047, RL-048 e RL-049 erano difetti delle pagine pubbliche e sono corretti nella PR #170.

Da correggere:

- **RL-045** — Le foto caricate si vedono come nomi file, non miniature (`Passo11.tsx`): l'artigiano non può verificare l'upload. `urlFotoFile()` esiste ed è già usata in `VistaStato` e `RichiestaConsorzio`.
- **RL-046** — Il calendario della campagna mostra un segnaposto «AI 1:1» al posto dell'immagine AI, mentre `ArchivioFoto` allo stesso ruolo mostra l'immagine vera (`CalendarioCampagnaView.tsx` contro `ArchivioFoto.tsx`).
- **RL-050** — Detriti di demo: link morto «Post su {canale}» (`PostCard.tsx`), «operatore n. 7» con l'ID invece del nome, errore grezzo «Stato non previsto: {stato}» (`VistaStato.tsx`), `Badge` dentro `Text` in `Artigiani.tsx`.
- **RL-052** — Attriti d'uso: il date picker di `Passo10` ammette una data che il validatore poi rifiuta; gli errori di upload si sovrascrivono e resta solo l'ultimo; «Rimuovi queste foto» elimina serie e descrizione senza conferma; la dichiarazione del passo 12 è rossa prima di toccarla; «Chiama il consorzio» non è un link `tel:`/`mailto:`; i tooltip degli stati ci sono solo per l'operatore; `aria-expanded` mancante sui toggle; 3 `<img>` dell'operatore senza `loading="lazy"`; `Guscio` ricarica il profilo a ogni pagina.
- **RL-053** — Select di filtro in «Campagne da approvare» senza etichetta visibile né valore selezionato leggibile, soprattutto da telefono.
- **RL-055** — Le tile foto non danno feedback se l'immagine non si carica: resta un riquadro grigio vuoto, indistinguibile da un caricamento lento.

Proposte:

- **RL-051** — Deriva di vocabolario e struttura: lo stesso stato appare «inviata» (`SceltaCampagna`) e «In lavorazione» (`ElencoCampagne`); tre schemi colore diversi per i canali e tre per le immagini AI; `Passo12` salta da h2 a h4; grigi freddi `#e9ecef` fuori palette in 5 file.
- **RL-054** — Le barre «Entro quando» sono gialle identiche su ogni riga: l'urgenza non si legge nella barra e si accavalla col bordo rosso di «Preparazione non riuscita».

## Sistema di log

Oggi ci sono il log JSONL e il tracciamento delle richieste (`backend/app/core/log_jsonl.py`, `tracciamento_richieste.py`). L'idea: un posto unico dove leggere ciò che succede (errori, job del worker, pubblicazioni, chiamate AI), con livelli e filtri; da un semplice visore dei file fino a uno strumento esterno. *Stato: idea.*

## Prompt dell'AI

Migliorare i prompt (oggi `v3`) del piano, dei testi e delle immagini AI (`backend/app/adapters/ai/`, `backend/app/moduli/contenuti/generazione.py`), confrontando le versioni con i numeri e i voti dello Storico AI. Si può fare un prompt alla volta. *Stato: idea.*

## Trattamento delle foto

Migliorare la sistemazione delle foto (`backend/app/moduli/campagne/sistemazione_foto.py`): ritaglio sul soggetto, bordi, esposizione, qualità del JPEG; più avanti l'espansione con l'AI, oggi in roadmap. *Stato: idea.*
