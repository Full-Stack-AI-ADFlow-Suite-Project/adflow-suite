# Roadmap · AdFlow Suite

Ciò che non entra nell'MVP del 6 novembre 2026 (ADR-114, `docs/agenti/perimetro-mvp.md`). È anche la slide "dove può arrivare il prodotto" del pitch.
**Da riattivare** = il codice esiste ed è testato, ma nell'MVP è congelato e nascosto. **Da costruire** = solo analisi e, a volte, tabelle già pronte. Le regole (R-xx) e i criteri (CA-xx) di ciò che è da costruire sono in `docs/agenti/spec.md` §7.

## Contenuti e AI

| Voce | Stato | Origine |
|---|---|---|
| Caroselli: più foto in un post | Da riattivare | A8; R-21, R-28 |
| Foto d'archivio della bottega come rimpiazzo, prima dell'immagine AI | Da riattivare | A10; R-27 |
| Ritocco delle foto con l'AI, versioni delle foto, "ritocca di nuovo" e scelta della versione | Da costruire | C4; R-03, R-17 |
| Analisi AI della foto che l'artigiano carica con una richiesta del consorzio (oggi la giudica l'operatore) | Da costruire | ADR-116; R-46 |
| Immagine AI chiesta dall'operatore sul singolo post, al posto di una foto | Da costruire | ADR-116 |
| Immagini AI chieste dall'artigiano con un gruppo `create_ai` | Da costruire | A4; R-19 |
| Immagini AI che partono da una foto vera (prodotto ambientato, sfondo nuovo) | Da costruire | proposta del team del 12/10 |
| Varianti dei post per test A/B sull'engagement | Da costruire | proposta del team del 12/10 |
| Crediti immagine per fascia e pacchetti extra | Da costruire | A12; proposta del team del 12/10 |

## Dashboard e metriche

| Voce | Stato | Origine |
|---|---|---|
| Metriche di engagement per post, campagna e canale, lette ogni giorno | Da costruire | E2; R-39; CA-44, CA-75 |
| Report settimanale agli operatori e riepilogo di fine campagna all'artigiano | Da costruire | R-39 |
| Calendario d'insieme di tutte le campagne, per l'operatore | Da costruire | E1 |
| Orari dei post scelti dalle metriche della pagina | Da costruire | appunti in archivio (sfasamento e orari) |

## Operatore e account

| Voce | Stato | Origine |
|---|---|---|
| Spunta "va bene", nota interna, togli canale | Da riattivare | B4; R-30, R-32 |
| Richiesta all'artigiano con un link a tempo, da telefono e senza password (nell'MVP passa dal suo account) | Da costruire | ADR-116; R-46 |
| Indicatore di recuperabilità della campagna in revisione (chiedere all'artigiano o respingere) | Da costruire | ADR-116 |
| Motivi codificati della sospensione e misure per motivo (nell'MVP una nota libera) | Da costruire | ADR-116; R-33 |
| Pagine dell'operatore: ingresso con "Da sistemare", elenco artigiani, pagina artigiano, campagne chiuse | Da costruire | R-38 |
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
