# Perimetro MVP

Decisione ADR-114 del 13/10/2026, approvata dal team. Consegna e pitch il **6 novembre 2026**; codice bloccato il **30 ottobre**.
Questa pagina dice che cosa entra nell'MVP. Dove `spec.md`, `plan.md` o `tasks.md` non tornano con questa pagina, vale questa pagina.

| Decisione | Significato |
|---|---|
| **Mantieni** | Resta nell'MVP com'è |
| **Task MVP** | Si costruisce o si cambia nello sprint 3 · MVP (`tasks.md`) |
| **Congela** | Il codice e i suoi test restano; l'interfaccia lo nasconde; non si estende |
| **Togli** | Si rimuovono codice e test (T3-01; il minimo di foto in T3-22, le cartoline in T3-34); tabelle e migrazioni restano |
| **Roadmap** | Non si costruisce: va in `docs/ROADMAP.md` e nel pitch |

## Metodo

| ID | Decisione |
|---|---|
| M1 | I quattro deliverable della traccia (analisi, architettura, piano con costi e tempi, pitch) sono il percorso critico |
| M2 | L'AI vera è il primo lavoro dello sprint: prova su 10 post appena l'adattatore esiste |
| M4 | In caso di dubbio si congela; si toglie solo ciò che confonde la demo o blocca il lavoro |

## A · Generazione e piano

| ID | Tema (regole) | Decisione | Nell'MVP |
|---|---|---|---|
| A1 | Chi redige il piano (R-05, R-09) | Task MVP | L'AI vera valuta le foto e redige il piano; il numero dei post per canale lo fissa il codice dalla frequenza; il controllo R-09 resta |
| A2 | Foto e post (R-05, R-25) | Mantieni, riscritta | Post = frequenza. Foto in meno: immagini AI. Foto in più: il codice passa all'AI solo le migliori per punteggio dell'analisi, fino ai post chiesti |
| A3 | Piano debole, `piano_da_rivedere`, Prosegui (R-20) | Togli | Il piano è sempre completo; l'operatore approva o respinge |
| A4 | Immagini AI (R-19, R-28) | Task MVP | Unico rimpiazzo delle foto mancanti; gruppi `create_ai` in roadmap |
| A5 | Minimo di 4 foto all'invio (R-13) | Togli | Senza foto la campagna è tutta con immagini AI |
| A6 | Cartolina (R-28) | Togli | Sostituita dall'immagine AI |
| A7 | Logo (R-40) | Togli | Il logo è una foto come le altre |
| A8 | Caroselli (R-21, R-28) | Congela | Un post = una foto |
| A9 | Date e ore dei post (R-08) | Mantieni | Le decide l'AI nel piano; il controllo R-08 resta |
| A10 | Archivio della bottega come rimpiazzo (R-27) | Congela | Ogni foto mancante diventa un'immagine AI |
| A11 | Foto con la stella (R-23) | Togli | Le foto le sceglie la valutazione dell'AI; la colonna `da_usare` resta |
| A12 | Spesa per le immagini AI | Task MVP | Nessun tetto; costo di ogni chiamata AI registrato e mostrato in Vedi campagna |

### Casi della generazione

| Caso | Cosa fa la generazione |
|---|---|
| Foto idonee = post chiesti | Una foto per post |
| Foto idonee meno dei post | Immagini AI per i post mancanti |
| Nessuna foto | Tutti i post con immagini AI |
| Foto idonee più dei post | Il codice passa all'AI le migliori per punteggio; le altre restano non usate |
| Foto non idonee (sfocate, scure, doppioni) | Escluse con il motivo; contano come mancanti |
| Errore tecnico dell'AI | `generazione_fallita` e Riprova (R-35) |

In ogni caso il piano esce completo e l'operatore approva o respinge.

**Regola delle immagini AI.** Mostrano ambienti, materiali, attrezzi, lavorazioni, atmosfere e stagioni; mai un prodotto finito come se fosse della bottega, mai persone riconoscibili, testi o marchi. Sono quadrate 1:1, valide su Facebook e Instagram: un'uscita usa la stessa immagine su entrambi i canali. Il post porta l'indicazione "Immagine creata con AI".

## E · Dashboard

| ID | Tema (regole) | Decisione | Nell'MVP |
|---|---|---|---|
| E1 | Calendario editoriale | Task MVP | Solo per campagna: in Vedi campagna e nella vista dell'artigiano; elenco per giorno, nessuna libreria nuova |
| E2 | Metriche (R-39) | Roadmap | Nel pitch la pagina statica delle metriche come anteprima |
| E3 | Stato dei canali collegati (`GET /canali`) | Mantieni | Copre "gestire le piattaforme" |

## G · Deliverable della traccia

| ID | Deliverable | Decisione | Fonte |
|---|---|---|---|
| G1–G3 | Proposta tecnica: un solo documento in tre capitoli (analisi; architettura, schema dati e stack; piano, costi e tempi) | Task MVP | `spec.md`, `plan.md`, `constitution.md` §2, `tasks.md`, `ROADMAP.md`, diagrammi |
| G4 | Pitch di 10 minuti, demo dal vivo con video di riserva | Task MVP | Tutti i precedenti |

## B · Revisione

| ID | Tema (regole) | Decisione | Nell'MVP |
|---|---|---|---|
| B1 | Approva, respingi, riprova, modifica a mano, rigenera testo (R-14, R-18, R-30, R-35) | Mantieni | Le sole azioni visibili in Vedi campagna |
| B2 | Rigenerazioni del testo (R-03, R-04) | Mantieni | 3 per post |
| B3 | Respinta (R-18) | Mantieni | Motivo `foto` / `altro` e nota; i tre casi di respinta sono linee guida (spec §3) |
| B4 | Spunta, nota interna, togli canale (R-30, R-32) | Congela | Nascosti |
| B5 | Sospendi, riattiva, annulla, riprogramma (R-16, R-33, R-34) | Congela | Nascosti |
| B6 | Scadenze automatiche (R-06) | Mantieni | Nessun lavoro |
| B7 | Promemoria 48 h (R-06) | Roadmap | — |

## C · Foto

| ID | Tema (regole) | Decisione | Nell'MVP |
|---|---|---|---|
| C1 | Sistemazione delle foto (R-17, R-36) | Task MVP | Locale e automatica con Pillow: rotazione, GPS tolto, ritaglio 1:1 o 4:5, 1080 px, autocontrasto leggero, JPEG; una funzione per anteprima e pubblicazione |
| C2 | Controlli sulle foto (R-13) | Mantieni | Formato, peso, 1080 px; qualità e doppioni dall'analisi dell'AI |
| C3 | Dichiarazione dell'artigiano | Task MVP | Spunta obbligatoria all'invio: "Le foto mostrano prodotti della mia bottega; le persone riconoscibili hanno dato il consenso" |
| C4 | Ritocco AI, versioni delle foto, cicli di ritocco (R-03, R-17) | Roadmap | La migrazione 012 di `versione_foto` non si fa |

## D · Operatore, account, notifiche, pubblicazione

| ID | Tema (regole) | Decisione | Nell'MVP |
|---|---|---|---|
| D1 | Pubblicazione reale | Task MVP | Facebook e Instagram su una sola pagina di prova del team, da `.env`, per tutti gli artigiani; Standard Access, senza App Review. Se Instagram non pubblica entro il 23/10 resta simulato |
| D2 | Nuovo artigiano (R-37) | Task MVP | L'operatore crea l'utente artigiano (email, nome); password provvisoria mostrata una volta; il profilo lo compila l'artigiano |
| D3 | Collegamento degli account social | Roadmap | Tutti pubblicano sulla pagina di prova di `.env` |
| D4 | Notifiche | Congela | Righe nel database ed email al catcher locale |
| D5 | Permesso scaduto o account scollegato (R-07) | Roadmap | L'errore resta un post `fallito` |

### Meta in breve

Pagina Facebook di prova e account Instagram professionale collegato, amministrati da una persona del team; app Business su developers.facebook.com; strada "Instagram API with Facebook Login": un token della Pagina per entrambi i canali. Permessi: `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish`. Facebook: `POST /{page-id}/photos`. Instagram: `POST /{ig-id}/media` con `image_url`, poi `POST /{ig-id}/media_publish`. Instagram accetta solo JPEG, da un indirizzo pubblico (tunnel in demo). Completare subito la Page Publishing Authorization, se la Pagina la chiede. Fonti: [Content Publishing](https://developers.facebook.com/documentation/instagram-platform/content-publishing), [Pages API](https://developers.facebook.com/documentation/pages-api).

## Pagine statiche (`docs/pagine`)

Si aggiornano all'MVP (T3-03) e tornano il riferimento per l'interfaccia.

| Pagina | Nell'MVP |
|---|---|
| Login | Com'è |
| Profilo bottega | Passo 7 senza logo né archivio |
| Campagna (passi 10–12) | Senza stella né gruppi da creare con l'AI; nessun minimo di foto; avviso dei post con immagine AI; dichiarazione al passo 12 |
| Campagna, viste per stato | Senza `piano_da_rivedere`; calendario per giorno nelle viste dopo l'approvazione |
| Campagne da approvare | Com'è, senza `piano_da_rivedere` |
| Vedi campagna | Solo approva, respingi, riprova, modifica a mano, rigenera; "Immagine AI" sui post; costo AI; calendario; senza spunta, nota interna, togli canale, sospensione, ritocco, cambia foto, sposta |
| Nuovo artigiano | Solo email e nome; password provvisoria mostrata una volta |
| Ingresso, elenco artigiani, pagina artigiano, campagne chiuse | Roadmap: restano, segnate così nella mappa |
| Metriche | Roadmap: anteprima nel pitch |

## F · Processo

| ID | Tema | Decisione | Nell'MVP |
|---|---|---|---|
| F1 | Corsie e proprietà dei file | Togli | Aree di lavoro leggere: un task tocca i file che gli servono |
| F2 | Approvazione di tutto il team | Togli | Una revisione di un collega e controlli verdi; per `core/`, migrazioni e `requirements.txt` la rivede il referente dei file comuni (Giovanni) |
| F3 | Apertura e chiusura, firme prima del codice, colonna Tocca, prestito | Togli | Ogni task ha cosa fare e "fatto quando"; la chiusura è la prova del percorso della demo |
| F4 | Due canali di documenti e assorbimento | Togli | Vale `docs/agenti/`; `docs/archivio/` è un archivio, le pagine statiche sono in `docs/pagine/` (ADR-115); ADR nuova solo se cambia il perimetro |
| F5 | `allinea.py`, controlli delle PR, `test_confini.py`, branch per task | Mantieni | — |
