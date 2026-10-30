# T3-904 · Una sola Rigenera testo

Screenshot a 1280 e 375 px della finestra «Rigenera testo» in Vedi campagna (campagna in revisione, 4 post) e traffico di rete del browser per le due modalità. Il browser è Chromium (Playwright); `/api/` è simulato con i dati di esempio del frontend (`src/api/esempi/`), che hanno la forma degli schemi del backend: non è il backend vero. Il backend non cambia.

| Immagine | Cosa mostra |
|---|---|
| `azioni-post-desktop.png` | Le azioni di un post in revisione: «Modifica a mano», «Rigenera testo», «Cambia immagine», «Sposta», con «Rigenerazioni: 0 di 3» |
| `finestra-chiusa-desktop.png`, `finestra-chiusa-telefono.png` | La finestra: «Indicazioni per l'AI (facoltative)» e il link «Parti da questo testo», con il campo chiuso |
| `finestra-parti-da-testo-aperto-desktop.png` | Dopo il clic sul link: il campo «Parti da questo testo (facoltativo)» propone il testo attuale, qui con una frase aggiunta |
| `avviso-in-corso-desktop.png` | Dopo l'invio: «Intervento in corso» e «Rigenerazione del testo in corso dalle …» |

## Pulsanti

In Vedi campagna: 4 post, 4 pulsanti «Rigenera testo» (uno per post) e nessuno «Rigenera da zero» o «Rigenera da testo proposto».

## Rete del browser

Le richieste che il browser invia dalla stessa finestra (`rete-browser.json`):

| Caso | Richiesta | Corpo |
|---|---|---|
| Nessuna indicazione, «Parti da questo testo» chiuso | `POST /api/post/1301/rigenera` | `{"modalita": "totale", "testo_proposto": null, "nota": null}` |
| Indicazione e testo di partenza | `POST /api/post/1302/rigenera` | `{"modalita": "da_proposta", "testo_proposto": "Un plaid comprato oggi … Ti aspettiamo sabato in bottega.", "nota": "Più caldo, nomina il sabato."}` |
| Campo aperto e poi svuotato | `POST /api/post/1303/rigenera` | `{"modalita": "totale", "testo_proposto": null, "nota": null}` |

Quindi vuoto → `"totale"`; pieno → `"da_proposta"` con quel testo. Nessun errore in console (restano gli avvisi di React sull'annidamento `<div>` in `<p>` del riquadro del piano, già presenti prima della corsia 9).
