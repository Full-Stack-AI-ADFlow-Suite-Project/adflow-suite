"""Apertura delle foto in sRGB (ADR-124, RT-02 di `docs/ritocco-corsia.md`).

L'iPhone e diversi Android recenti salvano i JPEG con il profilo Display P3, più
ampio di sRGB: i numeri dei pixel hanno senso solo insieme al profilo. Ignorarlo
spegne i colori saturi (pomodoro, fiori, smalti) e fa giudicare male la
dominante. Questa è l'**unica** funzione che decodifica una foto per sistemarla,
misurarla o mandarla all'AI: Pillow decodifica, poi si converte in sRGB; chi
riceve l'immagine lavora sempre in sRGB.

Regole (nota 12.1):
- i limiti di oggi: file illeggibile o oltre 36 MP → ``DatiNonValidi``;
- ``lato_max`` accelera i JPEG con ``draft()`` (decodifica a scala ridotta); non
  ridimensiona: l'immagine può restare più grande e ci pensa chi la usa;
- rotazione da EXIF; trasparenza appiattita su bianco *prima* della conversione;
- profilo → sRGB, intento relativo colorimetrico con compensazione del punto nero;
- profilo mancante, già sRGB, o di un altro spazio rispetto al modo dell'immagine:
  nessuna conversione; profilo rotto: avviso nel log e nessuna eccezione, la foto
  resta pubblicabile come prima;
- JPEG CMYK senza profilo: la conversione semplice di Pillow, come oggi.
"""

from __future__ import annotations

import logging
import math
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageCms, ImageOps

from app.core.errori import DatiNonValidi

from .immagini import MAX_PIXELS

_log = logging.getLogger(__name__)

# Lo spazio colore del profilo che si accetta per ogni modo dell'immagine.
_SPAZIO_PER_MODO = {"RGB": "RGB", "L": "GRAY", "CMYK": "CMYK"}


@lru_cache(maxsize=1)
def profilo_srgb_bytes() -> bytes:
    """Il profilo sRGB da incorporare nel JPEG in uscita (pochi KB, nessun dato personale)."""
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


@lru_cache(maxsize=1)
def _srgb() -> ImageCms.ImageCmsProfile:
    return ImageCms.ImageCmsProfile(BytesIO(profilo_srgb_bytes()))


def _e_gia_srgb(profilo: ImageCms.ImageCmsProfile) -> bool:
    """Il profilo RGB standard (IEC 61966-2.1 e simili): convertirlo non cambierebbe nulla."""
    try:
        return "srgb" in ImageCms.getProfileDescription(profilo).lower()
    except ImageCms.PyCMSError:
        return False


def _converti_con_profilo(
    immagine: Image.Image, dati_profilo: bytes
) -> Image.Image | None:
    """L'immagine in sRGB, oppure None se il profilo non si applica (e si sa perché)."""
    try:
        sorgente = ImageCms.ImageCmsProfile(BytesIO(dati_profilo))
        spazio = sorgente.profile.xcolor_space.strip()
        if spazio != _SPAZIO_PER_MODO.get(immagine.mode):
            return None  # profilo di un altro spazio: lo si ignora senza rumore
        if immagine.mode == "RGB" and _e_gia_srgb(sorgente):
            return None
        return ImageCms.profileToProfile(
            immagine,
            sorgente,
            _srgb(),
            renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
            outputMode="RGB",
            flags=ImageCms.Flags.BLACKPOINTCOMPENSATION,
        )
    except (ImageCms.PyCMSError, OSError, ValueError, TypeError, SyntaxError) as exc:
        _log.warning("Profilo colore illeggibile, ignorato: %s", exc)
        return None


def _a_rgb(immagine: Image.Image, dati_profilo: bytes | None) -> Image.Image:
    """Porta qualunque modo di Pillow in RGB, convertendo con il profilo se c'è."""
    ha_trasparenza = (
        "A" in immagine.mode
        or (immagine.mode == "P" and "transparency" in immagine.info)
        or immagine.mode in ("RGBA", "LA", "PA")
    )
    if ha_trasparenza:
        # Sfondo bianco prima della conversione: il bianco è bianco in ogni spazio RGB.
        if immagine.mode in ("LA", "PA"):
            dati_profilo = None  # il profilo grigio non vale più dopo l'RGBA
        rgba = immagine.convert("RGBA")
        sfondo = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        sfondo.paste(rgba, mask=rgba.split()[3])
        immagine = sfondo.convert("RGB")
    elif immagine.mode == "P":
        immagine = immagine.convert("RGB")
    elif immagine.mode == "1":
        immagine = immagine.convert("L")

    if dati_profilo and immagine.mode in _SPAZIO_PER_MODO:
        convertita = _converti_con_profilo(immagine, dati_profilo)
        if convertita is not None:
            return convertita
    return immagine if immagine.mode == "RGB" else immagine.convert("RGB")


def apri_in_srgb(
    dati: bytes, lato_max: int | None = None, max_pixel: int = MAX_PIXELS
) -> Image.Image:
    """Decodifica ``dati`` e restituisce un'immagine RGB in sRGB, dritta (EXIF applicato).

    Args:
        dati: i byte di un JPEG, PNG o WEBP.
        lato_max: se c'è, accelera la decodifica dei JPEG riducendo la scala (1/2,
            1/4, 1/8) finché il lato lungo resta almeno ``lato_max``. Non ridimensiona.
        max_pixel: limite anti-decompression-bomb (default 36 MP, come il caricamento).

    Raises:
        DatiNonValidi: file illeggibile o troppo grande.
    """
    try:
        grezza = Image.open(BytesIO(dati))
    except Exception as exc:
        raise DatiNonValidi("File immagine non valido o corrotto.") from exc

    try:
        larghezza, altezza = grezza.size
        if larghezza <= 0 or altezza <= 0:
            raise DatiNonValidi("Dimensioni dell'immagine non valide (<= 0).")
        if larghezza * altezza > max_pixel:
            raise DatiNonValidi(
                f"Immagine troppo grande ({larghezza}x{altezza} px). "
                f"Il limite consentito è di {max_pixel} pixel."
            )

        if lato_max and grezza.format == "JPEG" and max(larghezza, altezza) > lato_max:
            scala = lato_max / max(larghezza, altezza)
            grezza.draft(
                None, (math.ceil(larghezza * scala), math.ceil(altezza * scala))
            )

        dati_profilo = grezza.info.get("icc_profile")
        try:
            try:
                dritta = ImageOps.exif_transpose(grezza)
            except (OSError, SyntaxError, ValueError):
                raise
            except Exception:  # EXIF illeggibile: la foto resta com'è
                dritta = grezza.copy()
            risultato = _a_rgb(dritta, dati_profilo)
            # Dopo la conversione il colore è sRGB per contratto: il profilo non serve.
            risultato.info.pop("icc_profile", None)
            return risultato
        except (OSError, SyntaxError, ValueError) as exc:
            raise DatiNonValidi("File immagine non valido o corrotto.") from exc
    finally:
        grezza.close()
