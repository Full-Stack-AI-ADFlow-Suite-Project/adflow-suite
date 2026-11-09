"""La finestra e le barre (RT-16): casi scelti e proprietà."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image, ImageDraw

from app.core.errori import DatiNonValidi
from app.moduli.campagne import ritocco_catalogo as catalogo
from app.moduli.campagne import sistemazione_foto as regole
from app.moduli.campagne.esecutore import Comando, esegui
from app.moduli.campagne.finestra import Finestra, calcola_finestra
from tests import immagini

pytest.importorskip("hypothesis")

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

TOL = regole.TOLLERANZA_PROPORZIONE + 1e-6


def _px(finestra: Finestra, w: int, h: int):
    x, y, bw, bh = finestra.b
    return x * w, y * h, (x + bw) * w, (y + bh) * h


# --- Casi scelti -------------------------------------------------------------------


def test_foto_nell_intervallo_senza_richieste_resta_intera():
    esito = calcola_finestra(3000, 2000)
    assert esito.barre is False
    assert esito.finestra.b == pytest.approx((0, 0, 1, 1))
    assert esito.finestra.rapporto == pytest.approx(1.5)


def test_foto_troppo_larga_con_poco_da_tagliare_si_taglia_al_centro():
    # 2:1 → 1,91:1 toglie il 4,5%: sotto il 10%
    esito = calcola_finestra(4000, 2000)
    assert esito.barre is False
    assert esito.finestra.rapporto == pytest.approx(regole.RATIO_MASSIMO, abs=TOL)
    x, y, w, h = esito.finestra.b
    assert x == pytest.approx((1 - w) / 2) and (y, h) == pytest.approx((0, 1))


def test_foto_molto_stretta_senza_soggetto_va_in_barre():
    # 1:3 → 4:5 toglierebbe il 73%: sopra ogni soglia
    esito = calcola_finestra(1000, 3000)
    assert esito.barre is True
    assert esito.finestra.b == pytest.approx((0, 0, 1, 1))


def test_con_il_soggetto_il_taglio_ammesso_sale_al_35_per_cento():
    # 2,2:1 → 1,91:1 toglie il 13,2% (>10% senza soggetto): con il soggetto si taglia
    soggetto = (0.45, 0.2, 0.2, 0.6)
    senza = calcola_finestra(4400, 2000)
    con = calcola_finestra(4400, 2000, soggetto=soggetto)
    assert senza.barre is True
    assert con.barre is False
    x0, y0, x1, y1 = _px(con.finestra, 4400, 2000)
    assert x0 <= 0.45 * 4400 and x1 >= 0.65 * 4400


def test_il_soggetto_non_si_taglia_mai_se_non_ci_sta_si_mettono_le_barre():
    # soggetto largo quasi quanto la foto: la finestra 1,91:1 non lo contiene
    esito = calcola_finestra(4400, 2000, soggetto=(0.0, 0.1, 1.0, 0.8))
    assert esito.barre is True


def test_il_testo_da_tenere_conta_come_il_soggetto():
    esito = calcola_finestra(
        4400, 2000, tieni=[(0.0, 0.1, 0.15, 0.2), (0.85, 0.7, 0.15, 0.2)]
    )
    assert esito.barre is True


def test_avvicinamento_stringe_sul_soggetto_senza_scendere_sotto_i_1080():
    esito = calcola_finestra(4000, 3000, soggetto=(0.4, 0.4, 0.15, 0.2), avvicina=True)
    x0, y0, x1, y1 = _px(esito.finestra, 4000, 3000)
    assert min(x1 - x0, y1 - y0) >= 1080 - 1
    assert esito.finestra.rapporto == pytest.approx(4 / 3, abs=0.01)
    assert (
        x0 <= 0.4 * 4000 and x1 >= 0.55 * 4000 and y0 <= 0.4 * 3000 and y1 >= 0.6 * 3000
    )
    # molto più stretta della foto
    assert (x1 - x0) < 0.5 * 4000


def test_il_limite_di_ingrandimento_della_spinta_permette_di_stringere_di_piu():
    soggetto = (0.45, 0.45, 0.08, 0.1)
    standard = calcola_finestra(
        4000, 3000, soggetto=soggetto, avvicina=True, parametri=catalogo.STANDARD
    )
    spinta = calcola_finestra(
        4000, 3000, soggetto=soggetto, avvicina=True, parametri=catalogo.SPINTA
    )
    assert spinta.finestra.b[2] < standard.finestra.b[2]
    x0, y0, x1, y1 = _px(spinta.finestra, 4000, 3000)
    assert min(x1 - x0, y1 - y0) >= 1080 / catalogo.SPINTA.ingrandimento_max - 1


def test_una_foto_piccola_non_si_avvicina():
    # lato corto 900 < 1080: nessun ingrandimento ammesso, la finestra è la foto
    esito = calcola_finestra(1200, 900, soggetto=(0.4, 0.4, 0.1, 0.1), avvicina=True)
    assert esito.finestra.b == pytest.approx((0, 0, 1, 1))


def test_ambiente_limita_l_avvicinamento():
    soggetto = (0.45, 0.45, 0.06, 0.08)
    libero = calcola_finestra(6000, 4500, soggetto=soggetto, avvicina=True)
    limitato = calcola_finestra(
        6000,
        4500,
        soggetto=soggetto,
        avvicina=True,
        taglio_avvicinamento_max=catalogo.STANDARD.ambiente_taglio_max,
    )
    area = lambda e: e.finestra.b[2] * e.finestra.b[3]  # noqa: E731
    assert area(limitato) >= 0.9 - 1e-6
    assert area(limitato) > area(libero)


def test_il_centro_d_interesse_sposta_la_finestra_ma_non_taglia_il_soggetto():
    soggetto = (0.40, 0.40, 0.10, 0.12)
    a_sinistra = calcola_finestra(
        6000, 4500, soggetto=soggetto, avvicina=True, centro=(0.0, 0.5)
    )
    a_destra = calcola_finestra(
        6000, 4500, soggetto=soggetto, avvicina=True, centro=(1.0, 0.5)
    )
    assert a_sinistra.finestra.b[0] < a_destra.finestra.b[0]
    for e in (a_sinistra, a_destra):
        x0, y0, x1, y1 = _px(e.finestra, 6000, 4500)
        assert x0 <= 0.40 * 6000 and x1 >= 0.50 * 6000


def test_intruso_ai_bordi_tolto_entro_il_tetto():
    intruso = (0.0, 0.0, 0.10, 1.0)  # una striscia a sinistra: il 10% della foto
    esito = calcola_finestra(4000, 3000, togli=[intruso], parametri=catalogo.STANDARD)
    assert esito.finestra.b[0] >= 0.10 - 1e-6
    # il ritaglio mantiene il rapporto dentro l'intervallo
    assert (
        regole.RATIO_MINIMO - TOL
        <= esito.finestra.rapporto
        <= regole.RATIO_MASSIMO + TOL
    )


def test_intruso_oltre_il_tetto_resta():
    intruso = (0.0, 0.0, 0.40, 1.0)
    esito = calcola_finestra(4000, 3000, togli=[intruso], parametri=catalogo.STANDARD)
    assert esito.finestra.b == pytest.approx((0, 0, 1, 1))


def test_la_spinta_toglie_intrusi_piu_grandi_della_standard():
    intruso = (0.0, 0.0, 0.25, 1.0)
    assert (
        calcola_finestra(
            4000, 3000, togli=[intruso], parametri=catalogo.STANDARD
        ).finestra.b[0]
        == 0
    )
    assert (
        calcola_finestra(
            4000, 3000, togli=[intruso], parametri=catalogo.SPINTA
        ).finestra.b[0]
        >= 0.25 - 1e-6
    )


def test_l_intruso_sopra_il_soggetto_non_si_toglie():
    soggetto = (0.0, 0.2, 0.3, 0.6)
    intruso = (0.0, 0.0, 0.10, 1.0)  # taglierebbe il soggetto
    esito = calcola_finestra(4000, 3000, soggetto=soggetto, togli=[intruso])
    assert esito.finestra.b[0] == pytest.approx(0)


def test_non_tagliare_lascia_solo_il_taglio_del_rapporto():
    soggetto = (0.45, 0.4, 0.1, 0.2)
    esito = calcola_finestra(
        4000,
        3000,
        soggetto=soggetto,
        avvicina=True,
        togli=[(0.0, 0.0, 0.1, 1.0)],
        non_tagliare=True,
    )
    assert esito.finestra.b == pytest.approx((0, 0, 1, 1))  # nel rapporto, intera
    fuori = calcola_finestra(
        4000, 1800, soggetto=soggetto, avvicina=True, non_tagliare=True
    )
    assert fuori.finestra.rapporto == pytest.approx(regole.RATIO_MASSIMO, abs=TOL)


def test_riquadri_sconfinanti_o_vuoti_non_fanno_danni():
    esito = calcola_finestra(
        3000,
        2000,
        soggetto=(-0.2, -0.2, 0.0, 0.0),
        tieni=[(0.9, 0.9, 0.5, 0.5)],
        togli=[(2.0, 2.0, 1.0, 1.0)],
        avvicina=True,
    )
    x, y, w, h = esito.finestra.b
    assert 0 <= x and 0 <= y and x + w <= 1 + 1e-9 and y + h <= 1 + 1e-9


# --- Proprietà ---------------------------------------------------------------------

riquadro = st.tuples(
    st.floats(-0.1, 1.0), st.floats(-0.1, 1.0), st.floats(0.0, 0.8), st.floats(0.0, 0.8)
)


@settings(max_examples=250, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    st.integers(300, 6000),
    st.integers(300, 6000),
    st.one_of(st.none(), riquadro),
    st.lists(riquadro, max_size=3),
    st.lists(riquadro, max_size=3),
    st.one_of(st.none(), st.tuples(st.floats(0, 1), st.floats(0, 1))),
    st.booleans(),
    st.booleans(),
    st.sampled_from([catalogo.STANDARD, catalogo.SPINTA]),
    st.one_of(st.none(), st.floats(0.05, 0.4)),
)
def test_proprieta_della_finestra(
    l, a, soggetto, tieni, togli, centro, avvicina, non_tagliare, parametri, tetto
):
    esito = calcola_finestra(
        l, a, soggetto=soggetto, tieni=tieni, togli=togli, centro=centro,
        avvicina=avvicina, non_tagliare=non_tagliare, parametri=parametri,
        taglio_avvicinamento_max=tetto,
    )  # fmt: skip
    x0, y0, x1, y1 = _px(esito.finestra, l, a)
    # sempre dentro la foto
    assert -1e-6 <= x0 < x1 <= l + 1e-6 and -1e-6 <= y0 < y1 <= a + 1e-6
    if esito.barre:
        assert esito.finestra.b == pytest.approx((0, 0, 1, 1))
        return
    # senza barre: rapporto nell'intervallo
    assert (
        regole.RATIO_MINIMO - TOL <= (x1 - x0) / (y1 - y0) <= regole.RATIO_MASSIMO + TOL
    )
    # soggetto e testo da tenere mai tagliati
    for b in ([soggetto] if soggetto else []) + list(tieni):
        bx0, by0 = max(0.0, b[0]) * l, max(0.0, b[1]) * a
        bx1, by1 = min(1.0, b[0] + b[2]) * l, min(1.0, b[1] + b[3]) * a
        if bx1 - bx0 > 0 and by1 - by0 > 0:
            assert (
                x0 <= bx0 + 1e-3
                and y0 <= by0 + 1e-3
                and x1 >= bx1 - 1e-3
                and y1 >= by1 - 1e-3
            ), b
    # il limite di ingrandimento: la finestra non è più piccola del consentito, a meno che la foto lo sia
    se_si_stringe = (x1 - x0) < l - 1e-3 and (y1 - y0) < a - 1e-3
    if se_si_stringe and avvicina and not non_tagliare:
        assert (
            min(x1 - x0, y1 - y0)
            >= min(1080 / parametri.ingrandimento_max, min(l, a)) - 1.0
        )
    # non_tagliare: la finestra è la foto intera o il solo taglio del rapporto
    if non_tagliare:
        r = l / a
        if regole.RATIO_MINIMO - TOL <= r <= regole.RATIO_MASSIMO + TOL:
            assert esito.finestra.b == pytest.approx((0, 0, 1, 1))
        else:
            assert x1 - x0 == pytest.approx(l) or y1 - y0 == pytest.approx(a)


# --- L'esecutore applica la finestra e le barre -----------------------------------


def _foto_a_bande(dimensioni=(2000, 1000)) -> bytes:
    img = Image.new("RGB", dimensioni, (200, 200, 200))
    ImageDraw.Draw(img).rectangle(
        [0, 0, dimensioni[0] // 4, dimensioni[1]], fill=(255, 0, 0)
    )
    return immagini.jpeg_qualita(img, 95)


def test_l_esecutore_ritaglia_la_finestra():
    comando = Comando(finestra=Finestra(b=(0.5, 0.0, 0.5, 1.0), rapporto=1.0))
    uscita = immagini.apri(esegui(_foto_a_bande(), comando))
    assert uscita.size == (1080, 1080)
    rosso = (np.asarray(uscita)[..., 0] > 200) & (np.asarray(uscita)[..., 1] < 80)
    assert not rosso.any(), "la banda rossa stava fuori dalla finestra"


def test_la_finestra_fuori_intervallo_con_barre_sfocate():
    # finestra 3:1, fuori dall'intervallo: barre sfocate
    comando = Comando(
        finestra=Finestra(b=(0.0, 0.25, 1.0, 0.5), rapporto=4.0), barre="sfocate"
    )
    uscita = immagini.apri(esegui(_foto_a_bande((2000, 1000)), comando))
    assert (
        regole.RATIO_MINIMO - 0.02
        <= uscita.width / uscita.height
        <= regole.RATIO_MASSIMO + 0.02
    )
    assert min(uscita.size) == 1080


def test_la_finestra_fuori_intervallo_con_barre_neutre():
    comando = Comando(
        finestra=Finestra(b=(0.0, 0.25, 1.0, 0.5), rapporto=4.0), barre="neutre"
    )
    uscita = np.asarray(immagini.apri(esegui(_foto_a_bande((2000, 1000)), comando)))
    barra = uscita[2, uscita.shape[1] // 2]
    assert tuple(int(v) for v in barra) == pytest.approx(
        regole.COLORE_BARRE_NEUTRE, abs=3
    )


def test_senza_barre_il_rapporto_rientra_comunque():
    comando = Comando(finestra=Finestra(b=(0.0, 0.25, 1.0, 0.5), rapporto=4.0))
    uscita = immagini.apri(esegui(_foto_a_bande((2000, 1000)), comando))
    assert (
        regole.RATIO_MINIMO - 0.02
        <= uscita.width / uscita.height
        <= regole.RATIO_MASSIMO + 0.02
    )


def test_la_finestra_intera_non_cambia_la_foto():
    dati = _foto_a_bande((1600, 1200))
    intera = esegui(dati, Comando(finestra=Finestra(b=(0, 0, 1, 1), rapporto=4 / 3)))
    nessuna = esegui(dati, Comando())
    assert intera == nessuna


@pytest.mark.parametrize(
    "b", [(0.0, 0.0, 0.0, 1.0), (1.0, 0.0, 0.5, 1.0), (-0.1, 0.0, 0.5, 0.5)]
)
def test_finestra_non_valida_nel_comando(b):
    with pytest.raises(DatiNonValidi):
        Comando(finestra=Finestra(b=b, rapporto=1.0))


def test_barre_non_ammesse():
    with pytest.raises(DatiNonValidi):
        Comando(barre="rosa")
