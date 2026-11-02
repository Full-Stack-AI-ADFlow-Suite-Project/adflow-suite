# T3-902 · Nome della bottega sulle pagine dell'artigiano

Screenshot della riga «{bottega} · {referente}» sopra il titolo, a 375 px e a 1280 px, con il menu chiuso (a 375 px la barra è nascosta dietro l'icona in alto a destra). Il browser è Chromium (Playwright); `/api/` è simulato con i dati di esempio del frontend (`src/api/esempi/`), che hanno la forma degli schemi del backend: non è il backend vero.

| Immagine | Cosa mostra |
|---|---|
| `ingresso-375px.png`, `ingresso-1280px.png` | Ingresso: «Falegnameria Bianchi · Mario Bianchi» sopra «Buongiorno, Mario» |
| `campagne-375px.png`, `campagne-1280px.png` | Campagne dell'artigiano |
| `campagna-375px.png`, `campagna-1280px.png` | Campagna |
| `calendario-375px.png`, `calendario-1280px.png` | Calendario settimanale |
| `archivio-foto-375px.png`, `archivio-foto-1280px.png` | Archivio foto |
| `profilo-bottega-375px.png`, `profilo-bottega-1280px.png` | Profilo bottega |
| `senza-profilo-375px.png` | Profilo non ancora compilato (`GET /profilo` → 404): la riga mostra solo il nome dell'utente, «Mario Bianchi» |

Per ognuna delle 12 pagine (6 pagine × 2 larghezze) lo script ha letto il testo della riga e ha verificato che sia esattamente «Falegnameria Bianchi · Mario Bianchi», che sia visibile, che la barra laterale non sia aperta e che la pagina non scorra in orizzontale: 12 su 12 corrette. A 375 px la riga sta a 90 px dall'alto, a 1280 px a 24 px.
