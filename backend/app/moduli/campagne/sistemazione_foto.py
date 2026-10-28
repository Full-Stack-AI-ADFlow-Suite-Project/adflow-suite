"""Sistemazione delle foto per anteprima e pubblicazione.

Implementa la logica locale con Pillow secondo spec R-21, R-42 e CA-81:
1. Rotazione dell'immagine secondo i metadati di orientamento EXIF;
2. Rimozione di qualsiasi metadato GPS e dato sensibile;
3. Ritaglio al centro solo se la foto è fuori dall'intervallo di proporzioni
   ammesso, da 4:5 a 1,91:1 (uguale per Facebook e Instagram): una foto dentro
   l'intervallo non si taglia, una fuori va al bordo più vicino;
4. Ridimensionamento con lato corto esattamente a 1080 px;
5. Applicazione di un leggero autocontrasto;
6. Esportazione finale in formato JPEG;
7. Invariante costituzionale (§1.3): il file originale non viene mai modificato.
"""

from __future__ import annotations

import io
from typing import Final
from PIL import Image, ImageOps

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
) -> bytes:
    """Elabora e sistema i byte binari di una foto secondo spec R-42.

    Operazioni eseguite su una copia in memoria:
    - Rotazione corretta basata sui metadati EXIF;
    - Rimozione totale di GPS e metadati identificativi;
    - Ritaglio al centro se la foto è fuori da 4:5 – 1,91:1;
    - Ridimensionamento con lato corto a 1080 px;
    - Autocontrasto leggero;
    - Codifica finale JPEG.

    Args:
        dati_foto: Il contenuto binario dell'immagine sorgente (JPEG, PNG o WEBP).
        canale: Canale di destinazione ('facebook' o 'instagram').
        proporzione: Opzionale proporzione forzata ('1:1' o '4:5').

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

        # 3. Ritaglio al centro solo se fuori da 4:5 – 1,91:1 (R-21, R-42)
        ratio_corrente = _calcola_ratio(img.width, img.height)
        target = _ratio_target(
            ratio_corrente=ratio_corrente,
            proporzioni_ammesse=PROPORZIONI_CANALE[canale_norm],
            proporzione_richiesta=proporzione,
        )

        if target is not None:
            img = _ritaglia_al_centro(img, target)

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
