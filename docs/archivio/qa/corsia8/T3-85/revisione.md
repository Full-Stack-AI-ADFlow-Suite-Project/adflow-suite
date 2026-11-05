# T3-85 - Revisione indipendente aggiornata

Esaminati il commit originale `524c219448c3cbb28f8b1634e3f259d4cd2fd587` e il solo delta correttivo `9a7b21ba8d30e7ecf9fdb75eae889bbb74a550f4`, su base T3-84 `54958e9538a05155623c3df4ac8c451cb067c713`. Checkout pulita. Nessuna modifica al prodotto; questo report è l'unico file scritto dal revisore.

Letti brief-interfaccia §1, §4 S1/S2/S3 e §T3-85, costituzione, perimetro MVP blocco I e AGENTS. Esaminati diff completo originale, report implementatore e sorgenti locali Mantine necessari ai selettori. Nel secondo passaggio esaminati esclusivamente i due file del fix. Non ripetuti lint/build/Prettier/AST/testi fissi già documentati PASS; nessun browser, CUA/CDP, credenziale, server QA, push o merge usato dal revisore.

## Findings prioritari attuali

**Nessun finding P0/P1/P2/P3 aperto nel codice esaminato.** Il P2 originale è risolto; dettagli ed evidenza sotto. Restano distinti i limiti di verifica e i requisiti di completamento del task.

### P2 originale chiuso - NumberInput mobile

La regola `frontend/src/components/Guscio.module.css:248-250` applicava il target 44x44 anche ai due UnstyledButton interni del NumberInput del Profilo passo 1 (`Profilo.tsx:310`), impilati da Mantine in un contenitore alto 34px e largo circa 24px. La causa era verificabile nei sorgenti locali Mantine.

Il fix aggiunge un layout specifico sotto 47.99em: wrapper/input alto 46px, sezione destra riservata di 90px, contenitore stepper 88x44px e due controlli affiancati da 44x44px. Non ritaglia i pulsanti con overflow:hidden e non cambia handler, campi o condizioni. Le variabili CSS risolvono anche lo spazio del testo dentro il campo. Il layout desktop resta fuori dalla media query.

**Evidenza browser comunicata dal controller, non eseguita dal revisore:** input alto 46px; contenitore 88x44; entrambi gli stepper 44x44 a x237.2/281.2, y663.9, terminanti a y707.9; etichetta del campo Sito a y726.5, quindi separata. Incremento 20→21 e decremento 21→20 riusciti. Font 16px e nessuno scroll orizzontale nel Profilo passo 1. Screenshot: `work/qa-t385/profilo1-fix-375.png`. Il controller riferisce inoltre Profilo passi 2-9 acquisiti a 375/1280 senza overflow e senza pulsanti mobile sotto 44px.

### Escape dal Burger - fix verificato

Il nuovo `onKeyDown` su `aside` in `frontend/src/components/Guscio.tsx:184` estende lo stesso handler visuale già esistente al Burger, oltre che a nav e piede. Chiude soltanto il menu e restituisce il focus al primo button dell'aside, che nell'ordine corrente è il Burger. Voci, link, ordine ed Esci restano invariati. Rientra nell'eccezione del menu puramente visivo, senza nuovi dati o chiamate.

**Evidenza browser comunicata dal controller:** dopo apertura dal Burger, Escape imposta aria-expanded=false e mantiene/restituisce il focus al pulsante «Menu di navigazione». Nessun ulteriore finding nel delta.

## SPEC - esito separato

- Perimetro rispettato: solo TSX esistenti e CSS, nessuna dipendenza/backend/API/logica di dominio; CSS statico modificato soltanto mediante nuovi @media, HTML e script invariati.
- Burger/useDisclosure corretti per l'eccezione ammessa; voci, ordine, destinazioni e handler funzionali preesistenti conservati. Menu chiuso escluso da focus/lettura con display:none.
- Presentazione coerente con padding mobile, azioni impilate, richiesta prioritaria, rimozione foto 44px, anteprima flessibile, densità operatore e colori distruttivi/blocco approvati. I submit restano nei rispettivi form/componenti.
- Guardia testuale §1.5: le righe con handler immutati sono spiegate nel report implementatore e coperte dal confronto AST documentato. Il brief ammette questa spiegazione; il grep non vuoto non è autonomamente un finding.
- AST dei 22 TSX e conteggio dei 21 testi fissi assunti dalle verifiche documentate, senza ripetizione. Diff senza cambi funzionali esterni al menu visuale.
- Breakpoint 860px della cornice e 47.99em dei controlli distinti per scopo: nessuna violazione dedotta dalla sola differenza, dato il requisito 375/1280.

**SPEC del codice: nessun blocco residuo rilevato dopo il fix.** La certificazione completa del Fatto quando dipende ancora dalle evidenze complessive del controller per tutto S2: menu dei due ruoli, Accesso, Ingresso, Campagna/stati/richiesta, Profilo, Campagne, Archivio, Calendario e operatore 1280, oltre a screenshot/converge richiesti. Non estendere il PASS mirato del Profilo all'intero percorso.

## QUALITÀ - esito separato

**PASS della revisione statica dopo il fix, con i limiti sotto.** Modifica contenuta e leggibile; riuso CSS senza duplicare componenti. Il fix risolve la collisione fra target generico e controllo composto mediante geometria esplicita coerente, senza cambiare comportamento funzionale. Escape copre anche l'origine di apertura del menu.

Limiti: il revisore non ha misurato direttamente geometria/clipping di tutti i controlli composti, font effettivi/default browser, tastiera/focus in tutte le pagine, dati lunghi, console o percorso backend. Le evidenze browser sopra sono attribuite al controller. I selettori Input sono validi nella versione installata: Input genera sia il proprio nome statico sia quello del derivato; PasswordInput e PillsInput ereditano il font. Nessun falso finding per presunta mancata copertura font.

## Readiness

**Draft: sì. Revisione codice: nessun finding aperto.** Il passaggio fuori Draft e la chiusura della casella T3-85 richiedono che il controller completi e colleghi le evidenze browser/converge del task; il solo controllo statico non attesta l'intero Fatto quando.

Destinazione autorizzata: pila T3-83 → main, T3-84 → T3-83, T3-85 → T3-84. Nessun merge su main richiesto/eseguito dal revisore e nessuna approvazione manuale simulata.
