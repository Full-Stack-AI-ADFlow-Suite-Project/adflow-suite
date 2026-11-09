"""Luce e nitidezza dell'esecutore (RT-17): esposizione, bianco, ombre, flash, nitidezza."""

from __future__ import annotations

import math
from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from app.moduli.campagne import ritocco_catalogo as catalogo
from app.moduli.campagne import luce
from app.moduli.campagne.esecutore import Comando, esegui
from app.moduli.campagne.finestra import Finestra
from app.moduli.campagne.preanalisi import misura, srgb_a_lab
from tests import immagini

pytest.importorskip("hypothesis")

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

PIENA = Finestra(b=(0.0, 0.0, 1.0, 1.0), rapporto=4 / 3)


def _jpeg(img: Image.Image, qualita: int = 95) -> bytes:
    return immagini.jpeg_qualita(img, qualita)


def _esegui(img: Image.Image, **campi) -> Image.Image:
    return immagini.apri(esegui(_jpeg(img), Comando(finestra=PIENA, **campi)))


def _mediana_l(img: Image.Image) -> float:
    return float(np.median(srgb_a_lab(np.asarray(img.convert("RGB")))[..., 0]))


def _media(img: Image.Image, riquadro) -> np.ndarray:
    x0, y0, x1, y1 = riquadro
    return np.asarray(img.convert("RGB"))[y0:y1, x0:x1].reshape(-1, 3).mean(axis=0)


def _foto(media: int = 128, dimensioni=(1200, 900)) -> Image.Image:
    """Una scena a gradiente morbido attorno a un grigio: nessun difetto."""
    return immagini.gradiente(
        dimensioni, (media - 40,) * 3, (media + 40,) * 3, verticale=True
    )


# --- Esposizione -------------------------------------------------------------------


def test_foto_scura_si_schiarisce_verso_l_obiettivo_entro_il_tetto():
    scura = _foto(40)
    prima = _mediana_l(_esegui(scura))
    dopo = _mediana_l(
        _esegui(scura, luce={"esposizione": {"verso": "su", "tetto": 0.5}})
    )
    assert dopo > prima + 2
    # al più mezzo stop in luce lineare
    lineare = lambda L: ((L + 16) / 116) ** 3  # noqa: E731
    assert lineare(dopo) / lineare(prima) <= 2**0.5 * 1.08
    # con un tetto ampio arriva all'obiettivo
    arrivo = _mediana_l(
        _esegui(scura, luce={"esposizione": {"verso": "su", "tetto": 4.0}})
    )
    assert arrivo == pytest.approx(catalogo.ESPOSIZIONE_OBIETTIVO_L, abs=3.0)


def test_foto_chiara_si_scurisce():
    chiara = _foto(215)
    prima = _mediana_l(_esegui(chiara))
    dopo = _mediana_l(
        _esegui(chiara, luce={"esposizione": {"verso": "giu", "tetto": 1.0}})
    )
    assert dopo < prima - 2


def test_il_verso_sbagliato_non_fa_niente():
    scura = _foto(40)
    assert _mediana_l(
        _esegui(scura, luce={"esposizione": {"verso": "giu", "tetto": 1.0}})
    ) == pytest.approx(_mediana_l(_esegui(scura)), abs=0.3)
    chiara = _foto(215)
    assert _mediana_l(
        _esegui(chiara, luce={"esposizione": {"verso": "su", "tetto": 1.0}})
    ) == pytest.approx(_mediana_l(_esegui(chiara)), abs=0.3)


def test_schiarire_non_brucia_le_luci():
    img = immagini.gradiente((1200, 900), (10, 10, 10), (200, 200, 200), verticale=True)
    dopo = np.asarray(
        _esegui(
            img, luce={"esposizione": {"verso": "su", "tetto": 1.0, "obiettivo": 70.0}}
        )
    )
    # il bianco quasi pieno non salta di colpo a 255 su metà foto
    assert (dopo.min(axis=2) >= 254).mean() < 0.05


def test_la_crominanza_si_conserva_schiarendo():
    colore = immagini.tinta_unita((100, 50, 40), (1200, 900))
    prima = _media(_esegui(colore), (0, 0, 1200, 900))
    dopo = _media(
        _esegui(colore, luce={"esposizione": {"verso": "su", "tetto": 1.0}}),
        (0, 0, 1200, 900),
    )

    def rapporto(m):  # in luce lineare, dove il guadagno è uguale per canale
        lineare = luce.a_lineare(np.round(m).astype(np.uint8))
        return lineare[0] / lineare[1], lineare[2] / lineare[1]

    assert rapporto(dopo) == pytest.approx(rapporto(prima), rel=0.05)


def test_foto_buona_resta_com_e_delta_e_sotto_uno():
    buona = _foto(130)
    comando = {
        "esposizione": {"verso": "su", "tetto": 0.5},
        "bianco": {"soggetto": True, "tetto": 0.04},
    }
    senza = _esegui(buona)
    con = _esegui(buona, luce=comando, nitidezza=False)
    assert immagini.delta_e(senza, con) < 1.0


# --- Bianco ------------------------------------------------------------------------


def _scena_con_neutro(colore_neutro, dimensioni=(1200, 900)):
    img = _foto(120, dimensioni)
    riquadro = (100, 100, 300, 250)
    img.paste(colore_neutro, riquadro)
    box = {
        "x": 100 / dimensioni[0],
        "y": 100 / dimensioni[1],
        "larghezza": 200 / dimensioni[0],
        "altezza": 150 / dimensioni[1],
    }
    return img, riquadro, box


def _dispersione(m: np.ndarray) -> float:
    return float((m.max() - m.min()) / m.mean())


def test_la_zona_neutra_tinta_si_corregge():
    img, riquadro, box = _scena_con_neutro((135, 128, 118))
    prima = _esegui(img)
    scala = 1080 / 900
    zona = tuple(int(v * scala) for v in riquadro)
    dopo = _esegui(img, luce={"bianco": {"neutro": box, "tetto": 0.25}})
    assert _dispersione(_media(dopo, zona)) < 0.02
    assert _dispersione(_media(prima, zona)) > 0.05


def test_il_tetto_del_bianco_limita_ogni_canale():
    img, riquadro, box = _scena_con_neutro((160, 128, 100))
    scala = 1080 / 900
    zona = tuple(int(v * scala) for v in riquadro)
    prima = _media(_esegui(img), zona)
    dopo = _media(_esegui(img, luce={"bianco": {"neutro": box, "tetto": 0.05}}), zona)
    lineare = lambda m: luce.a_lineare(np.round(m).astype(np.uint8))  # noqa: E731
    guadagni = lineare(dopo) / lineare(prima)
    assert np.all(guadagni >= 0.94) and np.all(guadagni <= 1.06)
    assert _dispersione(dopo) < _dispersione(prima)  # migliora, ma non del tutto


def test_la_media_dei_grigi_del_soggetto_solo_se_richiesta():
    tinta = immagini.con_dominante(_foto(120), (14, 4, -14))
    assert (
        immagini.delta_e(
            _esegui(tinta), _esegui(tinta, luce={"bianco": {"tetto": 0.04}})
        )
        < 0.3
    )
    corretta = _esegui(tinta, luce={"bianco": {"soggetto": True, "tetto": 0.04}})
    assert immagini.delta_e(_esegui(tinta), corretta) > 0.5


def test_il_bianco_non_cambia_la_luminanza():
    img, _, box = _scena_con_neutro((160, 128, 100))
    prima = _mediana_l(_esegui(img))
    dopo = _mediana_l(_esegui(img, luce={"bianco": {"neutro": box, "tetto": 0.1}}))
    assert dopo == pytest.approx(prima, abs=1.5)


# --- Ombre -------------------------------------------------------------------------


def test_le_ombre_si_aprono_e_le_luci_restano():
    img = Image.new("RGB", (1200, 900), (210, 190, 170))
    img.paste((12, 8, 6), (0, 0, 600, 900))
    prima = _esegui(img)
    dopo = _esegui(img, luce={"ombre": 0.5})
    buio = (50, 50, 400, 800)
    chiaro = (700, 50, 1000, 800)
    assert _media(dopo, buio).mean() > _media(prima, buio).mean() + 2
    assert np.allclose(_media(dopo, chiaro), _media(prima, chiaro), atol=1.0)
    # il colore si conserva: stessi rapporti fra i canali
    a, b = luce.a_lineare(_media(prima, buio).round().astype(np.uint8)), luce.a_lineare(
        _media(dopo, buio).round().astype(np.uint8)
    )
    assert (b[0] / b[1]) == pytest.approx(a[0] / a[1], rel=0.12)


def test_piu_dose_piu_ombre_aperte():
    img = Image.new("RGB", (1200, 900), (12, 12, 12))
    zona = (100, 100, 900, 700)
    assert (
        _media(_esegui(img, luce={"ombre": 0.5}), zona).mean()
        > _media(_esegui(img, luce={"ombre": 0.25}), zona).mean()
        > _media(_esegui(img), zona).mean()
    )


# --- Flash -------------------------------------------------------------------------


def _vignettatura(centro: int, bordo: int, dimensioni=(1200, 900)) -> Image.Image:
    larghezza, altezza = dimensioni
    y, x = np.mgrid[0:altezza, 0:larghezza]
    r = np.hypot(
        (x - larghezza / 2) / (larghezza / 2), (y - altezza / 2) / (altezza / 2)
    ) / np.sqrt(2)
    valori = centro + (bordo - centro) * np.clip(r, 0, 1) ** 2
    return Image.fromarray(np.dstack([valori] * 3).astype(np.uint8), "RGB")


def test_il_flash_alza_i_bordi_e_non_tocca_il_centro():
    img = _vignettatura(180, 80)
    prima, dopo = _esegui(img), _esegui(img, luce={"flash": 0.5})
    assert misura(dopo)["caduta_bordi"] < misura(prima)["caduta_bordi"]
    angolo = (0, 0, 120, 100)
    centro = (500, 400, 700, 600)
    assert _media(dopo, angolo).mean() > _media(prima, angolo).mean() + 5
    assert np.allclose(_media(dopo, centro), _media(prima, centro), atol=1.5)


def test_senza_caduta_il_flash_non_fa_niente():
    img = _foto(130)
    assert immagini.delta_e(_esegui(img), _esegui(img, luce={"flash": 0.5})) < 0.5


def test_il_flash_spento_non_fa_niente():
    img = _vignettatura(180, 80)
    assert immagini.delta_e(_esegui(img), _esegui(img, luce={"flash": 0.0})) < 0.1


# --- Nitidezza ---------------------------------------------------------------------


def _nitidezza(img: Image.Image) -> float:
    return misura(img)["nitidezza"]


def test_la_nitidezza_aumenta_il_contrasto_dei_bordi():
    molle = immagini.sfocata(immagini.nitida((1200, 900), 12), 1.6)
    dati = _jpeg(molle, 95)
    senza = immagini.apri(esegui(dati, Comando(finestra=PIENA)))
    con = immagini.apri(esegui(dati, Comando(finestra=PIENA, nitidezza=True)))
    media = immagini.apri(
        esegui(dati, Comando(finestra=PIENA, nitidezza=True, nitidezza_dose=0.6))
    )
    assert _nitidezza(con) > _nitidezza(senza)
    assert _nitidezza(media) > _nitidezza(con)


def test_con_compressione_forte_la_nitidezza_si_spegne():
    molle = immagini.sfocata(immagini.nitida((1200, 900), 12), 1.6)
    dati = _jpeg(molle, 30)
    avvisi: list[str] = []
    con = esegui(dati, Comando(finestra=PIENA, nitidezza=True), avvisi=avvisi)
    assert avvisi == ["nitidezza_saltata"]
    assert con == esegui(dati, Comando(finestra=PIENA))


def test_con_zoom_digitale_la_nitidezza_si_spegne():
    exif = Image.Exif()
    exif.get_ifd(0x8769)[0xA404] = 2.0
    buffer = BytesIO()
    immagini.sfocata(immagini.nitida((1200, 900), 12), 1.6).save(
        buffer, "JPEG", quality=95, exif=exif.tobytes()
    )
    avvisi: list[str] = []
    esegui(buffer.getvalue(), Comando(finestra=PIENA, nitidezza=True), avvisi=avvisi)
    assert avvisi == ["nitidezza_saltata"]


def test_un_png_senza_qualita_jpeg_si_nitidisce():
    buffer = BytesIO()
    immagini.sfocata(immagini.nitida((1200, 900), 12), 1.6).save(buffer, "PNG")
    avvisi: list[str] = []
    esegui(buffer.getvalue(), Comando(finestra=PIENA, nitidezza=True), avvisi=avvisi)
    assert avvisi == []


# --- La regione del soggetto e la mappa --------------------------------------------


def _scena_con_soggetto_scuro():
    """Chiara dappertutto, tranne un soggetto scuro in alto a sinistra."""
    img = Image.new("RGB", (1600, 1200), (190, 190, 190))
    img.paste((30, 30, 30), (80, 60, 560, 420))
    box = {
        "x": 80 / 1600,
        "y": 60 / 1200,
        "larghezza": 480 / 1600,
        "altezza": 360 / 1200,
    }
    return img, box


def test_si_misura_nel_soggetto_non_nella_foto_intera():
    img, box = _scena_con_soggetto_scuro()
    comando = {"esposizione": {"verso": "su", "tetto": 1.0}}
    senza_regione = _esegui(img, luce=comando)
    con_regione = _esegui(img, luce={**comando, "soggetto": box})
    base = _esegui(img)
    # la foto intera è chiara: senza regione non c'è niente da schiarire
    assert immagini.delta_e(base, senza_regione) < 0.5
    # col soggetto scuro, invece, si schiarisce
    zona = (int(100 * 0.9), int(80 * 0.9), int(500 * 0.9), int(400 * 0.9))
    assert _media(con_regione, zona).mean() > _media(base, zona).mean() + 10


@pytest.mark.parametrize("ruota", [90, 180, 270])
def test_la_regione_segue_la_rotazione(ruota):
    img, box = _scena_con_soggetto_scuro()
    comando = Comando(
        ruota=ruota,
        luce={"esposizione": {"verso": "su", "tetto": 1.0}, "soggetto": box},
    )
    senza = Comando(ruota=ruota)
    dati = _jpeg(img)
    dopo, base = immagini.apri(esegui(dati, comando)), immagini.apri(
        esegui(dati, senza)
    )
    # dove sta il soggetto nella foto ruotata: lo dice la mappa
    from app.moduli.campagne.geometria import Mappa, ruota_90

    ruotata, mappa = ruota_90(img, ruota, Mappa.identita(*img.size))
    scala = dopo.width / ruotata.width
    cx, cy = mappa.punto(320, 240)  # centro del soggetto
    px, py = int(cx * scala), int(cy * scala)
    zona = (px - 20, py - 20, px + 20, py + 20)
    assert _media(dopo, zona).mean() > _media(base, zona).mean() + 10
    # e lontano dal soggetto la foto è uguale (la correzione è globale ma qui già chiara)
    assert dopo.size == base.size


def test_dopo_la_finestra_la_regione_resta_sul_soggetto():
    img, box = _scena_con_soggetto_scuro()
    # finestra che taglia via la parte destra: il soggetto resta, ora in un riquadro diverso
    comando = Comando(
        finestra=Finestra(b=(0.0, 0.0, 0.5, 0.75), rapporto=1.0),
        luce={"esposizione": {"verso": "su", "tetto": 1.0}, "soggetto": box},
    )
    dati = _jpeg(img)
    dopo = immagini.apri(esegui(dati, comando))
    base = immagini.apri(esegui(dati, Comando(finestra=comando.finestra)))
    scala = dopo.width / 800
    zona = (int(150 * scala), int(150 * scala), int(450 * scala), int(350 * scala))
    assert _media(dopo, zona).mean() > _media(base, zona).mean() + 10


# --- Robustezza --------------------------------------------------------------------


@settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    st.integers(200, 500),
    st.integers(200, 500),
    st.sampled_from(["su", "giu"]),
    st.floats(0.0, 1.5),
    st.floats(0.0, 0.2),
    st.floats(0.0, 1.0),
    st.floats(0.0, 1.0),
    st.booleans(),
)
def test_proprieta_nessuna_eccezione_con_comandi_validi(
    l, a, verso, tetto, bianco_tetto, ombre, flash, nitido
):
    img = immagini.gradiente((l, a), (5, 10, 20), (230, 200, 180), verticale=True)
    comando = Comando(
        finestra=PIENA,
        luce={
            "esposizione": {"verso": verso, "tetto": tetto},
            "bianco": {"soggetto": True, "tetto": bianco_tetto},
            "ombre": ombre,
            "flash": flash,
        },
        nitidezza=nitido,
    )
    uscita = immagini.apri(esegui(_jpeg(img, 85), comando))
    assert min(uscita.size) == 1080


def test_una_regione_minuscola_si_ignora():
    assert luce.regione(
        {"x": 0.5, "y": 0.5, "larghezza": 0.001, "altezza": 0.001}, 1000, 800
    ) == (0, 0, 1000, 800)
    assert luce.regione(None, 100, 50) == (0, 0, 100, 50)


def test_da_lineare_e_inverso_di_a_lineare():
    tutti = np.arange(256, dtype=np.uint8).reshape(16, 16, 1).repeat(3, axis=2)
    assert np.array_equal(luce.da_lineare(luce.a_lineare(tutti)), tutti)
    assert math.isclose(
        float(luce.a_lineare(np.array([[[255, 255, 255]]], dtype=np.uint8))[0, 0, 0]),
        1.0,
    )
