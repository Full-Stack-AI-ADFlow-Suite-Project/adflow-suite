"""Sistemazione delle foto per anteprima e pubblicazione.

Implementa la logica locale con Pillow secondo spec R-21, R-42, CA-81 e CA-114 (ADR-119):
1. Rotazione dell'immagine secondo i metadati di orientamento EXIF;
2. Rimozione di qualsiasi metadato GPS e dato sensibile;
3. Adattamento alle proporzioni ammesse, da 4:5 a 1,91:1 (uguale per Facebook e Instagram):
   - Una foto dentro l'intervallo non si taglia;
   - Se fuori:
     (a) con soggetto_box che entra nella finestra e taglio <= 35% area -> ritaglio attorno al soggetto;
     (b) senza riquadro e taglio <= 10% area -> ritaglio al centro;
     (c) altrimenti -> bordi sfocati (tela della proporzione, foto sfocata GaussianBlur 30 e scurita 15%,
         foto intera centrata sopra);
4. Ridimensionamento con lato corto esattamente a 1080 px;
5. Applicazione di un leggero autocontrasto;
6. Esportazione finale in formato JPEG;
7. Invariante costituzionale (§1.3): il file originale non viene mai modificato.
"""

from __future__ import annotations

import io
from typing import Any, Final
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

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
CUTOFF_AUTOCONTRASTO: Final[int] = 2
MAX_PIXEL_TOTALI: Final[int] = 36_000_000

# Soglie di ritaglio (spec R-42, ADR-119, brief §1.5)
SOGLIA_TAGLIO_SOGGETTO: Final[float] = 0.35
SOGLIA_TAGLIO_SENZA_SOGGETTO: Final[float] = 0.10
TOLLERANZA_TAGLIO: Final[float] = 0.02


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
    if current_ratio < target_ratio:
        # Foto più stretta/alta della proporzione: l'altezza resta h, la larghezza cresce
        h_canvas = h
        w_canvas = round(h * target_ratio)
    else:
        # Foto più larga della proporzione: la larghezza resta w, l'altezza cresce
        w_canvas = w
        h_canvas = round(w / target_ratio)

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


def sistema_foto_buffer(
    dati_foto: bytes,
    canale: str = "instagram",
    proporzione: str | None = None,
    soggetto_box: dict[str, float] | None = None,
) -> bytes:
    """Elabora e sistema i byte binari di una foto secondo spec R-42 e CA-114 (ADR-119).

    Operazioni eseguite su una copia in memoria:
    - Rotazione corretta basata sui metadati EXIF;
    - Rimozione totale di GPS e metadati identificativi;
    - Adattamento alle proporzioni ammesse da 4:5 a 1,91:1 con ritaglio sul soggetto,
      ritaglio al centro o bordi sfocati;
    - Ridimensionamento con lato corto a 1080 px;
    - Autocontrasto leggero;
    - Codifica finale JPEG.

    Args:
        dati_foto: Il contenuto binario dell'immagine sorgente (JPEG, PNG o WEBP).
        canale: Canale di destinazione ('facebook' o 'instagram').
        proporzione: Opzionale proporzione forzata ('1:1' o '4:5').
        soggetto_box: Opzionale riquadro normalizzato del soggetto dall'analisi AI.

    Returns:
        I byte dell'immagine JPEG sistemata.

    Raises:
        DatiNonValidi: Se i byte non rappresentano un'immagine valida o se il canale/proporzione non è ammesso.
    """
    if not dati_foto:
        raise DatiNonValidi("Nessun dato immagine fornito.")

    canale_norm = canale.strip().lower()
    if canale_norm not in PROPORZIONI_CANALE:
        raise DatiNonValidi(
            f"Canale '{canale}' non valido. Canali ammessi: {', '.join(PROPORZIONI_CANALE.keys())}."
        )

    try:
        immagine_raw = Image.open(io.BytesIO(dati_foto))
    except Exception as exc:
        raise DatiNonValidi("File immagine non valido o corrotto.") from exc

    if immagine_raw.width <= 0 or immagine_raw.height <= 0:
        immagine_raw.close()
        raise DatiNonValidi("Dimensioni dell'immagine non valide (<= 0).")

    if immagine_raw.width * immagine_raw.height > MAX_PIXEL_TOTALI:
        w_curr, h_curr = immagine_raw.width, immagine_raw.height
        immagine_raw.close()
        raise DatiNonValidi(
            f"Immagine troppo grande ({w_curr}x{h_curr} px). "
            f"Il limite consentito è di {MAX_PIXEL_TOTALI} pixel."
        )

    try:
        # 1. Rotazione secondo i metadati di orientamento (EXIF Orientation)
        try:
            img = ImageOps.exif_transpose(immagine_raw)
        except Exception:
            img = immagine_raw.copy()

        # 2. Conversione a RGB pulita (gestendo canale alpha / trasparenza su sfondo bianco)
        ha_trasparenza = (
            "A" in img.mode
            or (img.mode == "P" and "transparency" in img.info)
            or img.mode in ("RGBA", "LA", "PA")
        )
        if ha_trasparenza:
            img_rgba = img.convert("RGBA")
            sfondo = Image.new("RGBA", img_rgba.size, (255, 255, 255, 255))
            sfondo.paste(img_rgba, mask=img_rgba.split()[3])
            img = sfondo.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 3. Adattamento alle proporzioni: da 4:5 a 1,91:1 (R-21, R-42, ADR-119)
        ratio_corrente = _calcola_ratio(img.width, img.height)
        target = _ratio_target(
            ratio_corrente=ratio_corrente,
            proporzioni_ammesse=PROPORZIONI_CANALE[canale_norm],
            proporzione_richiesta=proporzione,
        )

        if target is not None:
            img = _adatta_alle_proporzioni(img, target, soggetto_box=soggetto_box)

        # 4. Ridimensionamento con lato corto esattamente a 1080 px
        img = _ridimensiona_lato_corto(img, LATO_CORTO_TARGET)

        # 5. Autocontrasto leggero
        img = ImageOps.autocontrast(img, cutoff=CUTOFF_AUTOCONTRASTO)

        # 6. Salvataggio in JPEG pulito (senza metadati EXIF né GPS)
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=90, optimize=True)
        return output.getvalue()
    finally:
        immagine_raw.close()
