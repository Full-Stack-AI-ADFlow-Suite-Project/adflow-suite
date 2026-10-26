# Evidenze della corsia 8

Branch di documentazione per la revisione delle PR, da mantenere separato da main.

## T3-84

L’inventario in T3-84/inventario-testi.md riporta la tabella completa prima → dopo per 35 file e 194 occorrenze/frammenti. Sono inclusi solo testi visibili riscritti; formattazione e spazi JSX equivalenti non contano come modifiche di copy.

Le evidenze T3-83 sono allegate direttamente alla PR #142. I risultati dei controlli successivi della corsia saranno collegati alle rispettive PR. La prova con due persone reali è distinta dai controlli automatici e non viene dichiarata eseguita prima di avere le osservazioni.


## Aggiornamento finale della sessione

Layout pubblicato sul branch feature/T3-85-layout-telefono. [ProveT3-85](T3-85/README.md):68 screenshot prima/dopo con viewport375/1280 verificata e revisione. [RegistroT3-87](T3-87/README.md): stato reale di ogni passo,CI e blocchi. ProtocolloT3-86 pubblicato nel branch feature/T3-86-prova-persone. Le prove con due persone e la demo integrata non sono eseguite; nessun task viene spuntato senza evidenza.


## Aggiornamento 27 ottobre 2026

Tutti i task residui hanno una Draft PR separata: [tema #142](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/142), [testi #143](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/143), [layout #144](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/144), [protocollo persone #145](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/145), [collaudo #146](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/pull/146). Nessun merge.

Il nuovo [resoconto T3-87](https://github.com/Full-Stack-AI-ADFlow-Suite-Project/adflow-suite/blob/feature/T3-87-verifica-corsia8/qa/corsia8/T3-87/README.md) supera lo stato del tentativo locale del 26 ottobre: migrazioni riuscite su PostgreSQL isolato, Black verde, CI con1854test passati,26verifiche HTTP riuscite e worker con coda reale/provider finti. Le due persone e la demo completa live restano da eseguire; caselle aperte quando mancano i criteri.
