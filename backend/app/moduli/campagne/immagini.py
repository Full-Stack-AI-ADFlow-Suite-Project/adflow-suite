"""Modulo per l'ispezione binaria e la validazione delle immagini (Corsia 2).

Implementato interamente con la libreria standard di Python (`struct`),
senza dipendenze esterne, garantendo:
- Ispezione ad alte prestazioni dei formati PNG, JPEG e WEBP;
- Estrazione esatta di larghezza e altezza da header e metadati binari;
- Validazione delle regole di business (Spec R-13, CA-13): lato corto >= 1080 px;
- Sicurezza e protezione DoS (Defense in Depth): limiti massimi su larghezza,
  altezza e pixel totali (anti-decompression bomb).
"""

import struct
from typing import NamedTuple

from app.core.errori import DatiNonValidi

# Limiti dimensionali e quantitativi (Spec R-13 e vincoli di sicurezza)
MIN_LATO_CORTO: int = 1080
MAX_WIDTH: int = 8192
MAX_HEIGHT: int = 8192
MAX_PIXELS: int = 36_000_000
MAX_FOTO_PER_GRUPPO: int = 20


class InfoImmagine(NamedTuple):
    """Metadati estratti dall'analisi binaria dell'immagine."""

    larghezza: int
    altezza: int
    mime: str
    estensione: str


def _estrai_dimensioni_png(dati: bytes) -> tuple[int, int]:
    """Estrae larghezza e altezza da un flusso PNG tramite chunk IHDR."""
    if len(dati) < 24 or dati[:8] != b"\x89PNG\r\n\x1a\n":
        raise DatiNonValidi("File PNG non valido o corrotto.")

    if dati[12:16] != b"IHDR":
        raise DatiNonValidi("Intestazione IHDR non trovata nell'immagine PNG.")

    larghezza, altezza = struct.unpack(">II", dati[16:24])
    if larghezza <= 0 or altezza <= 0:
        raise DatiNonValidi("Dimensioni PNG non valide (<= 0 px).")
    return larghezza, altezza


def _estrai_dimensioni_jpeg(dati: bytes) -> tuple[int, int]:
    """Estrae larghezza e altezza da un flusso JPEG scansionando i marker SOF."""
    if len(dati) < 4 or not (dati[0] == 0xFF and dati[1] == 0xD8):
        raise DatiNonValidi("File JPEG non valido o corrotto.")

    offset = 2
    lunghezza_totale = len(dati)

    # Marker SOF validi (Start of Frame) che contengono dimensioni
    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }

    while offset < lunghezza_totale:
        # Nel formato JPEG ogni marker deve iniziare con il byte 0xFF
        if dati[offset] != 0xFF:
            raise DatiNonValidi("File JPEG non valido o corrotto: marker inatteso.")

        # Salta byte di padding 0xFF consecutivi
        while offset < lunghezza_totale and dati[offset] == 0xFF:
            offset += 1

        if offset >= lunghezza_totale:
            break

        marker = dati[offset]
        offset += 1

        # Marker di stop o restart senza lunghezza
        if marker == 0xD9:  # EOI (End of Image)
            break
        if 0xD0 <= marker <= 0xD7:  # RST0..RST7
            continue
        if marker == 0x01:  # TEM
            continue

        if offset + 2 > lunghezza_totale:
            break

        (lunghezza_segmento,) = struct.unpack(">H", dati[offset : offset + 2])
        if lunghezza_segmento < 2:
            break

        if marker in sof_markers:
            if offset + 7 > lunghezza_totale:
                break
            # Struttura SOF: 2B lunghezza, 1B precisione, 2B altezza, 2B larghezza
            altezza, larghezza = struct.unpack(">HH", dati[offset + 3 : offset + 7])
            if larghezza <= 0 or altezza <= 0:
                raise DatiNonValidi("Dimensioni JPEG non valide (<= 0 px).")
            return larghezza, altezza

        offset += lunghezza_segmento

    raise DatiNonValidi("Impossibile estrarre le dimensioni dall'immagine JPEG.")


def _estrai_dimensioni_webp(dati: bytes) -> tuple[int, int]:
    """Estrae dimensioni da un flusso WEBP (supporta VP8, VP8L, VP8X)."""
    if len(dati) < 16 or dati[:4] != b"RIFF" or dati[8:12] != b"WEBP":
        raise DatiNonValidi("File WEBP non valido o corrotto.")

    formato_chunk = dati[12:16]

    # 1. VP8 (lossy)
    if formato_chunk == b"VP8 ":
        if len(dati) < 30:
            raise DatiNonValidi("Chunk VP8 incompleto.")
        # Start code VP8: 0x9D 0x01 0x2A a offset 23
        if dati[23:26] != b"\x9d\x01\x2a":
            raise DatiNonValidi("Intestazione frame VP8 non valida.")
        # Larghezza e altezza a 14 bit (little endian)
        raw_w = struct.unpack("<H", dati[26:28])[0] & 0x3FFF
        raw_h = struct.unpack("<H", dati[28:30])[0] & 0x3FFF
        if raw_w <= 0 or raw_h <= 0:
            raise DatiNonValidi("Dimensioni WEBP non valide (<= 0 px).")
        return raw_w, raw_h

    # 2. VP8L (lossless)
    if formato_chunk == b"VP8L":
        if len(dati) < 25:
            raise DatiNonValidi("Chunk VP8L incompleto.")
        # Byte di firma 0x2F a offset 20
        if dati[20] != 0x2F:
            raise DatiNonValidi("Firma VP8L non valida.")
        # 32 bit a offset 21: 14 bit width-1, 14 bit height-1
        valore = struct.unpack("<I", dati[21:25])[0]
        larghezza = (valore & 0x3FFF) + 1
        altezza = ((valore >> 14) & 0x3FFF) + 1
        return larghezza, altezza

    # 3. VP8X (Extended canvas)
    if formato_chunk == b"VP8X":
        if len(dati) < 30:
            raise DatiNonValidi("Chunk VP8X incompleto.")
        # Larghezza canvas a 24 bit little-endian (offset 24..27) + 1
        larghezza = 1 + (dati[24] | (dati[25] << 8) | (dati[26] << 16))
        # Altezza canvas a 24 bit little-endian (offset 27..30) + 1
        altezza = 1 + (dati[27] | (dati[28] << 8) | (dati[29] << 16))
        return larghezza, altezza

    raise DatiNonValidi(
        f"Formato WEBP non supportato ({formato_chunk.decode('ascii', errors='ignore')})."
    )


def analizza_e_valida_immagine(contenuto: bytes) -> InfoImmagine:
    """Ispeziona il payload binario, rileva il formato ed esegue tutte le validazioni.

    Args:
        contenuto: byte dell'immagine caricata.

    Returns:
        InfoImmagine contenente larghezza, altezza, mime ed estensione.

    Raises:
        DatiNonValidi: se il file non è un'immagine ammessa, è corrotto,
            o vìola i criteri dimensionali e di sicurezza (R-13, CA-13).
    """
    if not contenuto:
        raise DatiNonValidi("Il file immagine è vuoto.")

    # Rilevamento formato dai magic bytes
    if contenuto.startswith(b"\x89PNG\r\n\x1a\n"):
        larghezza, altezza = _estrai_dimensioni_png(contenuto)
        mime = "image/png"
        estensione = ".png"
    elif contenuto.startswith(b"\xff\xd8\xff"):
        larghezza, altezza = _estrai_dimensioni_jpeg(contenuto)
        mime = "image/jpeg"
        estensione = ".jpg"
    elif (
        len(contenuto) >= 12 and contenuto[:4] == b"RIFF" and contenuto[8:12] == b"WEBP"
    ):
        larghezza, altezza = _estrai_dimensioni_webp(contenuto)
        mime = "image/webp"
        estensione = ".webp"
    else:
        raise DatiNonValidi(
            "Il file non è un'immagine valida o supportata (ammessi JPG, PNG, WEBP)."
        )

    # Validazione dimensioni minime (Spec R-13, CA-13: lato corto >= 1080 px)
    lato_corto = min(larghezza, altezza)
    if lato_corto < MIN_LATO_CORTO:
        raise DatiNonValidi(
            f"Il lato corto dell'immagine ({lato_corto} px) è inferiore al minimo richiesto di {MIN_LATO_CORTO} px."
        )

    # Protezione anti-DoS: limiti dimensionali massimi (anti-ratio estremi)
    if larghezza > MAX_WIDTH or altezza > MAX_HEIGHT:
        raise DatiNonValidi(
            f"Le dimensioni dell'immagine ({larghezza}x{altezza} px) superano il limite massimo consentito di {MAX_WIDTH}x{MAX_HEIGHT} px."
        )

    # Protezione anti-DoS: Pixel Flood / Decompression Bomb
    pixel_totali = larghezza * altezza
    if pixel_totali > MAX_PIXELS:
        raise DatiNonValidi(
            f"L'immagine supera il limite massimo di densità consentito ({pixel_totali} pixel su {MAX_PIXELS} max)."
        )

    return InfoImmagine(
        larghezza=larghezza,
        altezza=altezza,
        mime=mime,
        estensione=estensione,
    )
