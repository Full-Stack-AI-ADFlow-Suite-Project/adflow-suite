# T3-901 · Stati leggibili

Screenshot a 1280 px (desktop) e a 375 px (telefono) delle pagine dell'operatore con le etichette al posto dei valori del database. Il browser è Chromium (Playwright); `/api/` è simulato con i dati di esempio del frontend (`src/api/esempi/`), che hanno la forma degli schemi del backend: non è il backend vero.

| Immagine | Cosa mostra |
|---|---|
| `da-approvare-desktop.png`, `da-approvare-telefono.png` | Campagne da approvare: badge «Preparazione non riuscita», «Piano da rivedere», «Da rivedere», «L'AI la prepara»; la riga «Stati mostrati» con le etichette |
| `da-approvare-filtro-aperto-desktop.png` | Il filtro per stato: si legge l'etichetta («In coda (0)», «Da rivedere (3)»…) |
| `da-approvare-spiegazione-desktop.png` | La spiegazione di un badge al passaggio del mouse |
| `vedi-campagna-in-revisione-desktop.png`, `…-telefono.png`, `vedi-campagna-testata-in-revisione-desktop.png` | Vedi campagna in revisione (campagna 12 post): badge «Da rivedere», contatori «12 da approvare» e «1 da rivedere», post con le etichette del §1.1 |
| `vedi-campagna-attiva-desktop.png`, `vedi-campagna-testata-attiva-desktop.png`, `vedi-campagna-post-attiva-desktop.png` | Vedi campagna attiva: «In pubblicazione», post «In programma», «Pubblicato», «Non pubblicato» |
| `campagne-dell-operatore-desktop.png`, `…-telefono.png` | Campagne di un artigiano dell'operatore: «In pubblicazione», «Da rivedere», «Scaduta», «Conclusa», «Respinta» |
| `calendario-operatore-desktop.png`, `…-telefono.png` | Calendario settimanale dell'operatore con le etichette dei post |
| `calendario-artigiano-desktop.png`, `campagne-artigiano-desktop.png` | Le pagine dell'artigiano: restano le sue etichette di oggi |

## Controllo dei valori con il trattino basso

Un controllo automatico ha letto il testo visibile (più `title` e `aria-label`) di 42 pagine dell'operatore, tra cui Vedi campagna per ognuna delle 13 campagne di esempio (tutti gli stati del §1.1), Da approvare, Artigiani, campagne e archivio di 4 artigiani, calendario di 4 settimane e Storico AI. Nessuno stato compare come valore del database (`in_revisione`, `da_approvare`, `attiva`…).

Restano due altri tipi di identificatore con il trattino basso, che non sono stati e fuori dal perimetro di T3-901:
- il codice della regola del validatore nei blocchi e negli avvisi del post, per esempio «Blocco (max_hashtag)» e «(prezzi_o_premi)» in `PostCard.tsx` e `StoricoVersioni.tsx`;
- i nomi dei prompt nel filtro «Versione del prompt» dello Storico AI, per esempio `piano_v2`.

Osservazione, non toccata: il filtro per stato di Da approvare all'apertura appare vuoto, perché `stato` parte da `null` e l'opzione «Stato: tutti» ha valore `""`. Il comportamento è identico a prima della corsia 9.
