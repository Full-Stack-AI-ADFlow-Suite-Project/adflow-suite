"""La privacy: sfocatura forte delle zone che l'operatore ha deciso di oscurare (ADR-124, RT-18).

Passo 4 dell'esecutore, subito dopo la rotazione di 90° e prima del raddrizzamento: le
coordinate sono quelle dell'originale (nessuna conversione dalla geometria fine) e la
sfocatura segue la foto in tutti i passi dopo. Ogni zona è ``{"b": [x, y, larghezza,
altezza], ...}`` con i valori in centesimi della foto (0–100), nel riferimento dopo EXIF e
sRGB; ``"attiva": False`` la salta. Una zona malformata **non si ignora**: sbaglia il
render, perché non pubblicare è meglio che pubblicare un volto o una targa scoperti.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, Final

from PIL import Image, ImageFilter

from app.core.errori import DatiNonValidi

from .geometria import Mappa

MARGINE: Final[float] = 0.15  # in più su ogni lato, in quota della zona
BLOCCHI: Final[int] = 6  # la zona si riduce a ~6 blocchi per lato prima di sfocare
RAGGIO_QUOTA: Final[
    float
] = 0.25  # raggio della sfocatura, in quota del lato lungo della zona
RAGGIO_MIN: Final[float] = 6.0


def zona_a_box(zona: Any) -> dict[str, float] | None:
    """Il riquadro normalizzato di una zona attiva; ``None`` se è spenta.

    Raises:
        DatiNonValidi: la zona non ha un ``b`` fatto di quattro numeri in 0–100 con una
            larghezza e un'altezza vere.
    """
    if not isinstance(zona, dict):
        raise DatiNonValidi("Zona di privacy non valida.")
    if zona.get("attiva") is False:
        return None
    b = zona.get("b")
    if (
        not isinstance(b, (list, tuple))
        or len(b) != 4
        or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in b)
    ):
        raise DatiNonValidi("Zona di privacy non valida.")
    x, y, w, h = (float(v) for v in b)
    if not (0 <= x <= 100 and 0 <= y <= 100 and 0 < w <= 100 and 0 < h <= 100):
        raise DatiNonValidi("Zona di privacy fuori dalla foto.")
    return {
        "x": x / 100.0,
        "y": y / 100.0,
        "larghezza": w / 100.0,
        "altezza": h / 100.0,
    }


def _con_margine(box: dict[str, float]) -> dict[str, float]:
    mx, my = box["larghezza"] * MARGINE, box["altezza"] * MARGINE
    x0, y0 = max(0.0, box["x"] - mx), max(0.0, box["y"] - my)
    x1, y1 = min(1.0, box["x"] + box["larghezza"] + mx), min(
        1.0, box["y"] + box["altezza"] + my
    )
    return {"x": x0, "y": y0, "larghezza": x1 - x0, "altezza": y1 - y0}


def _oscura(img: Image.Image, riquadro: tuple[int, int, int, int]) -> None:
    """Pixelatura a pochi blocchi e poi sfocatura forte, sul posto: nessun dettaglio sopravvive."""
    x0, y0, x1, y1 = riquadro
    larghezza, altezza = x1 - x0, y1 - y0
    lato = max(larghezza, altezza)
    zona = img.crop(riquadro)
    blocco = max(2, lato // BLOCCHI)
    piccola = zona.resize(
        (max(1, larghezza // blocco), max(1, altezza // blocco)), Image.Resampling.BOX
    )
    grande = piccola.resize((larghezza, altezza), Image.Resampling.BICUBIC)
    sfocata = grande.filter(
        ImageFilter.GaussianBlur(max(RAGGIO_MIN, RAGGIO_QUOTA * lato))
    )
    img.paste(sfocata, (x0, y0))


def oscura_zone(img: Image.Image, zone: Sequence[Any], mappa: Mappa) -> Image.Image:
    """Oscura le zone attive: restituisce ``img`` (la stessa, modificata sul posto)."""
    larghezza, altezza = img.size
    for zona in zone:
        box = zona_a_box(zona)
        if box is None:
            continue
        mappato = mappa.box_norm(_con_margine(box))
        if mappato is None:
            continue  # la zona è finita fuori dalla foto
        riquadro = (
            max(0, int(mappato["x"] * larghezza)),
            max(0, int(mappato["y"] * altezza)),
            min(
                larghezza, math.ceil((mappato["x"] + mappato["larghezza"]) * larghezza)
            ),
            min(altezza, math.ceil((mappato["y"] + mappato["altezza"]) * altezza)),
        )
        if riquadro[2] - riquadro[0] >= 1 and riquadro[3] - riquadro[1] >= 1:
            _oscura(img, riquadro)
    return img
