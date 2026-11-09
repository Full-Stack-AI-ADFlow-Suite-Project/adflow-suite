"""Le regole di R-42 per le proporzioni delle foto (spec R-21, R-42, CA-81 e CA-114, ADR-119).

Dal task RT-04 (ADR-124) la sistemazione la esegue `esecutore.esegui`, con un
comando; qui restano le regole geometriche che il passo «finestra» applica:
1. Adattamento alle proporzioni ammesse, da 4:5 a 1,91:1 (uguale per Facebook e Instagram):
   - Una foto dentro l'intervallo non si taglia;
   - Se fuori:
     (a) con soggetto_box che entra nella finestra e taglio <= 35% area -> ritaglio attorno al soggetto;
     (b) senza riquadro e taglio <= 10% area -> ritaglio al centro;
     (c) altrimenti -> bordi sfocati (tela della proporzione, foto sfocata GaussianBlur 30 e scurita 15%,
         foto intera centrata sopra);
2. Ridimensionamento con lato corto esattamente a 1080 px.

L'autocontrasto leggero di una volta non c'è più (RT-04): le foto buone escono come
sono. Invariante costituzionale (§1.3): il file originale non viene mai modificato.
"""

from __future__ import annotations

from typing import Any, Final

from PIL import Image, ImageEnhance, ImageFilter

from app.core.errori import DatiNonValidi

# Intervallo ammesso per entrambi i canali (R-21, R-42): da 4:5 a 1,91:1.
RATIO_MINIMO: Final[float] = 4 / 5
RATIO_MASSIMO: Final[float] = 1.91

# Proporzioni che si possono ancora forzare a mano (R-42).
PROPORZIONI_CANALE: Final[dict[str, tuple[tuple[int, int], ...]]] = {
    "facebook": ((1, 1), (4, 5)),
    "instagram": ((1, 1), (4, 5)),
}

LATO_CORTO_TARGET: Final[int] = 1080
TOLLERANZA_PROPORZIONE: Final[float] = 0.01
MAX_PIXEL_TOTALI: Final[int] = 36_000_000

# Soglie di ritaglio (spec R-42, ADR-119, brief §1.5)
SOGLIA_TAGLIO_SOGGETTO: Final[float] = 0.35
SOGLIA_TAGLIO_SENZA_SOGGETTO: Final[float] = 0.10
TOLLERANZA_TAGLIO: Final[float] = 0.02

# Il grigio delle barre neutre (RT-16): scuro, non attira l'occhio sul feed.
COLORE_BARRE_NEUTRE: Final[tuple[int, int, int]] = (38, 38, 38)


def _calcola_ratio(larghezza: int, altezza: int) -> float:
    """Calcola il rapporto larghezza / altezza."""
    if larghezza <= 0 or altezza <= 0:
        raise DatiNonValidi("Dimensioni dell'immagine non valide (<= 0).")
    return larghezza / altezza


def _ratio_target(
    ratio_corrente: float,
    proporzioni_ammesse: tuple[tuple[int, int], ...],
    proporzione_richiesta: str | None = None,
) -> float | None:
    """Il rapporto a cui portare la foto, o None se non va tagliata.

    Una proporzione forzata ('1:1' o '4:5') vale come richiesta. Altrimenti una
    foto dentro l'intervallo da 4:5 a 1,91:1 (entro tolleranza) resta com'è, e
    una fuori va al bordo più vicino.
    """
    if proporzione_richiesta:
        ratios_ammessi = {f"{w}:{h}": w / h for (w, h) in proporzioni_ammesse}
        if proporzione_richiesta not in ratios_ammessi:
            raise DatiNonValidi(
                f"Proporzione '{proporzione_richiesta}' non ammessa. "
                f"Valori validi: {', '.join(ratios_ammessi.keys())}."
            )
        target = ratios_ammessi[proporzione_richiesta]
        if abs(ratio_corrente - target) <= TOLLERANZA_PROPORZIONE:
            return None
        return target

    if ratio_corrente < RATIO_MINIMO - TOLLERANZA_PROPORZIONE:
        return RATIO_MINIMO
    if ratio_corrente > RATIO_MASSIMO + TOLLERANZA_PROPORZIONE:
        return RATIO_MASSIMO
    return None


def _valida_soggetto_box(box: Any) -> dict[str, float] | None:
    """Valida il riquadro del soggetto.

    Deve essere un dizionario con chiavi 'x', 'y', 'larghezza', 'altezza',
    valori numerici tra 0 e 1, con larghezza e altezza positive.
    Un riquadro non valido o malformato vale None (R-42, brief §1.4).
    """
    if not isinstance(box, dict):
        return None
    try:
        x = float(box["x"])
        y = float(box["y"])
        w = float(box["larghezza"])
        h = float(box["altezza"])
    except (KeyError, TypeError, ValueError):
        return None
    if w <= 0 or h <= 0 or x < 0 or y < 0:
        return None
    if x + w > 1.0001 or y + h > 1.0001:
        return None
    return {
        "x": max(0.0, min(1.0, x)),
        "y": max(0.0, min(1.0, y)),
        "larghezza": min(1.0, w),
        "altezza": min(1.0, h),
    }


def _ritaglia_al_centro(img: Image.Image, target_ratio: float) -> Image.Image:
    """Esegue un ritaglio al centro per allineare l'immagine al rapporto target."""
    current_ratio = img.width / img.height

    if current_ratio > target_ratio:
        # Immagine troppo larga: ritaglia i bordi laterali
        nuova_larghezza = round(img.height * target_ratio)
        offset_x = (img.width - nuova_larghezza) // 2
        box = (offset_x, 0, offset_x + nuova_larghezza, img.height)
        return img.crop(box)
    elif current_ratio < target_ratio:
        # Immagine troppo alta: ritaglia sopra e sotto
        nuova_altezza = round(img.width / target_ratio)
        offset_y = (img.height - nuova_altezza) // 2
        box = (0, offset_y, img.width, offset_y + nuova_altezza)
        return img.crop(box)

    return img


def _adatta_alle_proporzioni(
    img: Image.Image,
    target_ratio: float,
    soggetto_box: dict[str, float] | None = None,
) -> Image.Image:
    """Adatta l'immagine al rapporto target secondo R-42 e brief §1.5 (T3-921).

    (a) con soggetto_box che entra nella finestra e il taglio toglie al più il 35% dell'area:
        ritaglio: la finestra più grande della proporzione che contiene il riquadro,
        centrata sul suo centro e tenuta dentro la foto;
    (b) senza riquadro e il taglio toglie al più il 10%:
        ritaglio al centro come oggi;
    (c) altrimenti:
        bordi sfocati: tela della proporzione, sotto la foto stessa ingrandita a coprire,
        sfocata (GaussianBlur 30) e scurita del 15%, sopra la foto intera centrata.
    """
    w, h = img.width, img.height
    area_orig = w * h

    current_ratio = w / h
    if current_ratio > target_ratio:
        # Foto più larga: altezza fissa, larghezza ridotta
        h_crop = h
        w_crop = round(h * target_ratio)
    else:
        # Foto più alta: larghezza fissa, altezza ridotta
        w_crop = w
        h_crop = round(w / target_ratio)

    area_crop = w_crop * h_crop
    frazione_taglio = max(0.0, (area_orig - area_crop) / area_orig)

    box = _valida_soggetto_box(soggetto_box)
    if box is not None:
        box_px_x = box["x"] * w
        box_px_y = box["y"] * h
        box_px_w = box["larghezza"] * w
        box_px_h = box["altezza"] * h

        # (a) Il riquadro entra nella finestra e il taglio toglie al più il 35%
        entra = box_px_w <= w_crop and box_px_h <= h_crop
        taglio_ammissibile = frazione_taglio <= (
            SOGLIA_TAGLIO_SOGGETTO + TOLLERANZA_TAGLIO
        )

        if entra and taglio_ammissibile:
            centro_x = box_px_x + box_px_w / 2
            centro_y = box_px_y + box_px_h / 2
            crop_x = round(centro_x - w_crop / 2)
            crop_y = round(centro_y - h_crop / 2)
            crop_x = max(0, min(crop_x, w - w_crop))
            crop_y = max(0, min(crop_y, h - h_crop))
            return img.crop((crop_x, crop_y, crop_x + w_crop, crop_y + h_crop))

    # (b) Senza riquadro e il taglio toglie al più il 10%
    if box is None and frazione_taglio <= (
        SOGLIA_TAGLIO_SENZA_SOGGETTO + TOLLERANZA_PROPORZIONE
    ):
        return _ritaglia_al_centro(img, target_ratio)

    # (c) Altrimenti bordi sfocati: tela della proporzione
    return tela_con_barre(img, target_ratio)


def tela_con_barre(
    img: Image.Image, target_ratio: float, neutre: bool = False
) -> Image.Image:
    """La foto intera, centrata su una tela del rapporto ``target_ratio``.

    Le barre sono la foto stessa ingrandita a coprire, sfocata (GaussianBlur 30) e
    scurita del 15%; con ``neutre`` un grigio uniforme (RT-16, nota 7.5 passo 6).
    """
    w, h = img.width, img.height
    current_ratio = w / h
    if current_ratio < target_ratio:
        # Foto più stretta/alta della proporzione: l'altezza resta h, la larghezza cresce
        h_canvas = h
        w_canvas = round(h * target_ratio)
    else:
        # Foto più larga della proporzione: la larghezza resta w, l'altezza cresce
        w_canvas = w
        h_canvas = round(w / target_ratio)

    if neutre:
        tela = Image.new("RGB", (w_canvas, h_canvas), COLORE_BARRE_NEUTRE)
        tela.paste(img, ((w_canvas - w) // 2, (h_canvas - h) // 2))
        return tela

    # Sotto: la foto stessa ingrandita a coprire
    scale = max(w_canvas / w, h_canvas / h)
    scaled_w = round(w * scale)
    scaled_h = round(h * scale)
    bg_scaled = img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

    # Ritaglio al centro per allineare a (w_canvas, h_canvas)
    bg_x = (scaled_w - w_canvas) // 2
    bg_y = (scaled_h - h_canvas) // 2
    bg = bg_scaled.crop((bg_x, bg_y, bg_x + w_canvas, bg_y + h_canvas))

    # Sfocata (GaussianBlur 30) e scurita del 15%
    bg = bg.filter(ImageFilter.GaussianBlur(30))
    bg = ImageEnhance.Brightness(bg).enhance(0.85)

    # Sopra: la foto intera centrata
    pos_x = (w_canvas - w) // 2
    pos_y = (h_canvas - h) // 2
    bg.paste(img, (pos_x, pos_y))
    return bg


def _ridimensiona_lato_corto(
    img: Image.Image, lato_corto_target: int = LATO_CORTO_TARGET
) -> Image.Image:
    """Ridimensiona l'immagine con resampling Lanczos affinché il lato corto sia esattamente quello target."""
    lato_corto = min(img.width, img.height)
    if lato_corto == lato_corto_target:
        return img

    fattore_scala = lato_corto_target / lato_corto
    nuova_larghezza = round(img.width * fattore_scala)
    nuova_altezza = round(img.height * fattore_scala)

    # Assicura che l'arrotondamento mantenga il lato corto esattamente pari al target
    if min(nuova_larghezza, nuova_altezza) != lato_corto_target:
        if nuova_larghezza <= nuova_altezza:
            nuova_larghezza = lato_corto_target
        else:
            nuova_altezza = lato_corto_target

    return img.resize((nuova_larghezza, nuova_altezza), Image.Resampling.LANCZOS)
