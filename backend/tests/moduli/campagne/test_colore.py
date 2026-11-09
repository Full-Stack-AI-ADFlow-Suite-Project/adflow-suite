"""Apertura delle foto in sRGB (RT-02, ADR-124, nota 12.1).

Immagini sintetiche (`tests/immagini.py`); nessun database.
"""

from __future__ import annotations

import logging
from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from app.core.errori import DatiNonValidi
from app.moduli.campagne.colore import apri_in_srgb, profilo_srgb_bytes
from app.moduli.campagne.sistemazione_foto import sistema_foto_buffer
from tests import immagini

P3 = immagini.profilo_icc("p3")
SRGB = immagini.profilo_icc("srgb")


def _pixel(dati: bytes, punto=(0, 0)) -> tuple[int, int, int]:
    return apri_in_srgb(dati).getpixel(punto)


def _vicino(a, b, tolleranza: int) -> bool:
    return all(abs(x - y) <= tolleranza for x, y in zip(a, b))


# --- Conversione ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("p3", "srgb"),
    [
        ((220, 60, 40), (239, 35, 17)),  # pomodoro
        ((60, 150, 60), (0, 152, 44)),  # basilico
        ((230, 90, 140), (249, 77, 141)),  # rosa
        ((205, 160, 110), (213, 158, 102)),  # pane
    ],
)
def test_png_p3_diventa_srgb(p3, srgb) -> None:
    dati = immagini.png_con_icc(immagini.tinta_unita(p3), P3)
    assert _vicino(_pixel(dati), srgb, 2)


def test_webp_con_icc_diventa_srgb() -> None:
    dati = immagini.webp_con_icc(immagini.tinta_unita((220, 60, 40)), P3)
    assert _vicino(_pixel(dati), (239, 35, 17), 2)


def test_jpeg_p3_diventa_srgb_entro_la_compressione() -> None:
    dati = immagini.jpeg_con_exif(
        immagini.tinta_unita((220, 60, 40), (64, 64)), profilo=P3
    )
    assert _vicino(_pixel(dati, (32, 32)), (239, 35, 17), 4)


def test_i_neutri_restano_invariati() -> None:
    for grigio in ((0, 0, 0), (60, 60, 60), (128, 128, 128), (255, 255, 255)):
        dati = immagini.png_con_icc(immagini.tinta_unita(grigio), P3)
        assert _vicino(_pixel(dati), grigio, 1)


def test_foto_senza_profilo_resta_invariata() -> None:
    img = immagini.gradiente((64, 8), (10, 20, 30), (200, 150, 90))
    buffer = BytesIO()
    img.save(buffer, "PNG")
    uscita = apri_in_srgb(buffer.getvalue())
    assert (np.asarray(uscita) == np.asarray(img)).all()


def test_foto_gia_srgb_resta_invariata() -> None:
    img = immagini.gradiente((64, 8), (10, 20, 30), (200, 150, 90))
    uscita = apri_in_srgb(immagini.png_con_icc(img, SRGB))
    assert (np.asarray(uscita) == np.asarray(img)).all()


def test_il_risultato_e_sempre_rgb_senza_profilo() -> None:
    uscita = apri_in_srgb(immagini.png_con_icc(immagini.tinta_unita((9, 9, 9)), P3))
    assert uscita.mode == "RGB"
    assert "icc_profile" not in uscita.info


# --- Modi particolari ------------------------------------------------------------


def test_profilo_rotto_non_solleva_e_lascia_la_foto_com_e(caplog) -> None:
    dati = immagini.png_con_icc(
        immagini.tinta_unita((220, 60, 40)), b"non un profilo" * 20
    )
    with caplog.at_level(logging.WARNING):
        assert _pixel(dati) == (220, 60, 40)
    assert any("Profilo colore" in r.message for r in caplog.records)


def test_cmyk_senza_profilo_usa_la_conversione_semplice() -> None:
    uscita = apri_in_srgb(immagini.jpeg_cmyk((16, 16), 40))
    assert uscita.mode == "RGB"
    assert uscita.size == (16, 16)


def test_scala_di_grigi_e_un_bit_diventano_rgb() -> None:
    for modo in ("L", "1"):
        buffer = BytesIO()
        Image.new(modo, (12, 8), 1).save(buffer, "PNG")
        uscita = apri_in_srgb(buffer.getvalue())
        assert uscita.mode == "RGB"
        assert uscita.size == (12, 8)


def test_trasparenza_su_bianco_prima_della_conversione() -> None:
    img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    buffer = BytesIO()
    img.save(buffer, "PNG", icc_profile=P3)
    assert _vicino(_pixel(buffer.getvalue()), (255, 255, 255), 1)


def test_palette_con_trasparenza_non_solleva() -> None:
    img = Image.new("P", (8, 8), 0)
    img.putpalette([200, 20, 20] + [0] * 765)
    buffer = BytesIO()
    img.save(buffer, "PNG", transparency=0)
    assert _vicino(_pixel(buffer.getvalue()), (255, 255, 255), 1)


def test_orientamento_exif_applicato() -> None:
    dati = immagini.jpeg_con_exif(
        immagini.tinta_unita((90, 90, 90), (40, 20)), orientamento=6
    )
    assert apri_in_srgb(dati).size == (20, 40)


# --- Limiti ----------------------------------------------------------------------


def test_file_illeggibile_solleva_dati_non_validi() -> None:
    for dati in (b"", b"non un'immagine", b"\xff\xd8\xff"):
        with pytest.raises(DatiNonValidi):
            apri_in_srgb(dati)


def test_oltre_il_limite_di_pixel_solleva_dati_non_validi() -> None:
    dati = immagini.jpeg_qualita(immagini.tinta_unita((1, 2, 3), (500, 500)))
    with pytest.raises(DatiNonValidi, match="troppo grande"):
        apri_in_srgb(dati, max_pixel=100_000)


def test_lato_max_riduce_la_scala_dei_jpeg_ma_non_oltre() -> None:
    dati = immagini.jpeg_qualita(immagini.tinta_unita((1, 2, 3), (2000, 1500)))
    ridotta = apri_in_srgb(dati, lato_max=500)
    assert max(ridotta.size) >= 500
    assert max(ridotta.size) < 2000
    intera = apri_in_srgb(dati, lato_max=5000)
    assert intera.size == (2000, 1500)
    assert apri_in_srgb(dati).size == (2000, 1500)


def test_lato_max_non_tocca_i_formati_senza_draft() -> None:
    buffer = BytesIO()
    immagini.tinta_unita((1, 2, 3), (2000, 1500)).save(buffer, "PNG")
    assert apri_in_srgb(buffer.getvalue(), lato_max=500).size == (2000, 1500)


# --- Uscita della sistemazione -----------------------------------------------------


def test_il_jpeg_in_uscita_porta_il_profilo_srgb_e_nessun_exif() -> None:
    dati = immagini.jpeg_con_exif(
        immagini.tinta_unita((220, 60, 40), (1200, 1200)),
        orientamento=1,
        gps=True,
        profilo=P3,
    )
    uscita = Image.open(BytesIO(sistema_foto_buffer(dati)))
    assert uscita.info.get("icc_profile") == profilo_srgb_bytes()
    exif = uscita.getexif()
    assert not exif and not exif.get_ifd(0x8825)
    assert uscita.size == (1080, 1080)


def test_il_pomodoro_p3_esce_come_pomodoro_srgb() -> None:
    dati = immagini.png_con_icc(immagini.tinta_unita((220, 60, 40), (1200, 1200)), P3)
    uscita = Image.open(BytesIO(sistema_foto_buffer(dati)))
    assert _vicino(uscita.getpixel((540, 540)), (239, 35, 17), 4)


def test_una_foto_senza_profilo_esce_con_gli_stessi_colori() -> None:
    buffer = BytesIO()
    immagini.tinta_unita((120, 90, 60), (1200, 1200)).save(buffer, "PNG")
    uscita = Image.open(BytesIO(sistema_foto_buffer(buffer.getvalue())))
    assert _vicino(uscita.getpixel((540, 540)), (120, 90, 60), 3)
