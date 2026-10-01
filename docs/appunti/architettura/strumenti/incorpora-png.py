"""Aggiorna i pulsanti "Scarica PNG" di AdFlow-diagrammi.html con i file attuali di diagrammi/.

Uso (da docs/appunti/architettura):  python strumenti/incorpora-png.py
"""
import base64
import re
from pathlib import Path

base = Path(__file__).resolve().parent.parent
html = base / "AdFlow-diagrammi.html"
testo = html.read_text(encoding="utf-8")

def sostituisci(m):
    nome = m.group(1)
    dati = base64.b64encode((base / "diagrammi" / nome).read_bytes()).decode()
    return f'download="{nome}" href="data:image/png;base64,{dati}"'

testo, n = re.subn(r'download="([^"]+\.png)" href="data:image/png;base64,[^"]*"', sostituisci, testo)
html.write_text(testo, encoding="utf-8")
print(f"{n} PNG incorporati in {html.name}")
