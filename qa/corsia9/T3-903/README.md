# T3-903 · Durata rapida al passo 10

Screenshot del passo 10 della Campagna dell'artigiano a 1280 e 375 px: stato iniziale e dopo ognuno dei tre pulsanti. Il browser è Chromium (Playwright, fuso Europe/Rome); `/api/` è simulato con i dati di esempio del frontend (`src/api/esempi/`): non è il backend vero. I campi data di Chromium senza interfaccia mostrano mm/gg/aaaa; i valori dei campi sono AAAA-MM-GG.

| Immagine | Cosa mostra |
|---|---|
| `passo10-iniziale-desktop.png`, `…-telefono.png` | I tre pulsanti accanto alle date, nessuno acceso (la durata di partenza è di 31 giorni) |
| `passo10-1-settimana-desktop.png`, `…-telefono.png` | «1 settimana»: inizio 2026-11-01, fine 2026-11-07 (7 giorni), pulsante acceso |
| `passo10-2-settimane-desktop.png`, `…-telefono.png` | «2 settimane»: fine 2026-11-14 (14 giorni) |
| `passo10-1-mese-desktop.png`, `…-telefono.png` | «1 mese»: fine 2026-11-30 (30 giorni) |

## Date, con il fuso Europe/Rome

Le date attese sono calcolate a parte, sul calendario in UTC (inizio + 6, + 13, + 29 giorni), e confrontate con il campo «Quando vuoi concludere?» dopo ogni clic. Quattro percorsi, tutti corretti (12 clic su 12, durata 7, 14 e 30 giorni, acceso solo il pulsante scelto):

| Ora del browser (Roma) | Inizio | «1 settimana» | «2 settimane» | «1 mese» |
|---|---|---|---|---|
| 28/10/2026 20:25 (ora vera) | 2026-11-01 | 2026-11-07 | 2026-11-14 | 2026-11-30 |
| 20/10/2026 10:00 | 2026-10-24 | 2026-10-30 | 2026-11-06 | 2026-11-22 |
| 30/10/2026 00:30 (in UTC ancora il 29) | 2026-11-02 | 2026-11-08 | 2026-11-15 | 2026-12-01 |

La seconda riga attraversa il cambio all'ora solare del 25/10; la terza è il caso in cui la data in UTC e quella di Roma differiscono. Il quarto percorso è la ripetizione a 375 px della prima riga.

## Accettati dal server

I corpi che il browser invia dopo «1 settimana» (`POST /api/campagne`) sono stati ripetuti sul backend vero con un test temporaneo, poi cancellato (database `adflow_test`):
- 28/10/2026, `{"inizio": "2026-11-01", "fine": "2026-11-07", …}` → 201, inizio e fine come inviati;
- gli stessi dati con fine 2026-11-06 (6 giorni) → 422 «La durata della campagna deve essere di almeno 7 giorni.»;
- le richieste delle ore 20/10 e 30/10 → `crea_bozza()` con l'ora del browser: 7 giorni, accettati.

Il confine di 7 giorni è già coperto da `test_debug_durata_minima_7_giorni_esatta` (`tests/moduli/campagne/test_api_bozza.py`).
