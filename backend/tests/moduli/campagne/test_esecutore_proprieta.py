"""Proprietà dell'esecutore (RT-04): qualunque dimensione valida, nessuna eccezione."""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from app.moduli.campagne import sistemazione_foto as regole
from app.moduli.campagne.esecutore import comando_originale, esegui
from tests import immagini

pytest.importorskip("hypothesis")

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    st.integers(40, 320),
    st.integers(40, 320),
    st.sampled_from(["facebook", "instagram"]),
    st.one_of(
        st.none(),
        st.builds(
            lambda x, y, w, h: {"x": x, "y": y, "larghezza": w, "altezza": h},
            st.floats(0, 0.6),
            st.floats(0, 0.6),
            st.floats(0.05, 0.4),
            st.floats(0.05, 0.4),
        ),
    ),
)
def test_qualunque_dimensione_valida_esce_nell_intervallo_con_lato_corto_1080(
    larghezza, altezza, canale, soggetto
) -> None:
    buffer = BytesIO()
    immagini.gradiente((larghezza, altezza), (20, 30, 40), (220, 200, 180)).save(
        buffer, "PNG"
    )
    uscita = Image.open(
        BytesIO(
            esegui(
                buffer.getvalue(),
                comando_originale(canale=canale, soggetto_box=soggetto),
            )
        )
    )
    assert min(uscita.size) == regole.LATO_CORTO_TARGET
    rapporto = uscita.width / uscita.height
    tolleranza = 2 * regole.TOLLERANZA_PROPORZIONE
    assert (
        regole.RATIO_MINIMO - tolleranza
        <= rapporto
        <= regole.RATIO_MASSIMO + tolleranza
    )
