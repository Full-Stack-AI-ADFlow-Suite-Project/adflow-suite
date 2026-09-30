# Spec · cosa fa il prodotto

I numeri stanno solo nelle regole (§5); il resto rimanda agli ID.

## 1. Attori
- **Artigiano**: compila il profilo della bottega, crea e invia campagne con foto, vede il calendario approvato.
- **Operatore** (del consorzio): rivede le campagne e decide; gestisce anagrafica e account social.
- **Admin**: crea operatori, configura. **Sistema**: genera, controlla scadenze, pubblica, invia email.
Un solo consorzio.

## 2. Flusso
**2.1 Scheda bottega** (una pagina, passi 1–12). Passi 1–9 = profilo (una volta; ai rientri schermata **Bentornato**: "Va bene così" → passo 10 senza salvare, "Modifica" → passo 1). Passo 10 = campagna in **bozza** (titolo, inizio, fine, descrizione). Passo 11 = foto a **gruppi**, una descrizione per gruppo. Passo 12 = **invio**: copia canali, frequenza e obiettivo dal profilo e ne salva la fotografia (`profilo_snapshot`). R-08, R-10…R-13.

**2.2 Generazione** (worker): analisi foto → ritocco foto (dallo sprint 3) → slot del calendario → testo e hashtag per slot → validatore. R-05, R-08, R-09. Fine: post `da_approvare`, campagna `in_revisione`.

**2.3 Revisione** (operatore, pagina **Vedi campagna**): sistema i post con gli interventi AI (§3), poi decide sulla campagna: **approva** (tutti i post approvati, campagna `attiva`), **rimanda** (etichetta + nota, stato invariato, nessuna email), **respingi** (motivo + nota, email all'artigiano). R-06, R-14…R-18.

**2.4 Pubblicazione** (tick ogni minuto): pubblica i post approvati alla loro data sulla pagina dell'artigiano; errori temporanei ritentati; tutti pubblicati o falliti → `conclusa`. R-01, R-07.

## 3. Motivi del No e interventi
| Motivo | Azione | Limite | Dopo il limite |
|---|---|---|---|
| Foto scattate male | Respingi con motivo `foto`, nota, foto da rifare segnate | — | — |
| Foto ritoccata male dall'AI | **Ritocca di nuovo** (nota facoltativa), vale solo per quel post | R-03 | Scegli foto originale o versione precedente (non consuma cicli) |
| Testo o hashtag scritti male | **Rigenera da zero** oppure **da testo proposto** + nota; stessa foto | R-03 | Solo Respingi con motivo `altro` |
| Altro | Respingi con motivo `altro` e nota | — | — |

Ogni intervento crea una nuova versione del post, che ripassa il validatore; le versioni rifiutate vanno all'AI come "cosa non rifare". Un post `da_rivedere` si sblocca solo con un nuovo intervento.

## 4. Cosa vede chi
- **Artigiano**: mai post `da_approvare`, `scartato` o `scaduto`. In revisione nessun post. Se `respinta`: motivo, nota e foto da rifare (anche nel Bentornato e per email). Se `scaduta`: avviso (anche per email).
- **Operatore**, pagina artigiano, sezioni: *Da approvare* = inviata, in_generazione, generazione_fallita (con Riprova), in_revisione · *In corso* = attiva, sospesa · *Scadute* = scaduta · *Passate* = conclusa, annullata, respinta. Un solo pulsante: Vedi campagna.

## 5. Regole
| ID | Regola |
|---|---|
| R-01 | Si pubblica solo un post approvato. |
| R-02 | Ogni intervento crea una nuova versione; le precedenti restano. |
| R-03 | Per post: max **3** rigenerazioni del testo (da zero + da proposta insieme) e max **3** ritocchi della foto. |
| R-04 | Le versioni rifiutate vanno all'AI come esempi di "cosa non rifare". |
| R-05 | Una foto alimenta max **2** post. Post = min(post/settimana × settimane, foto × 2); canali alternati. |
| R-06 | Promemoria all'operatore **48 h** prima dell'inizio; non approvata alle **00:00** (Europe/Rome) del giorno di inizio → `scaduta` con tutti i post. |
| R-07 | Account non collegato o permesso scaduto alla pubblicazione → campagna `sospesa` + avvisi. |
| R-08 | Inizio ≥ oggi + **3** giorni (alla creazione, modifica e invio); fine > inizio; durata ≤ **92** giorni; slot mai nel passato (adesso + **15** min). |
| R-09 | Testo non valido → riscrive max **3** volte, poi `da_rivedere`. Errore tecnico AI → **3** esecuzioni, poi `generazione_fallita` e Riprova dell'operatore. |
| R-10 | Profilo compilato una volta; ai rientri si conferma o si modifica. |
| R-11 | All'invio la campagna salva la fotografia del profilo; generazione e rigenerazioni usano quella. |
| R-12 | Una sola bozza per artigiano; campagne non `annullata/conclusa/respinta/scaduta` non sovrapposte. |
| R-13 | Invio solo con almeno un gruppo di foto e una descrizione per ogni gruppo. Foto: JPG/PNG/WEBP, ≤ **10 MB**, lato corto ≥ **1080 px**. |
| R-14 | Si approva la campagna in blocco; mai con un post `da_rivedere` o con un intervento in corso. |
| R-15 | Respinta o scaduta = chiusa; non blocca il periodo; l'artigiano ne crea una nuova. |
| R-16 | In campagna attiva o sospesa nessun intervento sui post; si sospende o si annulla. |
| R-17 | Il ritocco vale solo per il post su cui si lavora; l'originale resta. |
| R-18 | Foto scattate male → Respingi con motivo `foto` e le foto da rifare segnate; l'AI non prova a salvarle. Respingi richiede sempre motivo (`foto` / `altro`) e nota. |

## 6. Criteri di accettazione
Dato / Quando / Allora in forma breve. `S` = sprint in cui diventa verde. Il test porta l'ID nel nome (`test_ca09_...`).

| ID | S | Dato → Quando → Allora |
|---|---|---|
| CA-01 | 1 | utente attivo → login corretto → entra con il suo ruolo |
| CA-02 | 1 | utente → password errata → rifiutato, senza dire quale dato è sbagliato |
| CA-03 | 1 | artigiano → funzione operatore → 403 |
| CA-04 | 1 | artigiano → campagna o foto di un altro → 404 |
| CA-05 | 2a | artigiano senza profilo → entra → passo 1 |
| CA-06 | 2a | artigiano con profilo → rientra → Bentornato; "Va bene così" non salva il profilo |
| CA-07 | 2a | passo 9 → manca un obbligatorio → non salva e lo indica |
| CA-08 | 2a | bozza aperta → rientra → riprende dal passo 10 con dati e foto |
| CA-09 | 1 | → crea o invia con inizio < oggi + 3 giorni → 422 (anche bozza ferma) |
| CA-10 | 1 | → durata > 92 giorni o fine ≤ inizio → 422 |
| CA-11 | 1 | bozza esistente → nuova bozza → 409 |
| CA-12 | 1 | campagna attiva → periodo sovrapposto → 409; se la precedente è respinta o scaduta → ok |
| CA-13 | 1 | bozza → foto non immagine, > 10 MB o lato < 1080 px → 422 con motivo |
| CA-14 | 1 | bozza senza foto o gruppo senza descrizione → invio → 422 |
| CA-15 | 1 | bozza completa → invio → inviata, canali/frequenza/obiettivo copiati, snapshot salvato |
| CA-16 | 2a | campagna inviata → profilo modificato → generazione e Riprova usano lo snapshot |
| CA-17 | 1 | 4 settimane, 3 post/sett., 2 canali, 5 foto → generazione → 10 post, canali alternati, nessuna foto > 2 usi |
| CA-18 | 1 | testo che viola le regole → 3 riscritture non valide → post `da_rivedere` |
| CA-19 | 1 | errore AI a ogni esecuzione → 3 esecuzioni → `generazione_fallita`; Riprova → inviata e riparte |
| CA-20 | 1 | generazione riuscita → post `da_approvare`, campagna `in_revisione` |
| CA-21 | 1 | in revisione senza post da rivedere → approva → post approvati, campagna attiva, riga approvazione per post |
| CA-22 | 1 | post `da_rivedere` o intervento in corso → approva → 409 |
| CA-23 | 2b | in revisione → rimanda con nota → stato invariato, etichetta, nessuna email |
| CA-24 | 2b | in revisione → respingi senza motivo o nota → 422 |
| CA-25 | 2b | in revisione → respingi `foto` con 2 foto segnate → respinta, post scartati, email con motivo, nota, 2 miniature |
| CA-26 | 2b | post → rigenera da zero → nuova versione, stessa foto, validata |
| CA-27 | 2b | post → rigenera da proposta senza testo → 422; con testo → nuova versione, stessa foto |
| CA-28 | 2b | post con 3 rigenerazioni → quarta → 409 |
| CA-29 | 2b | campagna attiva o sospesa → qualsiasi intervento → 409 |
| CA-30 | 2b | non approvata → 00:00 del giorno di inizio → scaduta, post scaduti, email |
| CA-31 | 2b | in revisione → artigiano apre → nessun post; respinta → vede motivo, nota, foto |
| CA-32 | 2b | attiva → sospendi → non pubblica finché riattiva; annulla → non pubblica più |
| CA-33 | 3 | generazione → ogni foto ha versione ritoccata e l'originale resta |
| CA-34 | 3 | foto in 2 post → ritocca per uno → cambia solo quello |
| CA-35 | 3 | 3 ritocchi → quarto → 409; scegli originale → ok senza consumare cicli |
| CA-36 | 1 | post approvato con data raggiunta → due tick → pubblicato una volta sola |
| CA-37 | 1 | post da approvare con data raggiunta → tick → non pubblicato |
| CA-38 | 1 | errore temporaneo del social ×3 → post fallito, operatore avvisato |
| CA-39 | 1 | attiva → tutti i post pubblicati o falliti → conclusa |
| CA-40 | 3 | account assente o permesso scaduto → prima pubblicazione → sospesa + avvisi |
| CA-41 | 3 | campagne in stati diversi → pagina artigiano → ognuna nella sezione giusta (§4) |
| CA-42 | 3 | in revisione, inizio tra < 48 h → tick orario → un promemoria, una volta |
| CA-43 | 3 | nome diverso tra anagrafica e profilo → pagina artigiano → differenza segnalata |
| CA-44 | 4 | post pubblicato → lettura giornaliera → metriche salvate e visibili |
| CA-45 | 4 | sistema completo → invio e approvazione → post pubblicati (E2E nel browser) |
