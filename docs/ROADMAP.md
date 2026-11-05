# Roadmap · AdFlow Suite

Ciò che non entra nell'MVP (ADR-114; il perimetro com'era deciso è in `docs/archivio/perimetro-mvp.md`) e ciò che manca per andare in produzione. È anche la slide "dove può arrivare il prodotto" del pitch.
**Da riattivare** = il codice esiste ed è testato, ma nell'MVP è congelato: l'interfaccia lo nasconde e non si estende (commento "Congelato per l'MVP, ADR-114"). **Da costruire** = solo analisi e, a volte, tabelle già pronte. Le regole (R-xx) e i criteri (CA-xx) di ciò che è da costruire sono in `docs/archivio/fuori-mvp.md`.

## Contenuti e AI

| Voce | Stato | Origine |
|---|---|---|
| Caroselli: più foto in un post | Da riattivare | A8; R-21, R-28 |
| Foto d'archivio della bottega come rimpiazzo, prima dell'immagine AI | Da riattivare | A10; R-27 |
| Ritocco delle foto con l'AI, versioni delle foto, "ritocca di nuovo" e scelta della versione | Da costruire | C4; R-03, R-17 |
| Analisi AI della foto che l'artigiano carica con una richiesta del consorzio (oggi la giudica l'operatore) | Da costruire | ADR-116; R-46 |
| Immagini AI chieste dall'artigiano con un gruppo `create_ai` | Da costruire | A4; R-19 |
| Immagini AI che partono da una foto vera (prodotto ambientato, sfondo nuovo) | Da costruire | proposta del team del 12/10 |
| Espansione della foto con l'AI per le proporzioni dei canali (outpainting) | Da costruire | ADR-119 |
| Anteprima della foto sistemata con la scelta «taglia o bordi» per post | Da costruire | ADR-119 |
| Esportazione dello storico dell'AI | Da costruire | ADR-119 |
| Varianti dei post per test A/B sull'engagement | Da costruire | proposta del team del 12/10 |
| Crediti immagine per fascia e pacchetti extra | Da costruire | A12; proposta del team del 12/10 |

## Dashboard e metriche

| Voce | Stato | Origine |
|---|---|---|
| Metriche di engagement per post, campagna e canale, lette ogni giorno | Da costruire | E2; R-39; CA-44, CA-75 |
| Report settimanale agli operatori e riepilogo di fine campagna all'artigiano | Da costruire | R-39 |
| Calendario mensile, con trascinamento dei post (nell'MVP la settimana, ADR-117) | Da costruire | E1; R-48 |
| Orari dei post scelti dalle metriche della pagina | Da costruire | appunti in archivio (sfasamento e orari) |

## Operatore e account

| Voce | Stato | Origine |
|---|---|---|
| Spunta "va bene", nota interna, togli canale | Da riattivare | B4; R-30, R-32 |
| Richiesta all'artigiano con un link a tempo, da telefono e senza password (nell'MVP passa dal suo account) | Da costruire | ADR-116; R-46 |
| Indicatore di recuperabilità della campagna in revisione (chiedere all'artigiano o respingere) | Da costruire | ADR-116 |
| Motivi codificati della sospensione e misure per motivo (nell'MVP una nota libera) | Da costruire | ADR-116; R-33 |
| Ingresso dell'operatore con "Da sistemare"; nell'elenco artigiani codice, iscrizione e stato degli account per canale; pagina a parte delle campagne chiuse (elenco, pagina e campagne dell'artigiano sono nell'MVP, ADR-117) | Da costruire | R-29, R-38 |
| Archivio foto modificabile: caricare, eliminare e organizzare le foto della bottega (nell'MVP in sola lettura, ADR-117) | Da costruire | R-27, R-47 |
| Anagrafica completa: codice ART, codice consorzio, telefono, iscrizione sospesa | Da costruire | R-37 |
| Cambio password obbligato al primo accesso | Da costruire | R-37; CA-73 |
| Collegamento degli account social di ogni artigiano (OAuth), con Advanced Access, App Review e verifica aziendale di Meta | Da costruire | D3 |
| Campagna sospesa quando un permesso scade o un account si scollega | Da costruire | D5; R-07; CA-40 |
| Promemoria agli operatori 48 ore prima dell'inizio | Da costruire | B7; R-06; CA-42 |
| Email vere al posto del catcher locale | Da costruire | D4 |

## Prodotto e business

| Voce | Stato | Origine |
|---|---|---|
| Abbonamento a fasce (es. Bottega, Vetrina, Quotidiano), prezzi e fatturazione; chi paga tra artigiano e consorzio | Da costruire | R-26; proposta del team del 12/10 |
| Approvazione dei post da parte dell'artigiano | Da costruire | appunti in archivio (note sul flusso) |
| Anagrafica e accesso dal sito del consorzio | Da costruire | ADR-05 |
| Altri canali (LinkedIn, TikTok, X) e video | Da costruire | appunti in archivio (note sul flusso) |
| Più consorzi; app mobile; calendario con trascinamento | Da costruire | appunti in archivio (note sul flusso) |

## Prima della produzione

Ciò che la valutazione di sicurezza del 30/10/2026 (`docs/archivio/valutazione-sicurezza.md`) e la simulazione di accettazione (`docs/archivio/accettazione/sintesi.md`, rilievi RL-xxx) hanno lasciato aperto dopo lo sprint 5. MFA, recupero password e tetto di spesa AI cambiano il perimetro.

| Voce | Rilievi |
|---|---|
| Rilascio e staging: container, compose, proxy, rollback; la prova di TLS e proxy (oggi solo locale) ripetuta su uno staging vero, backend raggiungibile solo dal proxy, redirect HTTPS e HSTS, access log senza query string | RL-032, RL-033, issue #17 |
| Segreti in un secret manager, con rotazione e revoca coordinate; chiave dedicata per le foto firmate, distinta da quella dei contatori del login; token Meta con i permessi minimi; utente del database con privilegi minimi; backup cifrati con un ripristino provato | RL-038 |
| CSRF e CORS: caso del sottodominio non autorizzato, API same-origin o allowlist esatta | — |
| Sessioni: MFA per operatore e admin, durata massima assoluta, revoca di tutte le sessioni di un utente, reset della password con token monouso | — |
| Abuso e spesa: rate limit per endpoint su upload e job, limiti di concorrenza, budget e interruttore sul provider AI, limiti al proxy sulle foto pubbliche | — |
| Osservabilità: log centralizzati con allarmi, eventi anche per ruoli, approvazioni e pubblicazioni, procedura di risposta agli incidenti; prove di carico complete | RL-031 |
| CI: aggiornamenti automatici e lock delle dipendenze transitive, scansione dei segreti, mypy, copertura, E2E, Actions fissate a uno SHA | RL-001, RL-002, RL-003, RL-008, RL-030 |
| Privacy e AI Act: inventario dei dati, che cosa va al provider AI, conservazione e cancellazione (anche dello storico AI), registro, DPA, DPIA | RL-019, RL-040…RL-044 |
| Storage delle foto condiviso tra le istanze, token social cifrati | RL-017, RL-034, RL-039 |

I limiti noti dei task dello sprint 5, non corretti, sono in `docs/agenti/tasks.md`.
