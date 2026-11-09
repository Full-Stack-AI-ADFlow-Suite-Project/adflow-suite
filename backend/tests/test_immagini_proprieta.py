"""Proprietà degli strumenti di test per le immagini (RT-01, ADR-124).

Girano solo con hypothesis installato (si salta altrimenti): da RT-01 la CI lo
installa da `requirements-accettazione.txt`.
"""

from io import BytesIO

import pytest
from PIL import Image, ImageCms

from tests import immagini

pytest.importorskip("hypothesis")

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

colori = st.tuples(*[st.integers(0, 255)] * 3)

_SRGB = ImageCms.ImageCmsProfile(BytesIO(immagini.profilo_icc("srgb")))


@given(colori, colori)
def test_delta_e_e_una_distanza(a, b) -> None:
    assert immagini.delta_e(a, a) == 0.0
    assert immagini.delta_e(a, b) == pytest.approx(immagini.delta_e(b, a))
    assert immagini.delta_e(a, b) >= 0.0


@given(colori)
@settings(max_examples=60)
def test_srgb_generato_non_cambia_nessun_colore(colore) -> None:
    pixel = Image.new("RGB", (1, 1), colore)
    uscita = ImageCms.profileToProfile(
        pixel, _SRGB, _SRGB, renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC
    ).getpixel((0, 0))
    assert max(abs(u - c) for u, c in zip(uscita, colore)) <= 1


@given(st.integers(1, 100), st.integers(1, 100), colori)
def test_la_tinta_unita_ha_il_colore_e_le_dimensioni_chieste(
    larghezza, altezza, colore
) -> None:
    img = immagini.tinta_unita(colore, (larghezza, altezza))
    assert img.size == (larghezza, altezza)
    assert immagini.media_lab(img) == pytest.approx(
        immagini.media_lab(Image.new("RGB", (1, 1), colore))
    )
