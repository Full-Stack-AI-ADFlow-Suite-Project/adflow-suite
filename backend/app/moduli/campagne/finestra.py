"""La finestra: quale parte della foto esce, e quando servono le barre (ADR-124, RT-16).

``calcola_finestra`` è una funzione pura: dalle dimensioni della foto, dal soggetto,
dal testo da tenere (``tieni``), dagli intrusi ai bordi (``togli``) e dalle dosi di una
variante dice quale riquadro tenere. Lo chiamano le varianti (RT-25); l'esecutore
(``esecutore._passo_finestra``) si limita ad applicare il riquadro che gli arriva nel
comando. Le coordinate sono normalizzate (0–1) sulla foto **al momento del passo**
(dopo rotazione e raddrizzamento), come quelle che l'esecutore passa a ``Mappa``.

Regole (nota 7.5, passo 6, e 12.5):
- l'intervallo dei rapporti è quello unico di Facebook e Instagram: da 4:5 a 1,91:1;
- una foto dentro l'intervallo non si taglia, se non per avvicinarsi al soggetto;
- fuori intervallo si taglia solo quel che serve per rientrarci, e solo se il taglio non
  supera le soglie di R-42 (35% con un soggetto, 10% senza): altrimenti la foto resta
  intera e si mettono le barre;
- il soggetto e il testo da tenere non si tagliano mai: se non ci stanno, barre;
- l'avvicinamento cerca la finestra più piccola con il rapporto della foto che contiene
  il soggetto più il margine, centrata sul centro d'interesse, senza scendere sotto il
  limite di ingrandimento della variante;
- gli intrusi si escludono solo se il taglio resta dentro il tetto della variante, il
  rapporto resta nell'intervallo e il soggetto resta tutto dentro;
- con ``non_tagliare`` resta il solo taglio dovuto al rapporto.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from . import ritocco_catalogo as catalogo
from . import sistemazione_foto as regole

# Un riquadro: (x, y, larghezza, altezza), normalizzati sulla foto.
Box = tuple[float, float, float, float]

TOLLERANZA: Final[float] = 1e-6


@dataclass(frozen=True)
class Finestra:
    """Il riquadro da tenere, nella foto del momento del passo (normalizzato).

    ``b`` è ``(x, y, larghezza, altezza)``; ``rapporto`` è larghezza/altezza in pixel
    della finestra. L'esecutore la ritaglia; le barre le decide il comando.
    """

    b: Box
    rapporto: float


@dataclass(frozen=True)
class Esito:
    """Il risultato del calcolo: la finestra e se servono le barre per rientrare nell'intervallo."""

    finestra: Finestra
    barre: bool


def _px(box: Box, w: float, h: float) -> tuple[float, float, float, float]:
    """Da normalizzato a pixel, tagliato ai bordi della foto: (x0, y0, x1, y1)."""
    x, y, bw, bh = box
    x0, y0 = max(0.0, min(1.0, x)) * w, max(0.0, min(1.0, y)) * h
    x1, y1 = max(0.0, min(1.0, x + bw)) * w, max(0.0, min(1.0, y + bh)) * h
    return x0, y0, max(x0, x1), max(y0, y1)


def _unione(caselle: Sequence[tuple[float, float, float, float]]):
    if not caselle:
        return None
    return (
        min(c[0] for c in caselle),
        min(c[1] for c in caselle),
        max(c[2] for c in caselle),
        max(c[3] for c in caselle),
    )


def _dentro(finestra, richiesta) -> bool:
    return (
        finestra[0] <= richiesta[0] + 1e-6
        and finestra[1] <= richiesta[1] + 1e-6
        and finestra[2] >= richiesta[2] - 1e-6
        and finestra[3] >= richiesta[3] - 1e-6
    )


def _posiziona(
    larghezza: float,
    altezza: float,
    contenitore: tuple[float, float, float, float],
    richiesta: tuple[float, float, float, float] | None,
    centro: tuple[float, float] | None,
) -> tuple[float, float, float, float]:
    """La finestra ``larghezza``×``altezza`` dentro ``contenitore``, che contiene ``richiesta`` e sta più vicina a ``centro``."""
    cx0, cy0, cx1, cy1 = contenitore
    larghezza, altezza = min(larghezza, cx1 - cx0), min(altezza, cy1 - cy0)
    if centro is not None:
        px, py = centro
    elif richiesta is not None:
        px, py = (richiesta[0] + richiesta[2]) / 2.0, (
            richiesta[1] + richiesta[3]
        ) / 2.0
    else:
        px, py = (cx0 + cx1) / 2.0, (cy0 + cy1) / 2.0
    x0, y0 = px - larghezza / 2.0, py - altezza / 2.0
    # dentro il contenitore e, se si può, con tutta la richiesta dentro
    lo_x, hi_x = cx0, cx1 - larghezza
    lo_y, hi_y = cy0, cy1 - altezza
    if richiesta is not None:
        lo_x, hi_x = max(lo_x, richiesta[2] - larghezza), min(hi_x, richiesta[0])
        lo_y, hi_y = max(lo_y, richiesta[3] - altezza), min(hi_y, richiesta[1])
    if lo_x > hi_x:
        lo_x = hi_x = max(cx0, min(cx1 - larghezza, richiesta[0] if richiesta else x0))
    if lo_y > hi_y:
        lo_y = hi_y = max(cy0, min(cy1 - altezza, richiesta[1] if richiesta else y0))
    x0, y0 = max(lo_x, min(hi_x, x0)), max(lo_y, min(hi_y, y0))
    return x0, y0, x0 + larghezza, y0 + altezza


def _taglio_per_il_rapporto(
    w: float, h: float, rapporto_min: float, rapporto_max: float
) -> tuple[float, float] | None:
    """Le dimensioni del taglio che porta la foto nell'intervallo (None se ci sta già)."""
    rapporto = w / h
    tolleranza = regole.TOLLERANZA_PROPORZIONE
    if rapporto < rapporto_min - tolleranza:
        return w, w / rapporto_min
    if rapporto > rapporto_max + tolleranza:
        return h * rapporto_max, h
    return None


def calcola_finestra(
    larghezza: int,
    altezza: int,
    *,
    soggetto: Box | None = None,
    tieni: Sequence[Box] = (),
    togli: Sequence[Box] = (),
    centro: tuple[float, float] | None = None,
    avvicina: bool = False,
    non_tagliare: bool = False,
    parametri: catalogo.Parametri = catalogo.STANDARD,
    taglio_avvicinamento_max: float | None = None,
    rapporto_min: float = regole.RATIO_MINIMO,
    rapporto_max: float = regole.RATIO_MASSIMO,
    lato_corto: int = regole.LATO_CORTO_TARGET,
) -> Esito:
    """La finestra di una foto ``larghezza``×``altezza`` pixel. Vedi il modulo per le regole.

    ``taglio_avvicinamento_max`` è la quota d'area che l'avvicinamento può togliere (con
    la nota ``ambiente``: ``parametri.ambiente_taglio_max``); senza, nessun tetto
    oltre il limite di ingrandimento.
    """
    w, h = float(larghezza), float(altezza)
    foto = (0.0, 0.0, w, h)
    soggetti = [_px(b, w, h) for b in ([soggetto] if soggetto else []) + list(tieni)]
    soggetti = [c for c in soggetti if c[2] - c[0] > 0 and c[3] - c[1] > 0]
    richiesta = _unione(soggetti)
    punto = (centro[0] * w, centro[1] * h) if centro else None

    def esito(finestra, barre: bool = False) -> Esito:
        x0, y0, x1, y1 = finestra
        return Esito(
            Finestra(
                (x0 / w, y0 / h, (x1 - x0) / w, (y1 - y0) / h),
                (x1 - x0) / (y1 - y0),
            ),
            barre,
        )

    # 1. Il rapporto: la foto intera, o il taglio minimo per rientrare nell'intervallo.
    base = foto
    barre = False
    taglio = _taglio_per_il_rapporto(w, h, rapporto_min, rapporto_max)
    if taglio is not None:
        soglia = (
            regole.SOGLIA_TAGLIO_SOGGETTO
            if richiesta is not None
            else regole.SOGLIA_TAGLIO_SENZA_SOGGETTO
        ) + regole.TOLLERANZA_TAGLIO
        quota_tagliata = 1.0 - (taglio[0] * taglio[1]) / (w * h)
        candidata = _posiziona(taglio[0], taglio[1], foto, richiesta, punto)
        if quota_tagliata > soglia or (
            richiesta is not None and not _dentro(candidata, richiesta)
        ):
            return esito(foto, barre=True)  # niente taglio che mangi il soggetto: barre
        base = candidata
    if non_tagliare:
        return esito(base)

    bw, bh = base[2] - base[0], base[3] - base[1]
    finestra = base

    # 2. L'avvicinamento: la finestra più piccola con quel rapporto che contiene il soggetto.
    if avvicina and richiesta is not None:
        rapporto = bw / bh
        rw, rh = richiesta[2] - richiesta[0], richiesta[3] - richiesta[1]
        mw, mh = (
            rw * parametri.margine_avvicinamento,
            rh * parametri.margine_avvicinamento,
        )
        con_margine = (
            max(base[0], richiesta[0] - mw),
            max(base[1], richiesta[1] - mh),
            min(base[2], richiesta[2] + mw),
            min(base[3], richiesta[3] + mh),
        )
        fw = max(
            con_margine[2] - con_margine[0],
            (con_margine[3] - con_margine[1]) * rapporto,
        )
        # il lato corto della finestra non scende sotto quello che l'ingrandimento ammette
        corto_min = lato_corto / parametri.ingrandimento_max
        fw = max(fw, corto_min * rapporto if rapporto >= 1.0 else corto_min)
        if taglio_avvicinamento_max is not None:
            area_min = (1.0 - taglio_avvicinamento_max) * bw * bh
            fw = max(fw, math.sqrt(area_min * rapporto))
        fh = fw / rapporto
        if fw < bw - TOLLERANZA:
            finestra = _posiziona(fw, fh, base, con_margine, punto)
            if not _dentro(finestra, richiesta):
                finestra = base

    # 3. Gli intrusi ai bordi: si escludono se il taglio resta nei limiti.
    if togli:
        corto_min = lato_corto / parametri.ingrandimento_max
        for intruso in (_px(b, w, h) for b in togli):
            if intruso[2] <= intruso[0] or intruso[3] <= intruso[1]:
                continue
            x0, y0, x1, y1 = finestra
            if (
                intruso[2] <= x0
                or intruso[0] >= x1
                or intruso[3] <= y0
                or intruso[1] >= y1
            ):
                continue  # fuori dalla finestra
            area = (x1 - x0) * (y1 - y0)
            migliore = None
            for nuova in (
                (max(x0, intruso[2]), y0, x1, y1),  # taglia a sinistra
                (x0, y0, min(x1, intruso[0]), y1),  # taglia a destra
                (x0, max(y0, intruso[3]), x1, y1),  # taglia sopra
                (x0, y0, x1, min(y1, intruso[1])),  # taglia sotto
            ):
                nw, nh = nuova[2] - nuova[0], nuova[3] - nuova[1]
                if nw <= 0 or nh <= 0:
                    continue
                perso = 1.0 - (nw * nh) / area
                if (
                    perso > parametri.intrusi_taglio_max + TOLLERANZA
                    or not rapporto_min - regole.TOLLERANZA_PROPORZIONE
                    <= nw / nh
                    <= rapporto_max + regole.TOLLERANZA_PROPORZIONE
                    or min(nw, nh) < min(corto_min, min(w, h))
                    or (richiesta is not None and not _dentro(nuova, richiesta))
                    or (
                        intruso[0] < nuova[2]
                        and intruso[2] > nuova[0]
                        and intruso[1] < nuova[3]
                        and intruso[3] > nuova[1]
                    )
                ):
                    continue
                if migliore is None or perso < migliore[0]:
                    migliore = (perso, nuova)
            if migliore is not None:
                finestra = migliore[1]

    return esito(finestra)
