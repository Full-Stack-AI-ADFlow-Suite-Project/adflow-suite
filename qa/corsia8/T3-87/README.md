# T3-87 — Stato della verifica della Corsia 8

**NON COMPLETATA.** Questo registro distingue verifiche osservate, preparazione e prove mancanti. Non certifica i passi 1–9 della demo e non chiude task.

## Codice su GitHub

| Task | Riferimento | Stato |
|---|---|---|
| T3-83 | [PR142](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/142), edbf8196 | Draft, codice e allegati pubblicati |
| T3-84 | [PR143](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/143),54958e95 | Draft, inventario194frammenti/35file pubblicato |
| T3-85 | [branch](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/tree/feature/T3-85-layout-telefono),9a7b21ba | Codice pubblicato, revisione e68 screenshot in questa raccolta; creazionePR interrotta dal browser |
| T3-86 | [protocollo](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/blob/feature/T3-86-prova-persone/qa/corsia8/T3-86/protocollo-prova.md),84103d96 | Preparato, NON ESEGUITO |

Pila dei branch: T3-83→main, T3-84→T3-83, T3-85→T3-84, T3-86→T3-85. Nessun merge su main; l’admin integra nell’ordine. Il protocollo richiede le modifiche già su main prima delle due sessioni reali.

## Evidenze osservate

- Lint/build/Prettier e diff-check del frontend: PASS nei singoli task. Solo avviso preesistente bundle>500kB.
- T3-84: confronto AST/HTML privo di modifiche funzionali e21testi fissi invariati per file. T3-85: confronto AST22TSX, sole props visive e menu consentito;21testi fissi invariati. Le righe della guardia testuale§1.5 intercettate per formattazione/props sono spiegate nelle PR e nella revisione.
- T3-83: statiche32prima+32dopo e app22prima+22dopo allegate allaPR142, contrasto verificato e focus tastiera visibile.
- T3-85: [68 screenshot](../T3-85/screenshots), [misureDOM](../T3-85/report-browser.json), [metodo e limiti](../T3-85/README.md), [revisione indipendente](../T3-85/revisione.md). Dati dimostrativi VITE_USA_ESEMPI=1; viewport effettiva375/1280 verificata per ogni scatto; operatore1280. Non equivalgono alla prova integrata con API/provider reali.
- NumberInput Profilo1 corretto dopo findingP2: input46px, contenitore88×44 con due target44×44 affiancati; campo seguente separato. Incremento20→21 e decremento21→20 osservati. Escape daBurger chiude il menu e restituisce il focus; voci/ordine invariati.
- GitHub Actions PR142: [Frontend205](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/actions/runs/40410692677) e [Backend234](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/actions/runs/40410692669): completed/success. PR143: [Frontend206](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/actions/runs/40411382852) e [Backend235](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/actions/runs/40411382862): completed/success. Backendworkflow usaPostgreSQL16, migrazioni, pytest eblack. Questi esiti CI non sono un test manuale della demo.

## Matrice converge§4 — stato effettivo

| Passo | Evidenza | Restante |
|---|---|---|
|1 — nuovo artigiano/accesso/profilo | UI con fixture fotografata | Creazione account e accesso con API/database reali |
|2 — campagna7giorni, foto e dichiarazione | UI passi10–12, riepilogo e blocco invio senza dichiarazione osservati | Flusso completo7giorni/3foto reali e invio con API |
|3 — generazione/costi | UI post,costo e dicituraAI con fixture | GenerazioneAI vera e verifica risultati |
|4 — revisione/richiesta/risposta | Schermate richiesta eVedi campagna con fixture | Due finestre con richiesta, caricamento, risposta e approvazione reali |
|5 — pubblicazione | Nessuna pubblicazione eseguita | Meta pagina di prova, worker, formato/orientamento/GPS |
|6 — dopo approvazione/sospensione | Solo viste/stati dimostrativi | Modifica/sposta/annulla/sospendi/riattiva con API |
|7 — confronto visivo | TemaPR142 e layout68 screenshot | Confronto finale con backend e statiche dopoT3-85 |
|8 — respinta | Disponibili stati dimostrativi | Rifiuto con motivo e foto segnate su API |
|9 — negative | CIbackend verde sulle prime2PR | Percorso manuale completo dei casi previsti |

## Blocchi e azioni necessarie

1. Integrare i task UI tramite review/admin; completare le evidenze prima di spuntare le caselle.
2. Eseguire T3-86 con due persone reali, sul proprio telefono,30min, con le PR già su main; raccogliere osservazioni autentiche e applicare solo le correzioni consentite. Nessuna sessione è stata simulata.
3. Predisporre ambiente/API/database della demo e svolgere il percorso1–9 conAI eMeta di prova come previsto da converge. Il [tentativo locale backend](backend-locale.md) non ha prodotto alcun test/server/database: non lo si presenta comePASS. Nessuna chiamata reale aAI/Meta/email è stata effettuata.
4. Completare PRdelayout e protocollo: il caricamento allegato nel browser si è bloccato; il successivo controllo computer è stato fermato perché non riusciva a determinare con sicurezza l’URL corrente suWindows. Codice e prove sono quindi pubblicati tramiteGit.

T3-86 eT3-87 restano aperti. Anche83–85 non vengono dichiarati formalmente conclusi contro il loro Fattoquando: codice pronto e verifiche documentate non sostituiscono i passaggi mancanti.

Rettifica immagini:68 screenshot validi (21prima375 e47dopo), anziché94. Le26catture prima1280 duplicavano la scheda attiva e sono escluse dal confronto; prima desktop da rifare. La verifica non è completa.
