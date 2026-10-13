"""Sistemazione delle foto per anteprima e pubblicazione (Corsia 2 · Task T3-21).

Implementa la logica locale con Pillow secondo spec R-21, R-42 e CA-81:
1. Rotazione dell'immagine secondo i metadati di orientamento EXIF;
2. Rimozione di qualsiasi metadato GPS e dato sensibile;
3. Ritaglio al centro nelle proporzioni ammesse dalla scheda del canale (1:1 o 4:5),
   applicato solo se la foto è fuori dalle proporzioni consentite;
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

# Proporzioni ammesse per canale secondo spec R-21 e R-42 (MVP: 1:1 o 4:5)
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


def _trova_proporzione_target(
    ratio_corrente: float,
    proporzioni_ammesse: tuple[tuple[int, int], ...],
    proporzione_richiesta: str | None = None,
) -> tuple[int, int] | None:
    """Verifica se la foto è già conforme a una proporzione ammessa.

    Se la foto è già in proporzione (entro tolleranza), restituisce None (nessun ritaglio).
    Altrimenti restituisce la proporzione target ottimale (quella più vicina
    che preserva la massima porzione dell'immagine) o quella richiesta.
    """
    # Mappa delle proporzioni numeriche
    ratios_ammessi = {f"{w}:{h}": (w, h, w / h) for (w, h) in proporzioni_ammesse}

    if proporzione_richiesta:
        if proporzione_richiesta not in ratios_ammessi:
            raise DatiNonValidi(
                f"Proporzione '{proporzione_richiesta}' non ammessa. "
                f"Valori validi: {', '.join(ratios_ammessi.keys())}."
            )
        w, h, target_r = ratios_ammessi[proporzione_richiesta]
        # Se già conforme alla proporzione richiesta, nessun ritaglio
        if abs(ratio_corrente - target_r) <= TOLLERANZA_PROPORZIONE:
            return None
        return (w, h)

    # Verifica se la foto rientra già in una qualsiasi proporzione ammessa
    for _, (w, h, target_r) in ratios_ammessi.items():
        if abs(ratio_corrente - target_r) <= TOLLERANZA_PROPORZIONE:
            return None  # Già conforme!

    # Se fuori da tutte le proporzioni ammesse, sceglie quella con distanza minima
    # (minimizza i pixel tagliati per conservare al meglio l'inquadratura)
    proporzione_ottimale = min(
        ratios_ammessi.values(),
        key=lambda item: abs(ratio_corrente - item[2]),
    )
    return (proporzione_ottimale[0], proporzione_ottimale[1])


def _ritaglia_al_centro(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Esegue un ritaglio al centro per allineare l'immagine alle proporzioni target."""
    target_ratio = target_w / target_h
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
    - Ritaglio al centro se la foto non è in 1:1 o 4:5;
    - Ridimensionamento con lato corto a 1080 px;
    - Autocontrasto leggero;
    - Codifica finale JPEG.

    Args:
        dati_foto: Il contenuto binario dell'immagine sorgente (JPEG, PNG o WEBP).
        canale: Canale di destinazione ('facebook' o 'instagram').
        proporzione: Opzionale stringa di proporzione forzata ('1:1' o '4:5').

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

        # 3. Ritaglio al centro solo se fuori dalle proporzioni della scheda del canale (R-21, R-42)
        ratio_corrente = _calcola_ratio(img.width, img.height)
        proporzioni_ammesse = PROPORZIONI_CANALE[canale_norm]
        target_prop = _trova_proporzione_target(
            ratio_corrente=ratio_corrente,
            proporzioni_ammesse=proporzioni_ammesse,
            proporzione_richiesta=proporzione,
        )

        if target_prop is not None:
            img = _ritaglia_al_centro(img, target_prop[0], target_prop[1])

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
