"""Il prompt delle immagini AI di rimpiazzo (spec R-43, brief-ai T3-34).

Lo scrive il codice, non l'AI: parte dalla fotografia del profilo, dal tema
dell'uscita e dalla data del post. Il file ``prompts/immagine_v2.md`` ha il
testo; la riga di stagione e quella di tono si tolgono nella versione
semplice, per la seconda prova dopo un rifiuto (R-35).
"""

from collections.abc import Mapping
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

VERSIONE_PROMPT = "immagine_v2"
_FILE = Path(__file__).parent / "prompts" / f"{VERSIONE_PROMPT}.md"
# Righe del prompt che la versione semplice non ha.
_RIGHE_FACOLTATIVE = ("{stagione}", "{tono}")
_MAX_TEMA = 200

_STAGIONI = {
    12: "inverno",
    1: "inverno",
    2: "inverno",
    3: "primavera",
    4: "primavera",
    5: "primavera",
    6: "estate",
    7: "estate",
    8: "estate",
    9: "autunno",
    10: "autunno",
    11: "autunno",
}


@lru_cache
def _testo() -> str:
    return _FILE.read_text(encoding="utf-8")


def _tipo_prodotto(valore: Any) -> str:
    """``ceramica_vetro`` come «ceramica e vetro»; senza tipo, prodotti artigianali."""
    if not isinstance(valore, str) or valore in ("", "altro"):
        return "prodotti artigianali"
    return valore.replace("_", " e ")


def prompt_immagine(
    snapshot: Mapping[str, Any],
    tema: str,
    giorno: date,
    *,
    semplice: bool = False,
) -> str:
    """Il prompt dell'immagine di un'uscita.

    ``snapshot`` è la fotografia del profilo salvata all'invio; ``giorno`` è
    la data del post, che dà la stagione. Con ``semplice`` mancano stagione e
    tono.
    """
    citta = snapshot.get("citta")
    tono = snapshot.get("tono")
    valori = {
        "tipo_prodotto": _tipo_prodotto(snapshot.get("tipo_prodotto")),
        "luogo": f" a {citta}" if isinstance(citta, str) and citta.strip() else "",
        "tema": " ".join(tema.split())[:_MAX_TEMA],
        "stagione": _STAGIONI[giorno.month],
        "tono": ", ".join(tono) if isinstance(tono, list) else "",
    }
    righe = []
    for riga in _testo().strip().splitlines():
        facoltativa = any(segno in riga for segno in _RIGHE_FACOLTATIVE)
        if facoltativa and (semplice or ("{tono}" in riga and not valori["tono"])):
            continue
        righe.append(riga.format(**valori))
    return "\n".join(righe)
