# T3-914 · Storico AI, la pagina

Screenshot a 1280 e 375 px dell'elenco con i filtri e del dettaglio di una chiamata. In questo branch la pagina usa già le API vere (`ENDPOINT_PRONTO` a `true`, T3-924): il browser è Chromium (Playwright) e `/api/storico-ai`, `/api/storico-ai/numeri` e `/api/storico-ai/{id}` sono simulati con le risposte di esempio di `src/api/esempi/storico.ts` (120 chiamate di esempio), che hanno la forma degli schemi di `contenuti/schemas.py` (§1.3): non è il backend vero. Il backend vero è provato dai test CA-110, CA-111, CA-112.

| Immagine | Cosa mostra |
|---|---|
| `elenco-desktop.png`, `elenco-telefono.png` | Filtri (campagna, tipo, modello, versione del prompt, esito, dal / al), numeri, tabella per versione del prompt e le prime righe: data, campagna e bottega, tipo, esito, modello e versione, durata, costo. Nella barra dell'operatore la voce «Storico AI» dopo Calendario e prima di «Nuovo artigiano» |
| `elenco-filtro-aperto-desktop.png` | Il filtro «Versione del prompt» aperto, con le sue opzioni (`analisi_v2`, `piano_v2`, `post_v2`, `post_v3`, `immagine_v2`, `analisi_v3`) |
| `elenco-filtrato-desktop.png` | Tipo «Immagine AI» ed esito «Risposta fuori schema»: 3 chiamate, con «Azzera i filtri» |
| `elenco-filtri-campagna-versione-periodo-desktop.png` | Campagna, versione del prompt e periodo insieme |
| `dettaglio-richiesta-chiusa-desktop.png`, `…-telefono.png` | Dettaglio di una chiamata riuscita (analisi delle foto): dati, la foto, risposta e voto; la richiesta è ripiegata |
| `dettaglio-richiesta-aperta-desktop.png`, `…-telefono.png` | La stessa chiamata con la richiesta aperta (JSON leggibile) |
| `dettaglio-errore-desktop.png`, `…-telefono.png` | Una chiamata fallita: l'errore al posto della risposta |

Filtri visti dalla rete del browser: `GET /api/storico-ai?tipo=immagine&esito=risposta&pagina=1` e `GET /api/storico-ai?versione_prompt=analisi_v2&campagna_id=11&dal=2026-10-20&al=2026-10-28&pagina=1`. Nessun errore in console (restano gli avvisi di React sull'annidamento `<div>` in `<p>` di Vedi campagna, non di questa pagina).

Numeri, tabella per versione e voto sono di T3-924: le immagini sono in `qa/corsia9/T3-924/`.
