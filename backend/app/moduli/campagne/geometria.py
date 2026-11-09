"""La geometria dell'esecutore: rotazioni, raddrizzamento e la mappa delle coordinate (ADR-124, RT-15).

Tutte le coordinate che arrivano dall'AI, dall'operatore e dai candidati sono nel
riferimento della foto dopo EXIF e sRGB (nota 7.5, passo 2). I passi geometrici
cambiano la foto; ``Mappa`` tiene la trasformazione che porta un punto del
riferimento di partenza nella foto di adesso, così il soggetto, le zone e le
finestre seguono l'immagine senza essere ricalcolati a ogni passo.

Convenzioni: coordinate **continue** in pixel (0 è il bordo sinistro del primo
pixel, ``larghezza`` quello destro), y verso il basso. ``gradi`` di una rotazione
sono quelli di ``preanalisi.misura``: positivi se le linee scendono verso destra;
chi raddrizza ruota in senso antiorario di quell'angolo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Final

import cv2
import numpy as np
from PIL import Image

from . import ritocco_catalogo as catalogo

# Il lato di un'immagine raddrizzata in prospettiva non supera questo: la superficie
# di una foto da 36 MP non deve produrre un'immagine ancora più grande.
LATO_MAX_PROSPETTIVA: Final[int] = 6000
SUPERFICIE_MIN: Final[
    float
] = 16.0  # lato minimo, in pixel, di una superficie raddrizzata


@dataclass
class Mappa:
    """Porta i punti dal riferimento di partenza alla foto di adesso (matrice 3×3 omogenea)."""

    larghezza: int
    altezza: int
    matrice: np.ndarray = field(default_factory=lambda: np.eye(3))
    origine: tuple[int, int] = (0, 0)

    @classmethod
    def identita(cls, larghezza: int, altezza: int) -> "Mappa":
        return cls(larghezza, altezza, np.eye(3), (larghezza, altezza))

    def dopo(self, passo: np.ndarray, larghezza: int, altezza: int) -> "Mappa":
        """La mappa dopo un passo che trasforma i punti con ``passo`` (3×3) e dà una foto ``larghezza``×``altezza``."""
        return Mappa(larghezza, altezza, passo @ self.matrice, self.origine)

    def traslata(self, dx: float, dy: float, larghezza: int, altezza: int) -> "Mappa":
        """Dopo un ritaglio (``dx``, ``dy`` negativi) o l'aggiunta di barre (positivi)."""
        passo = np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]], dtype=float)
        return self.dopo(passo, larghezza, altezza)

    def scalata(self, larghezza: int, altezza: int) -> "Mappa":
        """Dopo un ridimensionamento della foto di adesso a ``larghezza``×``altezza``."""
        passo = np.array(
            [
                [larghezza / self.larghezza, 0, 0],
                [0, altezza / self.altezza, 0],
                [0, 0, 1],
            ],
            dtype=float,
        )
        return self.dopo(passo, larghezza, altezza)

    def punti(self, punti: np.ndarray) -> np.ndarray:
        """Trasforma un array (n, 2) di punti in pixel del riferimento di partenza."""
        omogenei = np.hstack([np.asarray(punti, dtype=float), np.ones((len(punti), 1))])
        mappati = omogenei @ self.matrice.T
        return mappati[:, :2] / mappati[:, 2:3]

    def punto(self, x: float, y: float) -> tuple[float, float]:
        px, py = self.punti(np.array([[x, y]]))[0]
        return float(px), float(py)

    def punto_norm(self, x: float, y: float) -> tuple[float, float]:
        """Un punto normalizzato (0–1) di partenza → normalizzato sulla foto di adesso."""
        l0, a0 = self.origine
        px, py = self.punto(x * l0, y * a0)
        return px / self.larghezza, py / self.altezza

    def box_norm(self, box: dict[str, float] | None) -> dict[str, float] | None:
        """Un riquadro normalizzato ``{x, y, larghezza, altezza}`` di partenza → quello che lo contiene, adesso.

        Il riquadro è la scatola dei quattro angoli mappati, tagliata ai bordi della
        foto; ``None`` se non resta niente (il soggetto è finito fuori).
        """
        if box is None:
            return None
        x, y, w, h = box["x"], box["y"], box["larghezza"], box["altezza"]
        angoli = [
            self.punto_norm(px, py)
            for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))
        ]
        x0 = max(0.0, min(p[0] for p in angoli))
        y0 = max(0.0, min(p[1] for p in angoli))
        x1 = min(1.0, max(p[0] for p in angoli))
        y1 = min(1.0, max(p[1] for p in angoli))
        if x1 - x0 <= 1e-6 or y1 - y0 <= 1e-6:
            return None
        return {"x": x0, "y": y0, "larghezza": x1 - x0, "altezza": y1 - y0}


# --- Rotazioni di 90° ---------------------------------------------------------------


def ruota_90(img: Image.Image, gradi: int, mappa: Mappa) -> tuple[Image.Image, Mappa]:
    """Ruota di ``gradi`` (0, 90, 180, 270) in senso orario, senza perdere pixel."""
    larghezza, altezza = img.size
    if gradi == 0:
        return img, mappa
    if gradi == 90:  # orario
        nuova = img.transpose(Image.Transpose.ROTATE_270)
        passo = np.array([[0, -1, altezza], [1, 0, 0], [0, 0, 1]], dtype=float)
        return nuova, mappa.dopo(passo, altezza, larghezza)
    if gradi == 180:
        nuova = img.transpose(Image.Transpose.ROTATE_180)
        passo = np.array([[-1, 0, larghezza], [0, -1, altezza], [0, 0, 1]], dtype=float)
        return nuova, mappa.dopo(passo, larghezza, altezza)
    if gradi == 270:  # orario = 90° antiorario
        nuova = img.transpose(Image.Transpose.ROTATE_90)
        passo = np.array([[0, 1, 0], [-1, 0, larghezza], [0, 0, 1]], dtype=float)
        return nuova, mappa.dopo(passo, altezza, larghezza)
    raise ValueError(f"Rotazione non ammessa: {gradi}")


# --- Rotazione fine -----------------------------------------------------------------


def rettangolo_inscritto(larghezza: int, altezza: int, gradi: float) -> float:
    """Il fattore (0–1) del più grande rettangolo, con le stesse proporzioni, dentro la foto ruotata.

    Una foto ruotata di un angolo ha gli angoli vuoti: si ritaglia il rettangolo
    più grande che sta tutto dentro la parte piena.
    """
    a = abs(math.radians(gradi))
    seno, coseno = math.sin(a), math.cos(a)
    return min(
        larghezza / (larghezza * coseno + altezza * seno),
        altezza / (larghezza * seno + altezza * coseno),
    )


def raddrizza_rotazione(
    img: Image.Image, gradi: float, mappa: Mappa
) -> tuple[Image.Image, Mappa]:
    """Ruota di ``gradi`` in senso antiorario (la correzione di un angolo misurato) e toglie i bordi vuoti."""
    larghezza, altezza = img.size
    ruotata = img.rotate(gradi, resample=Image.Resampling.BICUBIC, expand=False)
    k = rettangolo_inscritto(larghezza, altezza, gradi)
    nuova_l, nuova_a = max(1, int(larghezza * k)), max(1, int(altezza * k))
    sinistra, sopra = (larghezza - nuova_l) // 2, (altezza - nuova_a) // 2
    ritagliata = ruotata.crop((sinistra, sopra, sinistra + nuova_l, sopra + nuova_a))
    t = math.radians(gradi)
    c, s = math.cos(t), math.sin(t)
    cx, cy = larghezza / 2.0, altezza / 2.0
    # antiorario sullo schermo (y verso il basso): (dx, dy) → (dx·c + dy·s, −dx·s + dy·c)
    rotazione = np.array(
        [
            [c, s, cx - c * cx - s * cy - sinistra],
            [-s, c, cy + s * cx - c * cy - sopra],
            [0, 0, 1],
        ]
    )
    return ritagliata, mappa.dopo(rotazione, nuova_l, nuova_a)


# --- Prospettiva --------------------------------------------------------------------


def deformazione(angoli: np.ndarray) -> float:
    """Quanto un quadrilatero (alto-sx, alto-dx, basso-dx, basso-sx) è lontano da un rettangolo.

    È il maggiore fra la differenza relativa dei lati opposti: 0 per un rettangolo
    (anche ruotato), vicino a 1 per un trapezio molto stretto da una parte.
    """
    tl, tr, br, bl = (np.asarray(p, dtype=float) for p in angoli)
    lati = (
        (np.linalg.norm(tr - tl), np.linalg.norm(br - bl)),
        (np.linalg.norm(bl - tl), np.linalg.norm(br - tr)),
    )
    return max(abs(a - b) / max(a, b, 1e-9) for a, b in lati)


def coefficienti_prospettiva(
    origine: np.ndarray, destinazione: np.ndarray
) -> tuple[float, ...]:
    """I coefficienti per ``Image.transform(..., Image.PERSPECTIVE, ...)``.

    Pillow vuole la trasformazione **inversa**: per ogni pixel dell'uscita dice da
    dove prenderlo nell'ingresso. Quindi si calcola l'omografia ``origine`` →
    ``destinazione`` e si inverte: usare quella diretta storce la foto al contrario.
    """
    diretta = cv2.getPerspectiveTransform(
        np.asarray(origine, dtype=np.float32),
        np.asarray(destinazione, dtype=np.float32),
    )
    inversa = np.linalg.inv(diretta)
    inversa = inversa / inversa[2, 2]
    return tuple(float(v) for v in inversa.ravel()[:8])


def _dimensioni_superficie(angoli: np.ndarray) -> tuple[int, int]:
    tl, tr, br, bl = (np.asarray(p, dtype=float) for p in angoli)
    larghezza = (np.linalg.norm(tr - tl) + np.linalg.norm(br - bl)) / 2.0
    altezza = (np.linalg.norm(bl - tl) + np.linalg.norm(br - tr)) / 2.0
    scala = min(1.0, LATO_MAX_PROSPETTIVA / max(larghezza, altezza, 1.0))
    return max(1, round(larghezza * scala)), max(1, round(altezza * scala))


def _convesso_dentro(angoli: np.ndarray, larghezza: int, altezza: int) -> bool:
    """Il quadrilatero sta (quasi) dentro la foto, è convesso e ha un'area vera."""
    if not np.all(np.isfinite(angoli)):
        return False
    margine = 0.01 * max(larghezza, altezza)
    if (
        angoli[:, 0].min() < -margine
        or angoli[:, 1].min() < -margine
        or angoli[:, 0].max() > larghezza + margine
        or angoli[:, 1].max() > altezza + margine
    ):
        return False
    contorno = np.asarray(angoli, dtype=np.float32).reshape(-1, 1, 2)
    return bool(cv2.isContourConvex(contorno)) and cv2.contourArea(contorno) > 0


def raddrizza_prospettiva(
    img: Image.Image,
    angoli_norm: list[list[float]],
    mappa: Mappa,
    deformazione_max: float = catalogo.STANDARD.prospettiva_deformazione_max,
) -> tuple[Image.Image, Mappa] | None:
    """Raddrizza una superficie piana: l'uscita è la sola superficie, vista di fronte.

    ``angoli_norm`` sono i quattro angoli (alto-sx, alto-dx, basso-dx, basso-sx) nel
    riferimento di partenza, normalizzati. Se i controlli non passano (angoli fuori
    dalla foto, quadrilatero non convesso, superficie troppo piccola, deformazione
    oltre ``deformazione_max``) restituisce ``None``: il passo si salta, non il comando.
    """
    if len(angoli_norm) != 4 or any(len(p) != 2 for p in angoli_norm):
        return None
    l0, a0 = mappa.origine
    partenza = np.array([[x * l0, y * a0] for x, y in angoli_norm], dtype=float)
    angoli = mappa.punti(partenza)
    larghezza, altezza = img.size
    if not _convesso_dentro(angoli, larghezza, altezza):
        return None
    if deformazione(angoli) > deformazione_max:
        return None
    nuova_l, nuova_a = _dimensioni_superficie(angoli)
    if min(nuova_l, nuova_a) < SUPERFICIE_MIN:
        return None
    destinazione = np.array(
        [[0, 0], [nuova_l, 0], [nuova_l, nuova_a], [0, nuova_a]], dtype=float
    )
    coefficienti = coefficienti_prospettiva(angoli, destinazione)
    raddrizzata = img.transform(
        (nuova_l, nuova_a),
        Image.Transform.PERSPECTIVE,
        coefficienti,
        resample=Image.Resampling.BICUBIC,
    )
    diretta = cv2.getPerspectiveTransform(
        angoli.astype(np.float32), destinazione.astype(np.float32)
    ).astype(float)
    return raddrizzata, mappa.dopo(diretta, nuova_l, nuova_a)


def angoli_da_candidato(candidato: dict[str, Any]) -> list[list[float]]:
    """Gli angoli normalizzati di un candidato quadrilatero di ``preanalisi.candidati``."""
    return [[float(x), float(y)] for x, y in candidato["angoli"]]
