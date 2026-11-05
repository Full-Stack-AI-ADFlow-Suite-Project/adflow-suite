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

## Sistema di log

Oggi ci sono il log JSONL e il tracciamento delle richieste (`backend/app/core/log_jsonl.py`, `tracciamento_richieste.py`). L'idea: un posto unico dove leggere ciò che succede (errori, job del worker, pubblicazioni, chiamate AI), con livelli e filtri; da un semplice visore dei file fino a uno strumento esterno. *Stato: idea.*

## Prompt dell'AI

Migliorare i prompt (oggi `v3`) del piano, dei testi e delle immagini AI (`backend/app/adapters/ai/`, `backend/app/moduli/contenuti/generazione.py`), confrontando le versioni con i numeri e i voti dello Storico AI. Si può fare un prompt alla volta. *Stato: idea.*

## Trattamento delle foto

Migliorare la sistemazione delle foto (`backend/app/moduli/campagne/sistemazione_foto.py`): ritaglio sul soggetto, bordi, esposizione, qualità del JPEG; più avanti l'espansione con l'AI, oggi in roadmap. *Stato: idea.*
