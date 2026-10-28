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
# Righe che mancano quando non c'è niente da dire (nota, immagini da evitare).
_RIGHE_SE_MANCANO = ("{nota}", "{da_evitare}")
_MAX_TEMA = 200
# Quanto delle immagini già avute si passa al provider, in caratteri.
_MAX_DA_EVITARE = 1200

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
    nota: str | None = None,
    da_evitare: tuple[str, ...] | list[str] = (),
) -> str:
    """Il prompt dell'immagine di un'uscita.

    ``snapshot`` è la fotografia del profilo salvata all'invio; ``giorno`` è
    la data del post, che dà la stagione. Con ``semplice`` mancano stagione e
    tono. ``nota`` è l'indicazione dell'operatore e ``da_evitare`` i prompt
    delle immagini che l'uscita ha già avuto (R-49).
    """
    citta = snapshot.get("citta")
    tono = snapshot.get("tono")
    indicazione = " ".join((nota or "").split())
    evitare = " · ".join(" ".join(uno.split()) for uno in da_evitare if uno)
    valori = {
        "tipo_prodotto": _tipo_prodotto(snapshot.get("tipo_prodotto")),
        "luogo": f" a {citta}" if isinstance(citta, str) and citta.strip() else "",
        "tema": " ".join(tema.split())[:_MAX_TEMA],
        "stagione": _STAGIONI[giorno.month],
        "tono": ", ".join(tono) if isinstance(tono, list) else "",
        "nota": indicazione,
        "da_evitare": evitare[:_MAX_DA_EVITARE],
    }
    righe = []
    for riga in _testo().strip().splitlines():
        if semplice and any(segno in riga for segno in _RIGHE_FACOLTATIVE):
            continue
        if "{tono}" in riga and not valori["tono"]:
            continue
        if any(
            segno in riga and not valori[segno.strip("{}")]
            for segno in _RIGHE_SE_MANCANO
        ):
            continue
        righe.append(riga.format(**valori))
    return "\n".join(righe)
