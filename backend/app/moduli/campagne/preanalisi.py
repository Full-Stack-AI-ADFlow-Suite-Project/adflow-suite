"""La pre-analisi locale (L1): misure della foto e fasce per l'AI (ADR-124, RT-13).

``misura`` lavora sulla copia di lavoro (~2048 px, già in sRGB: ``colore.apri_in_srgb``)
e restituisce numeri; ``fatti_del_file`` legge dal file l'EXIF e la qualità del JPEG
(solo l'intestazione, non decodifica); ``fasce`` traduce i numeri in parole con le
soglie di ``ritocco_catalogo`` e tiene solo le fasce **non normali**: all'AI si dice
"scura", non "L* 21,3", e di una foto pulita non si dice niente.

Convenzioni (le stesse delle misure di tono dell'esecutore, RT-17):
- luminanza in L* (0 nero, 100 bianco), dominante come medie di a* e b* (D65);
- ``luci_bruciate`` e ``ombre_chiuse`` in percentuale di pixel (luminanza ≥ 250 e ≤ 5 su 255);
- ``angolo_linee`` in gradi, positivo se le linee dominanti scendono verso destra
  (verso il basso, con l'asse y dell'immagine che cresce in basso); la correzione di
  chi raddrizza è l'opposto.
I candidati (volti e quadrilateri) sono un altro pezzo (RT-14).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any, Final

import cv2
import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont

from . import ritocco_catalogo as catalogo

# Le misure di tono si fanno su una copia piccola: bastano e costano poco.
LATO_TONO: Final[int] = 512
# La nitidezza e le linee su una copia più grande, a lato lungo fisso: la varianza del
# Laplaciano dipende dalla risoluzione, quindi si misura sempre alla stessa scala
# (un'immagine più piccola si misura così com'è).
LATO_NITIDEZZA: Final[int] = 1024
LATO_LINEE: Final[int] = 1024
# Il centro e i bordi per la caduta di luce: il centro è il riquadro centrale della metà
# del lato; i bordi sono la cornice esterna del 15% per lato.
CENTRO: Final[float] = 0.25  # margine del riquadro centrale (0,25 → riquadro 25%–75%)
BORDO: Final[float] = 0.15
# Le linee che contano sono quasi orizzontali o verticali: oltre questi gradi dall'asse
# più vicino sono diagonali volute (tetti, scale) e non dicono niente sull'orizzonte.
LINEE_ENTRO_GRADI: Final[float] = 15.0
LINEE_LUNGHEZZA_MIN: Final[float] = 0.15  # in quota del lato lungo

_BIANCO_D65 = np.array([0.95047, 1.0, 1.08883])
_RGB_A_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)
# La tabella di quantizzazione di riferimento di libjpeg (luminanza, qualità 50).
_TABELLA_JPEG_50 = np.array(
    [16, 11, 10, 16, 24, 40, 51, 61]
    + [12, 12, 14, 19, 26, 58, 60, 55]
    + [14, 13, 16, 24, 40, 57, 69, 56]
    + [14, 17, 22, 29, 51, 87, 80, 62]
    + [18, 22, 37, 56, 68, 109, 103, 77]
    + [24, 35, 55, 64, 81, 104, 113, 92]
    + [49, 64, 78, 87, 103, 121, 120, 101]
    + [72, 92, 95, 98, 112, 100, 103, 99],
    dtype=float,
)


# --- Colore -----------------------------------------------------------------------


def srgb_a_lab(rgb: np.ndarray) -> np.ndarray:
    """Da sRGB (uint8, ..., 3) a Lab (D65, float, ..., 3)."""
    c = rgb.astype(np.float64) / 255.0
    lineare = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = (lineare @ _RGB_A_XYZ.T) / _BIANCO_D65
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack(
        [
            116.0 * f[..., 1] - 16.0,
            500.0 * (f[..., 0] - f[..., 1]),
            200.0 * (f[..., 1] - f[..., 2]),
        ],
        axis=-1,
    )


def _ridotta(img: Image.Image, lato_lungo: int) -> Image.Image:
    """Una copia con il lato lungo al massimo ``lato_lungo`` (media di area); mai più grande."""
    img = img.convert("RGB")
    massimo = max(img.size)
    if massimo <= lato_lungo:
        return img
    scala = lato_lungo / massimo
    nuova = (max(1, round(img.width * scala)), max(1, round(img.height * scala)))
    return img.resize(nuova, Image.Resampling.BOX)


def _grigio(rgb: np.ndarray) -> np.ndarray:
    """Luminanza 0–255 con i pesi Rec. 709 sui valori codificati (come la vede un istogramma)."""
    r, g, b = (rgb[..., i].astype(np.float64) for i in range(3))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# --- Le misure --------------------------------------------------------------------


def _nitidezza(img: Image.Image) -> float:
    grigio = np.asarray(_ridotta(img, LATO_NITIDEZZA).convert("L"), dtype=np.uint8)
    return float(cv2.Laplacian(grigio, cv2.CV_64F).var())


def _caduta_bordi(grigio: np.ndarray) -> float:
    """Quanto i bordi sono più scuri del centro, in quota del centro (0 se non lo sono)."""
    altezza, larghezza = grigio.shape
    y0, y1 = int(altezza * CENTRO), int(altezza * (1 - CENTRO))
    x0, x1 = int(larghezza * CENTRO), int(larghezza * (1 - CENTRO))
    by, bx = int(altezza * BORDO), int(larghezza * BORDO)
    if min(y1 - y0, x1 - x0, by, bx) < 1:
        return 0.0
    centro = grigio[y0:y1, x0:x1].mean()
    maschera = np.ones_like(grigio, dtype=bool)
    maschera[by : altezza - by, bx : larghezza - bx] = False
    bordi = grigio[maschera].mean()
    if centro < 1.0:
        return 0.0
    return float(max(0.0, (centro - bordi) / centro))


def _angolo_linee(img: Image.Image) -> float | None:
    """L'angolo dominante delle linee quasi orizzontali o verticali, in gradi (None se non ce ne sono)."""
    grigio = np.asarray(_ridotta(img, LATO_LINEE).convert("L"), dtype=np.uint8)
    lato = max(grigio.shape)
    bordi = cv2.Canny(cv2.GaussianBlur(grigio, (5, 5), 0), 50, 150)
    segmenti = cv2.HoughLinesP(
        bordi,
        rho=1,
        theta=math.pi / 720,
        threshold=max(30, lato // 20),
        minLineLength=max(20, int(lato * LINEE_LUNGHEZZA_MIN)),
        maxLineGap=max(3, lato // 100),
    )
    if segmenti is None:
        return None
    angoli, pesi = [], []
    for x1, y1, x2, y2 in segmenti[:, 0, :]:
        dx, dy = float(x2 - x1), float(y2 - y1)
        if dx < 0:
            dx, dy = -dx, -dy
        angolo = math.degrees(math.atan2(dy, dx))  # (-90, 90]
        if abs(angolo) > 45:  # quasi verticale: dall'asse verticale
            angolo -= math.copysign(90.0, angolo)
        if abs(angolo) <= LINEE_ENTRO_GRADI:
            angoli.append(angolo)
            pesi.append(math.hypot(dx, dy))
    if not angoli:
        return None
    ordine = np.argsort(angoli)
    angoli_o, pesi_o = np.asarray(angoli)[ordine], np.asarray(pesi)[ordine]
    cumulato = np.cumsum(pesi_o)
    mediano = angoli_o[int(np.searchsorted(cumulato, cumulato[-1] / 2.0))]
    return float(mediano)


def misura(img: Image.Image, dati: bytes | None = None) -> dict[str, Any]:
    """Le misure di una foto già in sRGB. Con i byte del file, anche i fatti del file.

    Numeri semplici, nelle unità del modulo (vedi sopra). Non solleva eccezioni per
    un'immagine valida; per una piccola o a tinta unita le misure che non hanno
    senso valgono 0 o ``None``.
    """
    piccola = _ridotta(img, LATO_TONO)
    rgb = np.asarray(piccola, dtype=np.uint8)
    lab = srgb_a_lab(rgb)
    luminanza = lab[..., 0]
    grigio = _grigio(rgb)
    p5, p50, p95 = (float(v) for v in np.percentile(luminanza, [5, 50, 95]))
    misure: dict[str, Any] = {
        "nitidezza": _nitidezza(img),
        "luminanza_mediana": p50,
        "percentili": {"p5": p5, "p50": p50, "p95": p95},
        "luci_bruciate": float((grigio >= 250).mean() * 100.0),
        "ombre_chiuse": float((grigio <= 5).mean() * 100.0),
        "dominante_ab": [float(lab[..., 1].mean()), float(lab[..., 2].mean())],
        "caduta_bordi": _caduta_bordi(grigio),
        "angolo_linee": _angolo_linee(img),
        "qualita_jpeg": None,
        "exif": {
            "flash": None,
            "iso": None,
            "zoom_digitale": None,
            "fotocamera": False,
            "software": None,
        },
    }
    if dati is not None:
        misure.update(fatti_del_file(dati))
    return misure


# --- I fatti del file -------------------------------------------------------------


def qualita_jpeg(tabelle: dict[int, Any] | None) -> int | None:
    """La qualità (1–100) con cui un JPEG è stato salvato, stimata dalla sua tabella di luminanza.

    La tabella di libjpeg è quella di riferimento moltiplicata per un fattore che
    dipende dalla qualità: dal rapporto medio si risale alla qualità. Le tabelle
    si confrontano in ordine crescente, così non conta in che ordine sono scritte.
    """
    if not tabelle or 0 not in tabelle:
        return None
    tabella = np.sort(np.asarray(tabelle[0], dtype=float))
    if tabella.shape != _TABELLA_JPEG_50.shape:
        return None
    fattore = 100.0 * float(np.mean(tabella / np.sort(_TABELLA_JPEG_50)))
    fattore = max(fattore, 1.0)
    qualita = 5000.0 / fattore if fattore >= 100.0 else (200.0 - fattore) / 2.0
    return int(round(min(100.0, max(1.0, qualita))))


def formato_e_colore(dati: bytes) -> dict[str, Any]:
    """Dimensioni, orientamento EXIF e profilo colore dall'intestazione del file (nessuna decodifica)."""
    vuoto: dict[str, Any] = {
        "formato": {
            "larghezza": None,
            "altezza": None,
            "rapporto": None,
            "orientamento_exif": None,
        },
        "colore": {"profilo": None, "convertito_srgb": False},
    }
    try:
        with Image.open(BytesIO(dati)) as aperta:
            larghezza, altezza = aperta.size
            orientamento = aperta.getexif().get(0x0112)
            profilo_icc = aperta.info.get("icc_profile")
            profilo = None
            if profilo_icc:
                try:
                    profilo = (
                        ImageCms.getProfileDescription(
                            ImageCms.ImageCmsProfile(BytesIO(profilo_icc))
                        ).strip()
                        or None
                    )
                except (
                    Exception
                ):  # noqa: BLE001 - un profilo rotto non ferma la pre-analisi
                    profilo = "illeggibile"
    except Exception:  # noqa: BLE001
        return vuoto
    if orientamento in (5, 6, 7, 8):  # la foto, una volta dritta, ha i lati scambiati
        larghezza, altezza = altezza, larghezza
    return {
        "formato": {
            "larghezza": larghezza,
            "altezza": altezza,
            "rapporto": round(larghezza / altezza, 4) if altezza else None,
            "orientamento_exif": int(orientamento) if orientamento else None,
        },
        "colore": {
            "profilo": profilo,
            "convertito_srgb": bool(
                profilo and profilo != "illeggibile" and "srgb" not in profilo.lower()
            ),
        },
    }


def fatti_del_file(dati: bytes) -> dict[str, Any]:
    """Qualità del JPEG ed EXIF dall'intestazione del file (nessuna decodifica dei pixel)."""
    fatti: dict[str, Any] = {
        "qualita_jpeg": None,
        "exif": {
            "flash": None,
            "iso": None,
            "zoom_digitale": None,
            "fotocamera": False,
            "software": None,
        },
    }
    try:
        with Image.open(BytesIO(dati)) as aperta:
            if aperta.format == "JPEG":
                fatti["qualita_jpeg"] = qualita_jpeg(
                    getattr(aperta, "quantization", None)
                )
            exif = aperta.getexif()
            interno = exif.get_ifd(0x8769)
    except Exception:  # noqa: BLE001 - un EXIF rotto non ferma la pre-analisi
        return fatti
    scheda = fatti["exif"]
    scheda["fotocamera"] = bool(exif.get(0x010F) or exif.get(0x0110))
    software = exif.get(0x0131)
    scheda["software"] = str(software).strip() or None if software else None
    if 0x9209 in interno:
        scheda["flash"] = bool(int(interno[0x9209]) & 1)
    iso = interno.get(0x8827)
    if isinstance(iso, (tuple, list)):
        iso = iso[0] if iso else None
    scheda["iso"] = int(iso) if isinstance(iso, (int, float)) else None
    zoom = interno.get(0xA404)
    scheda["zoom_digitale"] = float(zoom) if zoom else None
    return fatti


# --- Le fasce ---------------------------------------------------------------------


def fascia_dominante(a: float, b: float) -> str:
    """La fascia della dominante: ``nessuna`` o ``calda``/``fredda``/``verde``/``magenta``."""
    if math.hypot(a, b) < catalogo.DOMINANTE_SOGLIA:
        return "nessuna"
    asse = ("b" if abs(b) >= abs(a) else "a") + (
        "+" if (b if abs(b) >= abs(a) else a) > 0 else "-"
    )
    return catalogo.DOMINANTE_ASSI[asse]


def fasce(misure: dict[str, Any]) -> dict[str, str]:
    """Le sole fasce non normali delle misure: una foto pulita dà un dizionario vuoto."""
    tutte: dict[str, str] = {
        "nitidezza": catalogo.FASCE["nitidezza"].di(misure["nitidezza"]),
        "esposizione": catalogo.FASCE["esposizione"].di(misure["luminanza_mediana"]),
        "luci_bruciate": catalogo.FASCE["luci_bruciate"].di(misure["luci_bruciate"]),
        "ombre_chiuse": catalogo.FASCE["ombre_chiuse"].di(misure["ombre_chiuse"]),
        "dominante": fascia_dominante(*misure["dominante_ab"]),
    }
    if misure.get("qualita_jpeg") is not None:
        tutte["compressione"] = catalogo.FASCE["compressione"].di(
            misure["qualita_jpeg"]
        )
    normali = {nome: f.normali for nome, f in catalogo.FASCE.items()}
    normali["dominante"] = frozenset({"nessuna"})
    return {nome: f for nome, f in tutte.items() if f not in normali[nome]}


# --- I candidati: volti e quadrilateri ---------------------------------------------
# Il programma propone, l'AI conferma o scarta citando i codici (``V1``, ``Q1``...):
# un candidato si congela con l'analisi, quindi ``V2`` resta quel volto per sempre.
# Le coordinate sono normalizzate (0–1) sulla copia di lavoro.

LATO_CANDIDATI: Final[int] = 1024
MAX_VOLTI: Final[int] = 12
MAX_QUADRILATERI: Final[int] = 3
AREA_QUADRILATERO_MIN: Final[float] = 0.05  # in quota della foto
AREA_QUADRILATERO_MAX: Final[float] = 0.97  # oltre, è la cornice della foto
ANGOLO_QUADRILATERO: Final[tuple[float, float]] = (60.0, 120.0)  # gradi interni ammessi
SOVRAPPOSIZIONE_MAX: Final[float] = 0.3  # IoU oltre cui due volti sono lo stesso
PREFISSO_VOLTO: Final[str] = "V"
PREFISSO_QUADRILATERO: Final[str] = "Q"

# Un volto candidato: (x, y, larghezza, altezza) normalizzati e affidabilità 0–1.
Volto = tuple[float, float, float, float, float]
Rilevatore = Callable[[Image.Image], Sequence[Volto]]


def _iou(a: Volto, b: Volto) -> float:
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    larghezza = min(ax2, bx2) - max(a[0], b[0])
    altezza = min(ay2, by2) - max(a[1], b[1])
    if larghezza <= 0 or altezza <= 0:
        return 0.0
    comune = larghezza * altezza
    return comune / (a[2] * a[3] + b[2] * b[3] - comune)


def _senza_doppioni(volti: Sequence[Volto]) -> list[Volto]:
    """Soppressione dei doppioni: fra due riquadri che si sovrappongono resta il più affidabile."""
    tenuti: list[Volto] = []
    for volto in sorted(volti, key=lambda v: -v[4]):
        if all(_iou(volto, altro) <= SOVRAPPOSIZIONE_MAX for altro in tenuti):
            tenuti.append(volto)
    return tenuti


@lru_cache(maxsize=2)
def _cascata(nome: str) -> cv2.CascadeClassifier:
    cascata = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / nome))
    if cascata.empty():
        raise RuntimeError(f"Cascata di Haar non trovata: {nome}")
    return cascata


def _cerca(
    cascata: cv2.CascadeClassifier, grigio: np.ndarray, specchia: bool
) -> list[Volto]:
    altezza, larghezza = grigio.shape
    cerca_in = cv2.flip(grigio, 1) if specchia else grigio
    lato_min = max(24, min(altezza, larghezza) // 30)
    rettangoli, _, pesi = cascata.detectMultiScale3(
        cerca_in,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(lato_min, lato_min),
        outputRejectLevels=True,
    )
    trovati: list[Volto] = []
    for (x, y, w, h), peso in zip(rettangoli, np.ravel(pesi)):
        if specchia:
            x = larghezza - x - w
        affidabilita = 1.0 - math.exp(-max(float(peso), 0.0) / 3.0)
        trovati.append(
            (x / larghezza, y / altezza, w / larghezza, h / altezza, affidabilita)
        )
    return trovati


def rileva_volti_haar(img: Image.Image) -> list[Volto]:
    """I volti con le cascate di Haar di OpenCV: frontale e profilo (da entrambi i lati).

    Un rilevatore semplice, senza modelli da scaricare (D7): trova bene i volti
    frontali e grandi, meno quelli piccoli o di tre quarti. Si valuta in RT-34.
    """
    piccola = _ridotta(img, LATO_CANDIDATI)
    grigio = cv2.equalizeHist(np.asarray(piccola.convert("L"), dtype=np.uint8))
    frontale = _cascata("haarcascade_frontalface_default.xml")
    profilo = _cascata("haarcascade_profileface.xml")
    trovati = (
        _cerca(frontale, grigio, False)
        + _cerca(profilo, grigio, False)
        + _cerca(profilo, grigio, True)
    )
    return _senza_doppioni(trovati)


def _ordina_angoli(punti: np.ndarray) -> np.ndarray:
    """Alto-sinistra, alto-destra, basso-destra, basso-sinistra."""
    somma, differenza = punti.sum(axis=1), np.diff(punti, axis=1).ravel()
    return np.array(
        [
            punti[np.argmin(somma)],
            punti[np.argmin(differenza)],
            punti[np.argmax(somma)],
            punti[np.argmax(differenza)],
        ],
        dtype=np.float32,
    )


def _angoli_plausibili(angoli: np.ndarray) -> bool:
    for i in range(4):
        a, b, c = angoli[i - 1], angoli[i], angoli[(i + 1) % 4]
        v1, v2 = a - b, c - b
        coseno = float(
            np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
        )
        gradi = math.degrees(math.acos(max(-1.0, min(1.0, coseno))))
        if not ANGOLO_QUADRILATERO[0] <= gradi <= ANGOLO_QUADRILATERO[1]:
            return False
    return True


def _cerca_quadrilateri(img: Image.Image) -> list[dict[str, Any]]:
    piccola = _ridotta(img, LATO_CANDIDATI)
    grigio = np.asarray(piccola.convert("L"), dtype=np.uint8)
    altezza, larghezza = grigio.shape
    area_foto = float(altezza * larghezza)
    bordi = cv2.Canny(cv2.GaussianBlur(grigio, (5, 5), 0), 50, 150)
    bordi = cv2.dilate(bordi, np.ones((3, 3), np.uint8))
    contorni, _ = cv2.findContours(bordi, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    trovati: list[tuple[float, np.ndarray]] = []
    for contorno in contorni:
        area = cv2.contourArea(contorno)
        if (
            not AREA_QUADRILATERO_MIN * area_foto
            <= area
            <= AREA_QUADRILATERO_MAX * area_foto
        ):
            continue
        poligono = cv2.approxPolyDP(
            contorno, 0.02 * cv2.arcLength(contorno, True), True
        )
        if len(poligono) != 4 or not cv2.isContourConvex(poligono):
            continue
        angoli = _ordina_angoli(poligono.reshape(4, 2).astype(np.float32))
        if _angoli_plausibili(angoli):
            trovati.append((area, angoli))
    trovati.sort(key=lambda t: -t[0])
    scelti: list[tuple[float, np.ndarray]] = []
    for area, angoli in trovati:
        # il bordo di un oggetto dà due contorni quasi uguali (dentro e fuori): ne resta uno
        if all(
            np.abs(angoli - altri).max() > 0.03 * max(altezza, larghezza)
            for _, altri in scelti
        ):
            scelti.append((area, angoli))
        if len(scelti) == MAX_QUADRILATERI:
            break
    risultati = []
    for indice, (area, angoli) in enumerate(scelti, start=1):
        affinati = angoli.reshape(-1, 1, 2).copy()
        criterio = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
        cv2.cornerSubPix(grigio, affinati, (5, 5), (-1, -1), criterio)
        punti = affinati.reshape(4, 2)
        x0, y0, x1, y1 = (
            punti[:, 0].min(),
            punti[:, 1].min(),
            punti[:, 0].max(),
            punti[:, 1].max(),
        )
        risultati.append(
            {
                "id": f"{PREFISSO_QUADRILATERO}{indice}",
                "angoli": [
                    [float(x) / larghezza, float(y) / altezza] for x, y in punti
                ],
                "box": {
                    "x": float(x0) / larghezza,
                    "y": float(y0) / altezza,
                    "larghezza": float(x1 - x0) / larghezza,
                    "altezza": float(y1 - y0) / altezza,
                },
                "area": area / area_foto,
            }
        )
    return risultati


def candidati(
    img: Image.Image, rilevatore_volti: Rilevatore | None = None
) -> dict[str, list[dict[str, Any]]]:
    """I volti (``V1``...) e i quadrilateri (``Q1``...) che il programma propone.

    ``rilevatore_volti`` si inietta nei test (D8: nessuna foto con volti nel
    repository); senza, le cascate di Haar. I codici dipendono dalla posizione, non
    dall'ordine in cui il rilevatore li dà: da sinistra a destra, poi dall'alto.
    """
    rilevatore = rilevatore_volti or rileva_volti_haar
    volti = _senza_doppioni(list(rilevatore(img)))
    volti = sorted(
        volti, key=lambda v: (round(v[0] + v[2] / 2, 3), round(v[1] + v[3] / 2, 3))
    )
    return {
        "volti": [
            {
                "id": f"{PREFISSO_VOLTO}{i}",
                "box": {"x": x, "y": y, "larghezza": w, "altezza": h},
                "affidabilita": aff,
            }
            for i, (x, y, w, h, aff) in enumerate(volti[:MAX_VOLTI], start=1)
        ],
        "quadrilateri": _cerca_quadrilateri(img),
    }


# --- I segni sulla copia per l'AI (nota 9.6) ---------------------------------------

COLORE_SEGNI: Final[tuple[int, int, int]] = (
    255,
    0,
    255,
)  # un colore solo, ad alto contrasto


def disegna_segni(
    copia_ai: Image.Image, trovati: dict[str, list[dict[str, Any]]]
) -> Image.Image:
    """Riquadri sottili con l'etichetta sui candidati, solo se ce ne sono.

    Restituisce una copia disegnata; senza candidati, la stessa immagine. L'etichetta
    sta fuori dal riquadro (sopra, o sotto se non c'è posto).
    """
    voci: list[
        tuple[str, list[tuple[float, float]], tuple[float, float, float, float]]
    ] = []
    for volto in trovati.get("volti", []):
        b = volto["box"]
        angoli = [
            (b["x"], b["y"]),
            (b["x"] + b["larghezza"], b["y"]),
            (b["x"] + b["larghezza"], b["y"] + b["altezza"]),
            (b["x"], b["y"] + b["altezza"]),
        ]
        voci.append(
            (volto["id"], angoli, (b["x"], b["y"], b["larghezza"], b["altezza"]))
        )
    for quadro in trovati.get("quadrilateri", []):
        b = quadro["box"]
        voci.append(
            (
                quadro["id"],
                [tuple(p) for p in quadro["angoli"]],
                (b["x"], b["y"], b["larghezza"], b["altezza"]),
            )
        )
    if not voci:
        return copia_ai
    disegnata = copia_ai.convert("RGB").copy()
    pennello = ImageDraw.Draw(disegnata)
    larghezza, altezza = disegnata.size
    spessore = max(1, round(max(larghezza, altezza) / 600))
    corpo = max(10, round(max(larghezza, altezza) / 60))
    carattere = ImageFont.load_default(size=corpo)
    for etichetta, angoli, (x, y, w, h) in voci:
        punti = [(px * larghezza, py * altezza) for px, py in angoli]
        pennello.line(punti + [punti[0]], fill=COLORE_SEGNI, width=spessore)
        sinistra = x * larghezza
        sopra = y * altezza - corpo - 2
        if sopra < 0:
            sopra = (y + h) * altezza + 2
        pennello.text((sinistra, sopra), etichetta, fill=COLORE_SEGNI, font=carattere)
    return disegnata
