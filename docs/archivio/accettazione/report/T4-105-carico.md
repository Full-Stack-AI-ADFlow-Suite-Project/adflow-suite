# T4-105 · Carico

Copre §7.1 e §7.2 di `accettazione-post-mvp.md`. Database **dedicato**
`adflow_accettazione` (mai `adflow` o `adflow_test`), provider finti,
`locustfile.py` in `docs/accettazione/carico/`.

## 1. Numeri ipotizzati (D-01, dichiarati come ipotesi, non misure)

| Voce | Ipotesi a 12 mesi |
|---|---|
| consorzi | 200 |
| artigiani | 2 000 |
| operatori | 8 |
| campagne al mese | 400 (≈ 13 al giorno) |
| post al giorno | 60 (≈ 2 500 al mese) |
| foto per campagna | 12 |

Obiettivi di servizio di partenza: p95 < **300 ms** per le letture, < **1 s**
per le scritture, errori < **0,1 %**, ritardo di pubblicazione < **2 minuti**.

## 2. Che cosa è stato eseguito in questa sessione

Una **prova corta** (smoke) per accertare che il locustfile funzioni e che
l'API regga il percorso misto a due ruoli:

- API in locale, `AI_PROVIDER=finto`, `SOCIAL_PROVIDER=finto`, database
  `adflow_accettazione` creato e poi rimosso;
- `uvx locust … --headless -u 5 -r 1 -t 30s --only-summary`;
- utenti misti: artigiano (campagne, profilo, canali, calendario, archivio) e
  operatore (da approvare, artigiani, Vedi campagna, storico AI).

Risultato (**70 richieste, 0 errori, 0,00 %**):

| Endpoint | Richieste | p95 (ms) | max (ms) |
|---|---|---|---|
| login | 5 | 110 | 112 |
| GET /campagne | 15 | 33 | 33 |
| GET /da-approvare | 15 | 21 | 21 |
| GET /calendario | 8 | 32 | 32 |
| GET /archivio-foto | 7 | 19 | 19 |
| GET /canali, /profilo | 10 | 18 | 18 |
| GET /storico-ai, /numeri | 6 | 33 | 33 |
| GET /artigiani | 4 | 23 | 23 |
| **aggregato** | **70** | **110** | 112 |

Le letture restano ampiamente sotto i 300 ms e le scritture (solo il login in
questa prova) sotto 1 s. Con 5 utenti e il database delle prove (decine di
righe) **non è** una prova di carico: è la verifica che lo strumento e il
percorso funzionino.

## 3. Che cosa **non** è stato eseguito (e perché)

| Prova di §7.2 | Stato | Motivo |
|---|---|---|
| Carico normale 30 minuti, utenti misti | **non provato** | la sessione non ha il tempo per 30 minuti di prova e i dati di volume non ci sono (si creano con le `fabbrica.py`, ma servono migliaia di campagne) |
| Picco 10× per 2 minuti | **non provato** | dipende dalla prova normale |
| Durata 2–8 ore | **non provato** | fuori portata di una sessione |
| 50 upload paralleli da 10 MB | **non provato** | richiede il generatore di file e il disco; il limite dei 12 MB è provato nei test (413) |
| 1000 post nello stesso minuto con Meta finto lento | **non provato** | servirebbe rallentare il finto social e osservare la coda |
| Storico AI con 100 000 chiamate | **non provato** | i dati di volume non ci sono |

I comandi per rifare tutto sono nel `README.md` della cartella `carico/`; la
prova completa è la prima cosa da mettere nel piano di correzione (RL-031).

## 4. Lettura

- Lo smoke dà fiducia sul percorso (nessun 500, nessun errore) e sui tempi a
  vuoto, ma **gli obiettivi di servizio di §8 restano `non provato`**: senza le
  prove di volume non si può dire che l'MVP li rispetti.
- Il database dedicato si crea e si rimuove in un minuto: la prova è
  ripetibile.
- Il carico va sempre lanciato con provider finti e su `adflow_accettazione`:
  il locustfile non ha difese proprie contro un host sbagliato (si fida della
  variabile `--host`).
