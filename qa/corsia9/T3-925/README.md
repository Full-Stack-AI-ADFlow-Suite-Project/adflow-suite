# T3-925 · Prova dei prompt v3

Generazione **vera** (OpenRouter: `gpt-4o` per analisi, piano e testi; `gpt-5-image-mini` per le immagini) della campagna 6, copia della campagna 4 del 28/10 (stessa bottega Ceramiche Bianchi, stessi canali, durata, 5 foto vere, 26 post). Comando, dal worktree, a worker fermo, con i social finti e l'archivio del database di sviluppo:

```bash
ARCHIVIO_FOTO_DIR=/home/giova/Dev/adflow-suite/backend/archivio_foto SOCIAL_PROVIDER=finto uv run python -m app.cli prova-prompt --da-campagna 4
```

## Numeri (v2 = campagna 4 del 28/10, v3 = campagna 6)

| Tipo | n v2 | n v3 | costo v2 | costo v3 | tempo medio v3 | errori v3 |
|---|---|---|---|---|---|---|
| analisi | 3 | 3 | 0,0255 $ | 0,0304 $ | 8,8 s | 0 |
| piano | 1 | 2 | 0,0243 $ | 0,0589 $ | 13,0 s | 0 |
| testo | 35 | 28 | 0,2012 $ | 0,1765 $ | 1,9 s | 0 |
| immagine | 8 | 8 | 0,3200 $ | 0,3200 $ | 43,2 s | 0 |
| **totale** | | | **0,5710 $** | **0,5858 $** | 459,7 s in tutto | |

Riscritture del piano 0 → 1; dei testi 9 → 2 (v2 comprende modifiche e rigenerazioni dell'operatore, quindi il confronto è indicativo). Post con blocchi o avvisi: 0 e 0. Costo totale della prova: 0,5858 $. I tempi e le versioni della v2 non esistono nel database (prima della corsia 9 non si registravano).

## Voto a mano (mio, da 1 a 5; da rivedere da una persona)

Rubrica: pertinenza alla bottega, coerenza con le foto vere (che sono mosaici), varietà tra le immagini, rispetto di R-43 (mai prodotti finiti, persone, testi). Immagini a confronto: `confronto-immagini-v2.jpg` e `confronto-immagini-v3.jpg` (numerate 1–8, file singoli in `v2/` e `v3/`). **Per versione ce ne sono 8, non 10**: la campagna ne ha 8; non ho voluto aggiungere spesa.

| Versione | Pertinenza | Coerenza con le foto | Varietà | R-43 | Note |
|---|---|---|---|---|---|
| v2 (8 immagini) | 4,0 | 2,1 | 3,0 | 4,3 | Tutte nature morte di ceramica e pennelli sul banco; i mosaici delle foto non ci sono; l'immagine 6 è un vaso decorato finito |
| v3 (8 immagini) | 4,6 | 4,1 | 4,1 | 3,8 | Tessere di mosaico, scaffali, interno, finestra di Natale: più varie e coerenti. Ma 5 (medaglioni a mosaico), 7 (pannello), 8 (mosaici e vaso) mostrano prodotti finiti: R-43 non rispettato |

Testi (10 di Facebook per versione, prime frasi, voto sulla varietà degli attacchi): v2 3,5, v3 3,5. In v3 si ripetono «Nel cuore di Deruta» (2 volte) e «Nella nostra bottega di Deruta»/«All'interno della nostra bottega»: gli attacchi non sono ancora tutti diversi.

## Conclusioni e correzioni

- Costo e tempi sono in linea con la v2 (+2,6 %); nessun errore; il piano è stato riscritto una volta.
- Le immagini v3 sono più coerenti con le foto e più varie, ma il vincolo «mai un prodotto finito» va rinforzato nel prompt dell'immagine (`immagine_v3.md`): da fare in un giro successivo, è un cambio di prompt e non l'ho toccato.
- **Corretta** una svista in `adapters/ai/litellm.py`: la chiamata del piano v3 si registrava nello Storico AI come `piano_v2`. Ora è `piano_v3`. Le due righe di piano della campagna 6 nel database di sviluppo restano con l'etichetta vecchia.
