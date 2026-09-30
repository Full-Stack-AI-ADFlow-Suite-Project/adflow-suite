# Strumenti per i diagrammi

`AdFlow-diagrammi.html` è la sorgente dei diagrammi (HTML + connettori disegnati da script). Dopo averlo modificato, da `docs/appunti/architettura`:

```
node strumenti/render-diagrammi.mjs          # rigenera diagrammi/*.png (tutti, oppure: d01,d09)
python strumenti/incorpora-png.py            # aggiorna i PNG incorporati nei pulsanti "Scarica PNG"
```

Serve Chrome installato (percorso standard di Windows, oppure variabile `CHROME`) e Node 22 o successivo. Se un connettore punta a un id che non esiste, il primo script lo segnala.
