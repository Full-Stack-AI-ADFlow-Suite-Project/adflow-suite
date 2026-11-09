"""Strumenti di test per le immagini (ADR-124, RT-01 di `docs/ritocco-corsia.md`).

Tutto è sintetico: nessuna foto reale entra nel repository. Servono ai test
numerici del ritocco (colore, misure, geometria, finestra, luce, privacy), che
confrontano numeri (ΔE, medie, angoli) e mai i byte di un JPEG, perché questi
cambiano con la versione dell'encoder.

Contenuto:
- ``profilo_icc`` genera profili ICC v2 a matrice (sRGB e Display P3) dai
  primari pubblicati, con adattamento Bradford a D50 e curva sRGB;
- le immagini: tinta unita, gradiente, dominante di colore, rettangolo
  inclinato, linee inclinate, sfocata e nitida;
- i file codificati: JPEG di qualità data, con EXIF (orientamento, flash, GPS),
  PNG con ``iCCP``, WEBP con ICC, JPEG CMYK;
- ``delta_e`` (CIE76 in Lab) e ``media_lab``.
"""

from __future__ import annotations

import math
import struct
from io import BytesIO
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# --- Profili ICC ---------------------------------------------------------------

# Primari (x, y) e punto bianco D65 pubblicati dalle specifiche.
_PRIMARI = {
    "srgb": ((0.640, 0.330), (0.300, 0.600), (0.150, 0.060)),
    "p3": ((0.680, 0.320), (0.265, 0.690), (0.150, 0.060)),
}
_BIANCO_D65 = (0.3127, 0.3290)
# Bianco del PCS dell'ICC (D50), come XYZ normalizzato a Y = 1.
_D50 = np.array([0.9642, 1.0, 0.8249])

# Matrice di Bradford (cono-risposta) per adattare D65 a D50.
_BRADFORD = np.array(
    [
        [0.8951, 0.2664, -0.1614],
        [-0.7502, 1.7135, 0.0367],
        [0.0389, -0.0685, 1.0296],
    ]
)


def _xyz_da_xy(x: float, y: float) -> np.ndarray:
    return np.array([x / y, 1.0, (1.0 - x - y) / y])


def _matrice_primari_d50(nome: str) -> np.ndarray:
    """Colonne R, G, B in XYZ adattato a D50 (le tre colonne ``rXYZ``…)."""
    primari = _PRIMARI[nome]
    colonne = np.stack([_xyz_da_xy(x, y) for x, y in primari], axis=1)
    bianco = _xyz_da_xy(*_BIANCO_D65)
    scala = np.linalg.solve(colonne, bianco)
    matrice_d65 = colonne * scala
    # Adattamento cromatico Bradford: D65 -> D50.
    cono_origine = _BRADFORD @ bianco
    cono_destinazione = _BRADFORD @ _D50
    adattamento = (
        np.linalg.inv(_BRADFORD) @ np.diag(cono_destinazione / cono_origine) @ _BRADFORD
    )
    return adattamento @ matrice_d65


def _curva_srgb(punti: int = 1024) -> list[int]:
    """La curva sRGB (valori da 0 a 65535) come tabella ``curv`` dell'ICC v2."""
    uscita = []
    for i in range(punti):
        c = i / (punti - 1)
        lineare = c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        uscita.append(round(lineare * 65535))
    return uscita


def _s15f16(valore: float) -> bytes:
    return struct.pack(">i", round(valore * 65536))


def _tag_xyz(xyz) -> bytes:
    return b"XYZ \x00\x00\x00\x00" + b"".join(_s15f16(float(v)) for v in xyz)


def _tag_curva(tabella: list[int]) -> bytes:
    return (
        b"curv\x00\x00\x00\x00"
        + struct.pack(">I", len(tabella))
        + b"".join(struct.pack(">H", v) for v in tabella)
    )


def _tag_testo(testo: str) -> bytes:
    return b"text\x00\x00\x00\x00" + testo.encode("ascii") + b"\x00"


def _tag_descrizione(testo: str) -> bytes:
    ascii_ = testo.encode("ascii") + b"\x00"
    return (
        b"desc\x00\x00\x00\x00"
        + struct.pack(">I", len(ascii_))
        + ascii_
        + struct.pack(">II", 0, 0)  # Unicode: lingua e lunghezza vuote
        + struct.pack(">HB", 0, 0)  # ScriptCode: codice e lunghezza vuoti
        + bytes(67)
    )


def profilo_icc(nome: Literal["srgb", "p3"]) -> bytes:
    """Profilo ICC v2 a matrice: ``"srgb"`` o ``"p3"`` (Display P3, curva sRGB).

    Costruito dai primari pubblici, senza file esterni. Non è bit a bit quello
    ufficiale, ma LittleCMS lo legge e le conversioni tornano entro ±1.
    """
    matrice = _matrice_primari_d50(nome)
    curva = _tag_curva(_curva_srgb())
    descrizione = "sRGB sintetico" if nome == "srgb" else "Display P3 sintetico"
    tag: list[tuple[bytes, bytes]] = [
        (b"desc", _tag_descrizione(descrizione)),
        (b"cprt", _tag_testo("Dominio pubblico (profilo sintetico di test)")),
        (b"wtpt", _tag_xyz(_D50)),
        (b"rXYZ", _tag_xyz(matrice[:, 0])),
        (b"gXYZ", _tag_xyz(matrice[:, 1])),
        (b"bXYZ", _tag_xyz(matrice[:, 2])),
        (b"rTRC", curva),
        (b"gTRC", curva),
        (b"bTRC", curva),
    ]
    inizio_dati = 128 + 4 + 12 * len(tag)
    tabella = struct.pack(">I", len(tag))
    dati = b""
    for firma, contenuto in tag:
        riempimento = (-len(contenuto)) % 4
        tabella += firma + struct.pack(">II", inizio_dati + len(dati), len(contenuto))
        dati += contenuto + bytes(riempimento)
    totale = inizio_dati + len(dati)
    intestazione = (
        struct.pack(">I", totale)
        + bytes(4)  # CMM
        + struct.pack(">I", 0x02400000)  # versione 2.4.0
        + b"mntr"
        + b"RGB "
        + b"XYZ "
        + struct.pack(">6H", 2026, 11, 9, 0, 0, 0)  # data di creazione
        + b"acsp"
        + bytes(4)  # piattaforma
        + bytes(4)  # flag
        + bytes(4)  # produttore
        + bytes(4)  # modello
        + bytes(8)  # attributi
        + struct.pack(">I", 0)  # intento: percettivo
        + b"".join(_s15f16(float(v)) for v in _D50)  # illuminante del PCS
        + bytes(4)  # creatore
        + bytes(16)  # identificativo
        + bytes(28)
    )
    assert len(intestazione) == 128
    return intestazione + tabella + dati


# --- Immagini sintetiche -------------------------------------------------------

Colore = tuple[int, int, int]


def tinta_unita(colore: Colore, dimensioni: tuple[int, int] = (64, 64)) -> Image.Image:
    return Image.new("RGB", dimensioni, colore)


def gradiente(
    dimensioni: tuple[int, int] = (256, 64),
    da: Colore = (0, 0, 0),
    a: Colore = (255, 255, 255),
    verticale: bool = False,
) -> Image.Image:
    """Gradiente lineare da un colore all'altro, orizzontale (default) o verticale."""
    larghezza, altezza = dimensioni
    n = altezza if verticale else larghezza
    t = (
        np.linspace(0.0, 1.0, n)[:, None]
        if verticale
        else np.linspace(0.0, 1.0, n)[None, :]
    )
    inizio = np.array(da, dtype=float)
    fine = np.array(a, dtype=float)
    if verticale:
        riga = inizio + (fine - inizio) * t  # (altezza, 3)
        matrice = np.repeat(riga[:, None, :], larghezza, axis=1)
    else:
        colonna = inizio + (fine - inizio) * t.T  # (larghezza, 3)
        matrice = np.repeat(colonna[None, :, :], altezza, axis=0)
    return Image.fromarray(np.rint(matrice).astype(np.uint8), "RGB")


def con_dominante(immagine: Image.Image, canali: tuple[int, int, int]) -> Image.Image:
    """Aggiunge ``canali`` (R, G, B, anche negativi) a ogni pixel, tagliando a 0–255."""
    matrice = np.asarray(immagine.convert("RGB"), dtype=np.int16)
    matrice = np.clip(matrice + np.array(canali, dtype=np.int16), 0, 255)
    return Image.fromarray(matrice.astype(np.uint8), "RGB")


def rettangolo_inclinato(
    dimensioni: tuple[int, int] = (800, 600),
    angolo_gradi: float = 3.0,
    lati: tuple[int, int] = (480, 320),
    colore: Colore = (200, 180, 140),
    sfondo: Colore = (30, 30, 30),
) -> tuple[Image.Image, list[tuple[float, float]]]:
    """Un rettangolo pieno ruotato di ``angolo_gradi`` al centro dell'immagine.

    Restituisce l'immagine e i quattro angoli (x, y) in pixel, in ordine
    alto-sinistra, alto-destra, basso-destra, basso-sinistra: la verità con cui
    si misura l'errore di chi li cerca.
    """
    larghezza, altezza = dimensioni
    immagine = Image.new("RGB", dimensioni, sfondo)
    cx, cy = larghezza / 2, altezza / 2
    mezzo_l, mezzo_a = lati[0] / 2, lati[1] / 2
    rad = math.radians(angolo_gradi)
    cos, sin = math.cos(rad), math.sin(rad)
    angoli = []
    for dx, dy in (
        (-mezzo_l, -mezzo_a),
        (mezzo_l, -mezzo_a),
        (mezzo_l, mezzo_a),
        (-mezzo_l, mezzo_a),
    ):
        angoli.append((cx + dx * cos - dy * sin, cy + dx * sin + dy * cos))
    ImageDraw.Draw(immagine).polygon(angoli, fill=colore)
    return immagine, angoli


def linee_inclinate(
    dimensioni: tuple[int, int] = (800, 600),
    angolo_gradi: float = 3.0,
    passo: int = 40,
    spessore: int = 3,
) -> Image.Image:
    """Linee chiare su fondo scuro, inclinate di ``angolo_gradi`` rispetto all'orizzontale."""
    larghezza, altezza = dimensioni
    immagine = Image.new("RGB", dimensioni, (20, 20, 20))
    disegno = ImageDraw.Draw(immagine)
    rad = math.radians(angolo_gradi)
    pendenza = math.tan(rad)
    for y0 in range(-larghezza, altezza + larghezza, passo):
        disegno.line(
            [(0, y0), (larghezza, y0 + pendenza * larghezza)],
            fill=(235, 235, 235),
            width=spessore,
        )
    return immagine


def nitida(
    dimensioni: tuple[int, int] = (256, 256), lato_casella: int = 8
) -> Image.Image:
    """Scacchiera ad alto contrasto: il massimo di nitidezza."""
    larghezza, altezza = dimensioni
    y, x = np.mgrid[0:altezza, 0:larghezza]
    scacchi = ((x // lato_casella + y // lato_casella) % 2) * 255
    return Image.fromarray(scacchi.astype(np.uint8), "L").convert("RGB")


def sfocata(immagine: Image.Image, raggio: float = 6.0) -> Image.Image:
    return immagine.convert("RGB").filter(ImageFilter.GaussianBlur(raggio))


# --- File codificati -----------------------------------------------------------


def _byte(immagine: Image.Image, formato: str, **opzioni) -> bytes:
    uscita = BytesIO()
    immagine.save(uscita, formato, **opzioni)
    return uscita.getvalue()


def jpeg_qualita(immagine: Image.Image, qualita: int = 90) -> bytes:
    """JPEG a qualità data (senza profilo e senza EXIF)."""
    return _byte(immagine.convert("RGB"), "JPEG", quality=qualita)


def jpeg_con_exif(
    immagine: Image.Image,
    orientamento: int | None = None,
    flash: int | None = None,
    gps: bool = False,
    profilo: bytes | None = None,
) -> bytes:
    """JPEG con EXIF: ``orientamento`` (tag 0x0112), ``flash`` (0x9209), GPS, ICC."""
    exif = Image.Exif()
    exif[0x010F] = "ProduttoreProva"  # Make
    exif[0x0110] = "FotocameraProva"  # Model
    if orientamento is not None:
        exif[0x0112] = orientamento
    if flash is not None:
        exif.get_ifd(0x8769)[0x9209] = flash
    if gps:
        indirizzo = exif.get_ifd(0x8825)
        indirizzo[1] = "N"
        indirizzo[2] = (45.0, 30.0, 0.0)
        indirizzo[3] = "E"
        indirizzo[4] = (9.0, 10.0, 0.0)
    opzioni: dict = {"quality": 92, "exif": exif.tobytes()}
    if profilo is not None:
        opzioni["icc_profile"] = profilo
    return _byte(immagine.convert("RGB"), "JPEG", **opzioni)


def png_con_icc(immagine: Image.Image, profilo: bytes) -> bytes:
    """PNG con il profilo nel chunk ``iCCP``."""
    return _byte(immagine.convert("RGB"), "PNG", icc_profile=profilo)


def webp_con_icc(immagine: Image.Image, profilo: bytes) -> bytes:
    """WEBP (senza perdita) con il profilo ICC."""
    return _byte(immagine.convert("RGB"), "WEBP", lossless=True, icc_profile=profilo)


def jpeg_cmyk(dimensioni: tuple[int, int] = (64, 64), valore: int = 40) -> bytes:
    """JPEG CMYK a tinta unita."""
    return _byte(Image.new("CMYK", dimensioni, (valore, valore, valore, 0)), "JPEG")


def apri(dati: bytes) -> Image.Image:
    """Decodifica i byte di un file di prova (per i confronti nei test)."""
    immagine = Image.open(BytesIO(dati))
    immagine.load()
    return immagine


# --- Colore e distanze ---------------------------------------------------------

_M_SRGB_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)
_BIANCO_D65_XYZ = np.array([0.95047, 1.0, 1.08883])


def _lab(rgb: np.ndarray) -> np.ndarray:
    """Da sRGB (0–255, forma (..., 3)) a CIE Lab con bianco D65."""
    c = rgb.astype(float) / 255.0
    lineare = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = lineare @ _M_SRGB_XYZ.T / _BIANCO_D65_XYZ
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack(
        [
            116 * f[..., 1] - 16,
            500 * (f[..., 0] - f[..., 1]),
            200 * (f[..., 1] - f[..., 2]),
        ],
        axis=-1,
    )


def _matrice(oggetto: Image.Image | Colore) -> np.ndarray:
    if isinstance(oggetto, Image.Image):
        return np.asarray(oggetto.convert("RGB"))
    return np.asarray(oggetto, dtype=float).reshape(1, 1, 3)


def delta_e(a: Image.Image | Colore, b: Image.Image | Colore) -> float:
    """ΔE medio CIE76 (distanza euclidea in Lab) tra due immagini o due colori.

    Le immagini devono avere le stesse dimensioni; un colore si confronta con
    un'immagine intera (tutti i pixel contro quel colore).
    """
    lab_a, lab_b = _lab(_matrice(a)), _lab(_matrice(b))
    return float(np.mean(np.linalg.norm(lab_a - lab_b, axis=-1)))


def media_lab(
    immagine: Image.Image, riquadro: tuple[int, int, int, int] | None = None
) -> tuple[float, float, float]:
    """Media (L, a, b) dei pixel, su tutta l'immagine o su un riquadro (x0, y0, x1, y1)."""
    matrice = _matrice(immagine)
    if riquadro is not None:
        x0, y0, x1, y1 = riquadro
        matrice = matrice[y0:y1, x0:x1]
    media = _lab(matrice).reshape(-1, 3).mean(axis=0)
    return float(media[0]), float(media[1]), float(media[2])
