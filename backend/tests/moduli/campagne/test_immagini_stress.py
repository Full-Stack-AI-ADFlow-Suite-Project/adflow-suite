"""Prove dure sul controllo delle immagini (soglia 480 px, proporzioni 8:1, anti-DoS).

Si provano i confini al pixel, formati che non sono ammessi (HEIC, GIF, SVG,
BMP, TIFF, PDF) anche travestiti da JPG, e file troncati o corrotti: il controllo
deve sempre dire 422 (DatiNonValidi) e mai andare in errore in altro modo.
"""

import random
import struct
import zlib

import pytest

from app.core.errori import DatiNonValidi
from app.moduli.campagne.immagini import (
    MAX_ASPECT_RATIO,
    MAX_HEIGHT,
    MAX_PIXELS,
    MAX_WIDTH,
    MIN_LATO_CORTO,
    analizza_e_valida_immagine,
)


def png(w: int, h: int) -> bytes:
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", len(ihdr))
        + b"IHDR"
        + ihdr
        + crc
        + b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def jpeg(w: int, h: int) -> bytes:
    sof = (
        b"\x08" + struct.pack(">HH", h, w) + b"\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01"
    )
    return (
        b"\xff\xd8" + b"\xff\xc0" + struct.pack(">H", len(sof) + 2) + sof + b"\xff\xd9"
    )


def webp_lossy(w: int, h: int) -> bytes:
    corpo = b"\x00\x00\x00" + b"\x9d\x01\x2a" + struct.pack("<HH", w, h) + b"\x00" * 8
    chunk = b"VP8 " + struct.pack("<I", len(corpo)) + corpo
    return b"RIFF" + struct.pack("<I", 4 + len(chunk)) + b"WEBP" + chunk


def webp_lossless(w: int, h: int) -> bytes:
    valore = (w - 1) | ((h - 1) << 14)
    corpo = b"\x2f" + struct.pack("<I", valore) + b"\x00" * 4
    chunk = b"VP8L" + struct.pack("<I", len(corpo)) + corpo
    return b"RIFF" + struct.pack("<I", 4 + len(chunk)) + b"WEBP" + chunk


def webp_esteso(w: int, h: int) -> bytes:
    corpo = (
        b"\x00\x00\x00\x00"
        + (w - 1).to_bytes(3, "little")
        + (h - 1).to_bytes(3, "little")
    )
    chunk = b"VP8X" + struct.pack("<I", len(corpo)) + corpo
    return b"RIFF" + struct.pack("<I", 4 + len(chunk)) + b"WEBP" + chunk


FORMATI = [png, jpeg, webp_lossy, webp_lossless, webp_esteso]


def esito(dati: bytes):
    try:
        return analizza_e_valida_immagine(dati)
    except DatiNonValidi as errore:
        return errore


@pytest.mark.parametrize("formato", FORMATI)
@pytest.mark.parametrize(
    "w, h, ammessa",
    [
        (MIN_LATO_CORTO, MIN_LATO_CORTO, True),
        (MIN_LATO_CORTO - 1, MIN_LATO_CORTO, False),
        (MIN_LATO_CORTO, MIN_LATO_CORTO - 1, False),
        (MIN_LATO_CORTO, 640, True),
        (640, MIN_LATO_CORTO, True),
        (1080, 1350, True),
        (4000, 3000, True),
        # proporzioni: 8:1 passa, un pixel oltre no
        (MIN_LATO_CORTO * 8, MIN_LATO_CORTO, True),
        (MIN_LATO_CORTO * 8 + 1, MIN_LATO_CORTO, False),
        (MIN_LATO_CORTO, MIN_LATO_CORTO * 8, True),
        (MIN_LATO_CORTO, MIN_LATO_CORTO * 8 + 1, False),
        # anti-DoS
        (MAX_WIDTH, 4000, True),
        (MAX_WIDTH + 1, 4000, False),
        (4000, MAX_HEIGHT + 1, False),
        (6001, 6000, False),  # 36,006 Mpx > 36 Mpx
        (6000, 6000, True),
        (1, 1, False),
        (65000, 65000, False),
    ],
)
def test_confini_al_pixel_per_ogni_formato(formato, w, h, ammessa):
    if formato in (webp_lossy,) and max(w, h) > 16383:
        pytest.skip("il VP8 lossy ha 14 bit per lato")
    if formato is webp_lossless and max(w, h) > 16384:
        pytest.skip("il VP8L ha 14 bit per lato")
    risultato = esito(formato(w, h))
    assert isinstance(risultato, DatiNonValidi) is (not ammessa), (
        formato.__name__,
        w,
        h,
        risultato,
    )
    if ammessa:
        assert (risultato.larghezza, risultato.altezza) == (w, h)


def test_il_rapporto_massimo_e_otto_a_uno():
    assert MAX_ASPECT_RATIO == 8.0 and MIN_LATO_CORTO == 480
    assert MAX_PIXELS == 36_000_000


@pytest.mark.parametrize(
    "contenuto",
    [
        b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00" * 64,  # HEIC
        b"\x00\x00\x00\x18ftypheix\x00\x00\x00\x00" + b"\x00" * 64,
        b"\x00\x00\x00\x1cftypavif\x00\x00\x00\x00" + b"\x00" * 64,  # AVIF
        b"GIF89a\x01\x00\x01\x00" + b"\x00" * 64,
        b"<svg xmlns='http://www.w3.org/2000/svg' width='2000' height='2000'/>",
        b"BM" + b"\x00" * 64,
        b"II*\x00" + b"\x00" * 64,
        b"%PDF-1.7\n" + b"\x00" * 64,
        b"MZ" + b"\x00" * 64,
        b"",
        b"\xff",
        b"\xff\xd8",
        b"\x89PNG",
    ],
)
def test_formati_non_ammessi_e_file_vuoti_o_troncati_danno_422(contenuto):
    assert isinstance(esito(contenuto), DatiNonValidi)


def test_heic_travestito_da_jpg_si_ferma_ai_primi_byte():
    """Il tipo si legge dai byte, non dall'estensione né dal tipo dichiarato dal browser."""
    finto_jpg = b"\x00\x00\x00\x18ftypheic" + b"\x00" * 200
    assert isinstance(esito(finto_jpg), DatiNonValidi)


@pytest.mark.parametrize("seme", range(400))
def test_byte_a_caso_non_mandano_mai_in_errore_il_controllo(seme):
    rng = random.Random(seme)
    base = rng.choice([png(800, 800), jpeg(800, 800), webp_lossy(800, 800), b""])
    dati = bytearray(base)
    for _ in range(rng.randrange(0, 8)):
        if dati and rng.random() < 0.7:
            dati[rng.randrange(len(dati))] = rng.randrange(256)
        elif rng.random() < 0.5:
            dati = dati[: rng.randrange(len(dati) + 1)]
        else:
            dati += bytes(rng.randrange(256) for _ in range(rng.randrange(0, 20)))
    risultato = esito(bytes(dati))  # niente eccezioni diverse da DatiNonValidi
    assert risultato is not None
