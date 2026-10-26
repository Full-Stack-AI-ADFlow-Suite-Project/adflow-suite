# T3-87 - Revisione finale del pacchetto evidenze

Ambito: sola lettura di `work/adflow-t387/qa/corsia8/T3-87`, riferito al prodotto SHA `9a7b21ba8d30e7ecf9fdb75eae889bbb74a550f4`. Letti README, checklist-demo, verifiche-http.json, ci-pr144.txt, mappa-test e riepiloghi dei due log pytest. Non eseguiti test, browser, CUA, Node REPL, modifiche al prodotto, DB o pubblicazioni.

**Verdetto: sì alla pubblicazione come Draft del report, includendo i due log collegati.** Il task T3-87 resta aperto e non risulta una dichiarazione di demo completa né di T3-86 eseguito.

## Unico punto concreto di confezionamento

**[P2 se omessi dalla PR] README.md:24-25 collega due file .log ignorati da Git.**

`pytest-prima-esecuzione.log` e `pytest-ripresa.log` esistono nella cartella e sono leggibili, ma `git check-ignore -v` li associa a `.gitignore:59:*.log`; al momento della revisione `git ls-files qa/corsia8/T3-87` non li elenca e l'intera cartella risulta ancora non tracciata. Con un normale git add della cartella i due log verrebbero esclusi e i link pubblicati sarebbero rotti.

Rimedio sufficiente: includerli esplicitamente nello staging con git add -f, oppure usare estensione .txt e aggiornare i due link. Non richiede modifiche al prodotto o una nuova prova. Nessun altro link relativo mancante rilevato nei documenti letti; i riferimenti ../../../docs/agenti della checklist risolvono dalla directory T3-87 alla radice del repository.

## Coerenza dei risultati

| Evidenza                        | Riscontro della revisione                                                                                                                                                                                                                                                                                           |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CI PR #144                      | ci-pr144.txt riporta SHA corretto, 1854 passed in 65.39s, Black 221 file invariati e i due job success. Il controller ha verificato i log CI originali; questa revisione non simula una seconda verifica remota.                                                                                                    |
| Prima suite locale              | Log: 5 failed, 1826 passed, 23 errors in 260.80s. La somma è 1854, coerente con la suite CI. Le guardie sul nome DB/porta sono dichiarate, non trasformate in PASS.                                                                                                                                                 |
| Ripresa locale                  | Log: 24 passed, 4 deselected in 33.34s. 24+4 corrisponde ai precedenti 5+23 casi non passati. Il README conserva i quattro casi non riprovati localmente e distingue CI verde da suite locale completa. Exit 0 e invocazione --lf sono evidenza dell'esecuzione del controller, non ricostruiti dal solo riepilogo. |
| HTTP                            | JSON con 26 elementi checks, tutti pass=true e valori actual coerenti con expected. Nessuna password/cookie/token è riportata nei risultati; la dicitura password provvisoria è solo il nome del controllo.                                                                                                         |
| Schema contro regola funzionale | I due ultimi check distinguono correttamente payload di rigenerazione incompleto → 422 da rigenerazione in stato attivo → 409. Nessun falso PASS della regola basato sul solo 422.                                                                                                                                  |
| Worker e provider               | README/JSON dichiarano worker reale/coda PostgreSQL con AI e social finti ed email in memoria; generazione in_revisione e sei post/dicitura sono coerenti. Nessun claim di pubblicazione Meta live.                                                                                                                 |
| Ambiente                        | README distingue database iniziale QA e adflow_test creato nello stesso cluster QA su 55438, API8018, PostgreSQL18; il log iniziale mostra la URL QA su55438. Nessuna evidenza letta contraddice il resoconto del controller che il DB abituale5432 non è stato toccato. La revisione non ha contattato alcun DB.   |
| Perimetro Git                   | git status mostra soltanto la nuova cartella QA; nessuna modifica al backend/prodotto/test esistente nel delta osservato.                                                                                                                                                                                           |

## Limiti dichiarati correttamente

README e checklist mantengono distinti suite/API, demo in due finestre, AI/Meta reali e confronto visivo. La checklist lascia tutti i nove passi Da compilare. La mappa dei test non presenta l'ispezione statica come esecuzione e chiarisce CA-83 via HTTP simulato, CA-91 integrato con provider finti e CA-99 come API, non screenshot.

Le due sessioni T3-86 con persone reali, 30 minuti sul proprio telefono e PR integrate su main sono esplicitamente ancora da eseguire. La mancanza del browser nella ripresa è dichiarata. Il materiale precedente con 26 catture duplicate è escluso; il limite delle catture prima a1280 mancanti è esplicito. I 68 screenshot validi indicati si ricompongono in21 prima a375 e47 dopo a375/1280: il README non li spaccia per un confronto desktop prima/dopo già completo.

Nessun nuovo requisito aggiunto dalla revisione. Il pacchetto è coerente come resoconto parziale e reviewabile; diventa pubblicabile in Draft con i due log effettivamente inclusi. La presenza della PR non chiude T3-87/T3-86 né autorizza merge su main.

Risoluzione del controller: i due log sono inclusi come .txt e i link del README sono aggiornati, così non dipendono dall’eccezione per \*.log. Nessun risultato di test è stato alterato.
