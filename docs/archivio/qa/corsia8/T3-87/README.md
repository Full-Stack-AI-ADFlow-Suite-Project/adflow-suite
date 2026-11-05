# T3-87 — Verifica della Corsia 8

Data: 27 ottobre 2026. Codice verificato: 9a7b21ba8d30e7ecf9fdb75eae889bbb74a550f4 (T3-83 + T3-84 + T3-85). **Task aperto:** le verifiche tecniche sottostanti sono osservate; la demo completa di converge §4 e le due sessioni T3-86 non sono certificate.

## Codice e PR

| Task  | PR                                                                                  | Contenuto                                       |
| ----- | ----------------------------------------------------------------------------------- | ----------------------------------------------- |
| T3-83 | [#142](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/142) | Tema bosco/avorio, componenti, statiche e focus |
| T3-84 | [#143](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/143) | Inventario e riscrittura dei testi              |
| T3-85 | [#144](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/144) | Layout, telefono e gerarchia delle azioni       |
| T3-86 | [#145](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/145) | Protocollo per due persone, non ancora eseguito |

Questa PR contiene soltanto evidenze QA. I branch restano piccoli e collegati nell’ordine 83 → 84 → 85 → 86 → 87; nessun merge su main. Nessun file del prodotto/backend/API o test esistente modificato per far passare i controlli. Le caselle rimangono aperte se mancano i rispettivi criteri.

## Risultati osservati

| Verifica                                           | Risultato ed evidenza                                                                                                                                                                                                                               |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CI backend PR #144                                 | **1854 passed in 65.39s**; migrazioni e Black verdi. [Job](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/actions/runs/40419004746/job/121908396296)                                                                            |
| CI frontend PR #144                                | Verde. [Job](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/actions/runs/40419004737/job/121908396241)                                                                                                                          |
| Migrazioni locali                                  | Upgrade 001–012 riuscito su un cluster PostgreSQL 18 creato appositamente per QA                                                                                                                                                                    |
| Black locale                                       | 221 file invariati, exit 0                                                                                                                                                                                                                          |
| Suite locale, prima esecuzione                     | 1826 passati; 5 falliti e 23 errori nelle precondizioni che impongono nome DB/porta. [Log](pytest-prima-esecuzione.txt)                                                                                                                             |
| Ripresa dei casi compatibili con l’istanza isolata | 24 passati, exit 0; 4 casi con porta 5432 obbligatoria non riprovati localmente. [Log](pytest-ripresa.txt)                                                                                                                                          |
| HTTP su Uvicorn e PostgreSQL reali                 | **26 verifiche riuscite**, con cookie/sessioni effettivi e dati fittizi. [Risultati](verifiche-http.json)                                                                                                                                           |
| Worker locale                                      | Job letti dalla coda PostgreSQL: campagna da inviata a in_revisione; 6 post, 3 per canale, con dicitura AI. AI/social finti, email in memoria                                                                                                       |
| Frontend: struttura e testi fissi                  | Confronti AST e testi fissi già verificati nei task 83–85; revisione indipendente del layout favorevole dopo i fix                                                                                                                                  |
| Prove visive disponibili                           | [Evidenze separate](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/tree/evidence/corsia8-20261026/qa/corsia8): tema nella PR #142; layout con 68 screenshot validi (21 prima a 375 e 47 dopo a 375/1280), con limiti dichiarati |

Le 26 verifiche HTTP coprono accesso, sessione, nuovo artigiano/password provvisoria/primo profilo, duplicato 409, separazione dei ruoli, data e durata non valide, nuova campagna di 7 giorni, blocco senza dichiarazione, invio accettato nel database di prova, generazione del worker, richiesta dell’operatore, lettura e risposta dell’artigiano, approvazione, sospensione e riattivazione, rigenerazione non consentita dopo l’approvazione. Il controllo con payload incompleto è registrato separatamente dal rifiuto per stato: un 422 di schema non viene confuso con il 409 funzionale.

## Ambiente locale e limiti

Il cluster temporaneo è nella directory di lavoro QA e ascolta soltanto su 127.0.0.1:55438; il database normale sulla 5432 non è stato modificato. API su 127.0.0.1:8018. Seed: tre account fittizi; l’artigiano aggiunto via API appartiene allo stesso database QA. Nessuna credenziale, cookie o password è salvata in questi risultati.

La prima esecuzione usava adflow_corsia8_qa_test. Alcuni test, oltre alla guardia generale \*\_test, impongono esattamente adflow_test. Per la ripresa è stato creato quel nome **nel cluster QA sulla porta 55438**, senza usare l’omonimo database abituale sulla 5432. I 24 casi allora sono passati. I 4 rimanenti richiedono anche host locale e porta 5432 già occupata; non sono stati aggirati né cambiati. La suite completa della stessa modifica è verde in CI, con PostgreSQL 16 e porta 5432.

Per le prove automatiche valgono AI_PROVIDER=finto e SOCIAL_PROVIDER=finto; il worker aggiuntivo usa EmailFinto tramite il punto di sostituzione già previsto dal progetto. Nessuna richiesta reale ad AI, Meta o email. Questi risultati **non equivalgono** a generazione AI vera, pubblicazione su Facebook/Instagram, controllo di foto vere o prova d’uso con persone.

## Percorso completo ancora da eseguire

La [mappa dei test esistenti](mappa-test.md) associa tutti i 9 passi di converge §4 a CA, file e nomi concreti, separando ciò che il backend prova da ciò che richiede osservazione reale. Non attribuisce ai test automatici le verifiche visive o sui servizi live. La [checklist della demo](checklist-demo.md) conserva le attività residue.

- T3-86: due persone reali, 30 minuti sul proprio telefono, con le PR già su main, come richiede il brief. Il protocollo ha schede vuote e domande aperte; nessuna osservazione inventata.
- T3-87: percorso 1–9 in due finestre, foto vere, AI e Meta di prova, confronto finale tra app e statiche aggiornate.
- Confronto desktop prima/dopo del layout:26 catture duplicate sono state individuate ed escluse, non considerate prove valide; le catture precedenti a 1280 sono da rifare.
- Browser: in questa ripresa il browser integrato non è disponibile. La pubblicazione delle PR è riuscita tramite l’autenticazione Git già configurata; non si dichiara una verifica browser ulteriore.

La sola presenza di una PR o di un protocollo non chiude i task. L’admin mantiene il controllo dell’integrazione.

I log allegati sono normalizzati soltanto negli a capo e negli spazi finali; esiti e messaggi restano invariati.
