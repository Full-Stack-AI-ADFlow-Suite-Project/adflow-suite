# T3-927 · Demo con AI vera e Facebook vero (rapporto automatico)
- ok · Pagina e token Meta configurati

### 0 · Database nuovo, migrazioni, dati della demo (T3-06)

- ok · 2 foto vere caricate, nessuna scartata
- post chiesti per canale: 3; inizio 2026-11-02
- ok · le foto sono meno dei post chiesti (ci sarà un'immagine AI)

### 1 · Operatore: artigiano nuovo con password provvisoria (CA-79)

- ok · la password provvisoria si vede alla creazione
- ok · la stessa email: 409
- ok · il nuovo artigiano entra

### 2 · Artigiano: campagna di 7 giorni solo su Facebook, invio (CA-14, CA-54)

- ok · la campagna è in bozza
- ok · solo Facebook
- ok · passo 12: avviso «foto poche» (immagini AI)
- ok · invio senza dichiarazione rifiutato (422)
- ok · con la dichiarazione: inviata

### 3 · Generazione vera: post per canale, immagine AI, costo (CA-17, CA-57, CA-80, CA-82)

- generazione in 75 s
- ok · 3 post, tutti Facebook
- ok · i post scoperti hanno un'immagine AI, gli altri una foto vera
- ok · dicitura «Immagine creata con AI» sui post con immagine AI (CA-80)
- ok · nessuna dicitura sui post con foto vera
- ok · costo AI della campagna 0.0781 $ (CA-82)
- costo AI della campagna: **0.0781 $**

### 4 · Operatore: modifica, rigenera, richiesta all'artigiano, cambia foto, approva (CA-71, CA-86..90, CA-56)

- modifica a mano del primo post: 200
- ok · testo rigenerato con l'AI vera
- richiesta all'artigiano con una foto segnata (CA-86)
- ok · l'artigiano vede la richiesta (CA-87)
- ok · l'artigiano non legge i post (403)
- l'artigiano ha caricato la foto con la dichiarazione e risposto (CA-88)
- ok · la foto nuova è tra le foto possibili del post
- ok · foto nuova in uso (CA-71)
- ok · campagna approvata
- ok · calendario della campagna per giorno (CA-56)

### 6 · Dopo l'approvazione: modifica, sposta, annulla, sospendi, riattiva (CA-84, CA-72, CA-85, CA-32)

- modifica a mano dopo l'approvazione (esce tra più di 15 minuti)
- post spostato di 2 ore
- ok · campagna sospesa: l'artigiano la vede ferma
- ok · l'artigiano non legge la nota interna
- ok · campagna riattivata
- ok · 2 post approvati da pubblicare (uno annullato)

### 5 · Pubblicazione vera su Facebook, con l'orologio avanti (CA-81, CA-83)

- orologio di API e worker avanti di 9 giorni
- ok · 2 post pubblicati dal worker
- ok · un solo tentativo ok per post, con l'id di Facebook (idempotenza)
- ok · post 1 presente su Facebook (id 1343384632199586_122105993949518445), creato ora
- ok · post 1: il testo su Facebook è quello approvato
- ok · foto del post 1: senza GPS e dritta
- ok · foto del post 1: 720x900, nel formato del canale
- post 1 su Facebook: id `1343384632199586_122105993949518445`, creato 2026-10-29T20:11:02+0000
- ok · post 3 presente su Facebook (id 1343384632199586_122105994063518445), creato ora
- ok · post 3: il testo su Facebook è quello approvato
- ok · foto del post 3: senza GPS e dritta
- ok · foto del post 3: 720x900, nel formato del canale
- post 3 su Facebook: id `1343384632199586_122105994063518445`, creato 2026-10-29T20:11:06+0000
- ok · la campagna si conclude dopo l'ultimo post

Database `adflow_demo`, campagna 1.
