"""La luce e la nitidezza dell'esecutore: passi 8 e 9 (ADR-124, RT-17).

Le correzioni lavorano sulla foto già a lato corto 1080, in luce lineare, e conservano
la crominanza: ogni canale riceve lo stesso guadagno (esposizione, ombre, flash) oppure
guadagni che non cambiano la luminanza (bianco). Le misure si fanno nella **regione del
soggetto**, portata nel riferimento della foto di adesso; senza regione, su tutta la foto.

Il comando non porta le dosi finali ma i **tetti** e il verso: la dose la decide la
misura, fino al tetto (doppia chiave, nota 10.7: l'AI dice che c'è un difetto, la misura
dice quanto). Sotto la zona morta non si fa niente, così una foto buona esce com'è.

``luce`` del comando, tutte le chiavi facoltative::

    {"soggetto": {"x", "y", "larghezza", "altezza"},   # regione di misura, riferimento di partenza
     "esposizione": {"verso": "su"|"giu", "tetto": 0.5, "obiettivo": 55.0},
     "bianco": {"neutro": {box}|None, "soggetto": bool, "tetto": 0.05},
     "ombre": 0.25, "flash": 0.5}
"""

from __future__ import annotations

import math
from typing import Any, Final

import numpy as np
from PIL import Image, ImageFilter

from . import ritocco_catalogo as catalogo
from .preanalisi import srgb_a_lab

_REGIONE_MIN: Final[int] = 8  # pixel: sotto, la regione non dice niente

_LUT_LINEARE = np.array(
    [
        (c / 255.0) / 12.92
        if c / 255.0 <= 0.04045
        else ((c / 255.0 + 0.055) / 1.055) ** 2.4
        for c in range(256)
    ],
    dtype=np.float32,
)
_PESI_Y = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def a_lineare(rgb8: np.ndarray) -> np.ndarray:
    """Da sRGB uint8 (h, w, 3) a luce lineare float32 in 0–1."""
    return _LUT_LINEARE[rgb8]


def da_lineare(lineare: np.ndarray) -> np.ndarray:
    """Da luce lineare a sRGB uint8, con arrotondamento."""
    v = np.clip(lineare, 0.0, 1.0)
    codificato = np.where(
        v <= 0.0031308, v * 12.92, 1.055 * np.power(v, 1 / 2.4) - 0.055
    )
    return np.rint(codificato * 255.0).astype(np.uint8)


def _luminanza(lineare: np.ndarray) -> np.ndarray:
    return lineare @ _PESI_Y


def _spalla(v: np.ndarray, soglia: float = 0.8) -> np.ndarray:
    """Dopo un guadagno le alte luci non bruciano di colpo: sopra ``soglia`` la curva si ammorbidisce."""
    ammorbidita = soglia + (1.0 - soglia) * (
        1.0 - np.exp(-(v - soglia) / (1.0 - soglia))
    )
    return np.where(v > soglia, ammorbidita, v)


def regione(
    box: dict[str, float] | None, larghezza: int, altezza: int
) -> tuple[int, int, int, int]:
    """La regione di misura in pixel (x0, y0, x1, y1); tutta la foto se manca o è troppo piccola."""
    if box is not None:
        x0 = max(0, int(box["x"] * larghezza))
        y0 = max(0, int(box["y"] * altezza))
        x1 = min(larghezza, math.ceil((box["x"] + box["larghezza"]) * larghezza))
        y1 = min(altezza, math.ceil((box["y"] + box["altezza"]) * altezza))
        if x1 - x0 >= _REGIONE_MIN and y1 - y0 >= _REGIONE_MIN:
            return x0, y0, x1, y1
    return 0, 0, larghezza, altezza


# --- Le correzioni (ognuna restituisce la luce lineare corretta, o la stessa) ----------


def esposizione(
    lineare: np.ndarray, area: tuple[int, int, int, int], parametri: dict[str, Any]
) -> np.ndarray:
    """Porta la mediana di L* della regione verso l'obiettivo, nel verso detto e fino al tetto."""
    tetto = float(parametri.get("tetto", catalogo.STANDARD.esposizione_tetto_stop))
    obiettivo = float(parametri.get("obiettivo", catalogo.ESPOSIZIONE_OBIETTIVO_L))
    verso = parametri.get("verso", "su")
    x0, y0, x1, y1 = area
    campione = da_lineare(lineare[y0:y1:2, x0:x1:2])
    mediana = float(np.median(srgb_a_lab(campione)[..., 0]))

    def luminanza_di(L: float) -> float:
        return ((L + 16.0) / 116.0) ** 3 if L > 8.0 else L / 903.3

    attuale, voluta = luminanza_di(mediana), luminanza_di(obiettivo)
    if attuale <= 1e-6:
        stop = tetto if verso == "su" else 0.0
    else:
        stop = math.log2(voluta / attuale)
    if (verso == "su" and stop <= 0) or (verso == "giu" and stop >= 0):
        return lineare
    stop = max(-tetto, min(tetto, stop))
    if abs(stop) < catalogo.ZONA_MORTA_ESPOSIZIONE_STOP:
        return lineare
    corretta = lineare * np.float32(2.0**stop)
    return _spalla(corretta) if stop > 0 else corretta


def bianco(
    lineare: np.ndarray, area: tuple[int, int, int, int], parametri: dict[str, Any]
) -> np.ndarray:
    """Guadagni per canale che portano al grigio la zona neutra (o, senza, la media del soggetto)."""
    tetto = float(parametri.get("tetto", catalogo.STANDARD.bianco_tetto_canale))
    if tetto <= 0:
        return lineare
    zona = parametri.get("neutro_px")
    if zona is None:
        if not parametri.get("soggetto"):
            return lineare
        zona = area
    x0, y0, x1, y1 = zona
    medie = lineare[y0:y1, x0:x1].reshape(-1, 3).mean(axis=0)
    if float(medie.min()) <= 1e-4:
        return lineare
    guadagni = float(medie.mean()) / medie
    if float(np.abs(guadagni - 1.0).max()) < catalogo.ZONA_MORTA_BIANCO:
        return lineare
    guadagni = guadagni / float(guadagni @ _PESI_Y)  # la luminanza non cambia
    guadagni = np.clip(
        guadagni, 1.0 - tetto, 1.0 + tetto
    )  # il tetto vale per ogni canale
    return lineare * guadagni.astype(np.float32)


def ombre(lineare: np.ndarray, dose: float) -> np.ndarray:
    """Apre le ombre: un guadagno uguale per canale, forte dove la luminanza è bassa, nullo oltre il grigio medio."""
    if dose <= 0:
        return lineare
    y = _luminanza(lineare)
    # 0.18 è il grigio medio in luce lineare
    maschera = np.clip(1.0 - y / 0.18, 0.0, 1.0) ** 2
    guadagno = np.power(
        2.0, dose * catalogo.OMBRE_GUADAGNO_MAX_STOP * maschera, dtype=np.float32
    )
    return lineare * guadagno[..., None]


def flash(lineare: np.ndarray, dose: float) -> np.ndarray:
    """Compensa la caduta di luce ai bordi dei flash frontali con un guadagno radiale."""
    if dose <= 0:
        return lineare
    altezza, larghezza = lineare.shape[:2]
    y = _luminanza(lineare)
    centro = y[
        int(altezza * 0.25) : int(altezza * 0.75),
        int(larghezza * 0.25) : int(larghezza * 0.75),
    ].mean()
    bordo_h, bordo_w = max(1, int(altezza * 0.15)), max(1, int(larghezza * 0.15))
    maschera = np.ones((altezza, larghezza), dtype=bool)
    maschera[bordo_h : altezza - bordo_h, bordo_w : larghezza - bordo_w] = False
    bordi = y[maschera].mean()
    if centro <= 1e-6 or (centro - bordi) / centro < catalogo.ZONA_MORTA_FLASH:
        return lineare
    caduta = float((centro - bordi) / centro)
    massimo = min(catalogo.FLASH_GUADAGNO_MAX, 1.0 / max(1.0 - caduta, 1e-3))
    yy, xx = np.mgrid[0:altezza, 0:larghezza].astype(np.float32)
    r = np.hypot(
        (xx - larghezza / 2.0) / (larghezza / 2.0),
        (yy - altezza / 2.0) / (altezza / 2.0),
    ) / math.sqrt(2.0)
    guadagno = 1.0 + dose * (massimo - 1.0) * np.clip(r, 0.0, 1.0) ** 2
    return lineare * guadagno[..., None].astype(np.float32)


def correggi_luce(
    img: Image.Image,
    luce: dict[str, Any],
    box_soggetto: dict[str, float] | None,
    box_neutro: dict[str, float] | None,
) -> Image.Image:
    """Applica esposizione, bianco, ombre e flash, in quest'ordine, alla foto ``img`` (già a lato corto 1080).

    ``box_soggetto`` e ``box_neutro`` sono già nel riferimento di ``img`` (normalizzati).
    """
    larghezza, altezza = img.size
    lineare = a_lineare(np.asarray(img.convert("RGB"), dtype=np.uint8))
    area = regione(box_soggetto, larghezza, altezza)
    originale = lineare
    if luce.get("esposizione"):
        lineare = esposizione(lineare, area, luce["esposizione"])
    if luce.get("bianco"):
        parametri = dict(luce["bianco"])
        if box_neutro is not None:
            parametri["neutro_px"] = regione(box_neutro, larghezza, altezza)
        lineare = bianco(lineare, area, parametri)
    lineare = ombre(lineare, float(luce.get("ombre") or 0.0))
    lineare = flash(lineare, float(luce.get("flash") or 0.0))
    if lineare is originale:
        return img
    return Image.fromarray(da_lineare(lineare), "RGB")


def nitidezza(img: Image.Image, dose: float) -> Image.Image:
    """Una maschera di contrasto leggera (``UnsharpMask``): ``dose`` 0–1 sulla foto già a 1080."""
    if dose <= 0:
        return img
    percentuale = max(1, round(dose * catalogo.NITIDEZZA_PERCENTUALE_MAX))
    return img.filter(
        ImageFilter.UnsharpMask(
            radius=catalogo.NITIDEZZA_RAGGIO, percent=percentuale, threshold=2
        )
    )
