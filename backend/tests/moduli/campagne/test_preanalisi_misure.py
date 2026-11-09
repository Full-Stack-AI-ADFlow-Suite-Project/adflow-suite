"""Le misure e le fasce della pre-analisi, una per una su immagini con valore noto (RT-13)."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from app.moduli.campagne import preanalisi
from tests import immagini


def _piatta(colore, dimensioni=(400, 300)):
    return immagini.tinta_unita(colore, dimensioni)


# --- Nitidezza ---------------------------------------------------------------------


def test_nitida_contro_sfocata():
    nitida = immagini.nitida((800, 600))
    sfocata = immagini.sfocata(nitida, 6.0)
    n, s = (
        preanalisi.misura(nitida)["nitidezza"],
        preanalisi.misura(sfocata)["nitidezza"],
    )
    assert n > 10 * s
    assert preanalisi.fasce(preanalisi.misura(nitida)).get("nitidezza") is None
    assert preanalisi.fasce(preanalisi.misura(sfocata))["nitidezza"] == "bassa"


def test_la_nitidezza_non_dipende_dalle_dimensioni_della_copia():
    """Normalizzata: la stessa scena a 2048 e a 1024 px dà la stessa fascia."""
    piccola = immagini.sfocata(immagini.nitida((1024, 768), 16), 3.0)
    grande = piccola.resize((2048, 1536), Image.Resampling.BOX)
    fp = preanalisi.fasce(preanalisi.misura(piccola)).get("nitidezza")
    fg = preanalisi.fasce(preanalisi.misura(grande)).get("nitidezza")
    assert fp == fg


# --- Luminanza ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("grigio", "atteso"),
    [(0, 0.0), (119, 50.0), (255, 100.0)],
    ids=["nero", "medio", "bianco"],
)
def test_luminanza_mediana_in_lstar(grigio, atteso):
    misure = preanalisi.misura(_piatta((grigio,) * 3))
    assert misure["luminanza_mediana"] == pytest.approx(atteso, abs=0.6)
    assert misure["percentili"]["p5"] == pytest.approx(atteso, abs=0.6)


def test_buia_contro_normale_contro_chiara():
    assert (
        preanalisi.fasce(preanalisi.misura(_piatta((20, 20, 20))))["esposizione"]
        == "scura"
    )
    assert "esposizione" not in preanalisi.fasce(
        preanalisi.misura(_piatta((128, 128, 128)))
    )
    assert (
        preanalisi.fasce(preanalisi.misura(_piatta((240, 240, 240))))["esposizione"]
        == "chiara"
    )


def test_luci_bruciate_e_ombre_chiuse_in_percentuale():
    meta = Image.new("RGB", (400, 300), (255, 255, 255))
    meta.paste((0, 0, 0), (0, 0, 200, 300))
    misure = preanalisi.misura(meta)
    assert misure["luci_bruciate"] == pytest.approx(50.0, abs=1.0)
    assert misure["ombre_chiuse"] == pytest.approx(50.0, abs=1.0)
    f = preanalisi.fasce(misure)
    assert f["luci_bruciate"] == "molte" and f["ombre_chiuse"] == "molte"


def test_una_foto_media_non_ha_luci_ne_ombre():
    misure = preanalisi.misura(_piatta((128, 128, 128)))
    assert misure["luci_bruciate"] == 0.0 and misure["ombre_chiuse"] == 0.0


def test_poche_luci_bruciate():
    immagine = Image.new("RGB", (400, 300), (128, 128, 128))
    immagine.paste((255, 255, 255), (0, 0, 40, 30))  # l'1% dei pixel
    assert preanalisi.fasce(preanalisi.misura(immagine))["luci_bruciate"] == "poche"


# --- Dominante ---------------------------------------------------------------------


def test_neutro_senza_dominante():
    misure = preanalisi.misura(_piatta((128, 128, 128)))
    assert misure["dominante_ab"] == pytest.approx([0.0, 0.0], abs=0.5)
    assert "dominante" not in preanalisi.fasce(misure)


@pytest.mark.parametrize(
    ("colore", "atteso"),
    [
        ((190, 140, 90), "calda"),
        ((100, 140, 190), "fredda"),
        ((100, 150, 100), "verde"),
        ((160, 100, 160), "magenta"),
    ],
)
def test_le_quattro_dominanti(colore, atteso):
    misure = preanalisi.misura(_piatta(colore))
    assert preanalisi.fasce(misure)["dominante"] == atteso


def test_dominante_aggiunta_a_un_grigio():
    calda = immagini.con_dominante(_piatta((128, 128, 128)), (30, 8, -30))
    assert preanalisi.fasce(preanalisi.misura(calda))["dominante"] == "calda"


# --- Caduta di luce ai bordi -------------------------------------------------------


def _vignettatura(centro: int, bordo: int) -> Image.Image:
    y, x = np.mgrid[0:300, 0:400]
    r = np.hypot((x - 200) / 200, (y - 150) / 150) / np.sqrt(2)
    valori = centro + (bordo - centro) * np.clip(r, 0, 1) ** 2
    return Image.fromarray(np.dstack([valori] * 3).astype(np.uint8), "RGB")


def test_caduta_bordi_nulla_su_foto_piatta():
    assert preanalisi.misura(_piatta((140, 140, 140)))["caduta_bordi"] == 0.0


def test_caduta_bordi_con_vignettatura():
    misure = preanalisi.misura(_vignettatura(200, 80))
    assert 0.25 < misure["caduta_bordi"] < 0.6


def test_i_bordi_piu_chiari_non_sono_una_caduta():
    assert preanalisi.misura(_vignettatura(80, 200))["caduta_bordi"] == 0.0


# --- Angolo delle linee ------------------------------------------------------------


@pytest.mark.parametrize("gradi", [3.0, -3.0, 6.0, 0.0])
def test_angolo_delle_linee(gradi):
    immagine = immagini.linee_inclinate((1000, 800), gradi)
    angolo = preanalisi.misura(immagine)["angolo_linee"]
    assert angolo is not None
    assert angolo == pytest.approx(gradi, abs=0.6)


def test_angolo_di_linee_verticali():
    # le stesse linee ruotate di 90°: l'angolo si misura dall'asse verticale
    orizzontali = immagini.linee_inclinate((1000, 800), 4.0)
    verticali = orizzontali.rotate(-90, expand=True)
    assert preanalisi.misura(verticali)["angolo_linee"] == pytest.approx(
        4.0, abs=0.8
    ) or (preanalisi.misura(verticali)["angolo_linee"] == pytest.approx(-4.0, abs=0.8))


def test_senza_linee_nessun_angolo():
    assert preanalisi.misura(_piatta((100, 100, 100)))["angolo_linee"] is None
    sfumata = immagini.gradiente((800, 600))
    assert preanalisi.misura(sfumata)["angolo_linee"] is None


def test_le_diagonali_non_sono_un_orizzonte_storto():
    assert (
        preanalisi.misura(immagini.linee_inclinate((1000, 800), 30.0))["angolo_linee"]
        is None
    )


# --- Qualità del JPEG --------------------------------------------------------------


@pytest.mark.parametrize("qualita", [30, 50, 75, 90, 95])
def test_qualita_jpeg_dalla_tabella(qualita):
    dati = immagini.jpeg_qualita(
        immagini.gradiente((256, 256), (10, 20, 30), (200, 180, 160)), qualita
    )
    stimata = preanalisi.fatti_del_file(dati)["qualita_jpeg"]
    assert stimata == pytest.approx(qualita, abs=4)


def test_compressione_forte_contro_nessuna():
    base = immagini.gradiente((256, 256))
    forte = preanalisi.misura(base, immagini.jpeg_qualita(base, 30))
    alta = preanalisi.misura(base, immagini.jpeg_qualita(base, 95))
    assert preanalisi.fasce(forte)["compressione"] == "forte"
    assert "compressione" not in preanalisi.fasce(alta)


def test_un_png_non_ha_qualita_jpeg():
    uscita = preanalisi.fatti_del_file(
        immagini.png_con_icc(_piatta((10, 10, 10)), immagini.profilo_icc("srgb"))
    )
    assert uscita["qualita_jpeg"] is None


# --- Fatti dall'EXIF ---------------------------------------------------------------


def test_flash_e_fotocamera_dall_exif():
    con = preanalisi.fatti_del_file(
        immagini.jpeg_con_exif(_piatta((90, 90, 90)), flash=1)
    )
    senza = preanalisi.fatti_del_file(
        immagini.jpeg_con_exif(_piatta((90, 90, 90)), flash=0)
    )
    assert con["exif"]["flash"] is True and senza["exif"]["flash"] is False
    assert con["exif"]["fotocamera"] is True


def test_iso_software_e_zoom():
    exif = Image.Exif()
    exif[0x0131] = "Editor di prova"
    interno = exif.get_ifd(0x8769)
    interno[0x8827] = 1600
    interno[0xA404] = 2.0
    from io import BytesIO

    uscita = BytesIO()
    _piatta((90, 90, 90)).save(uscita, "JPEG", exif=exif.tobytes())
    fatti = preanalisi.fatti_del_file(uscita.getvalue())["exif"]
    assert fatti["iso"] == 1600
    assert fatti["software"] == "Editor di prova"
    assert fatti["zoom_digitale"] == pytest.approx(2.0)
    assert fatti["fotocamera"] is False


def test_senza_exif_nessun_fatto_e_nessuna_eccezione():
    fatti = preanalisi.fatti_del_file(immagini.jpeg_qualita(_piatta((90, 90, 90)), 90))
    assert fatti["exif"] == {
        "flash": None,
        "iso": None,
        "zoom_digitale": None,
        "fotocamera": False,
        "software": None,
    }
    assert preanalisi.fatti_del_file(b"non e' un'immagine")["qualita_jpeg"] is None


# --- Fasce -------------------------------------------------------------------------


def test_una_foto_pulita_non_ha_fasce():
    scena = immagini.gradiente((800, 600), (60, 70, 80), (180, 190, 200))
    nitida = Image.blend(scena, immagini.nitida((800, 600), 4), 0.5)
    assert preanalisi.fasce(preanalisi.misura(nitida)) == {}


def test_misura_di_una_immagine_minuscola_non_solleva():
    for dimensioni in ((1, 1), (3, 2), (8, 8)):
        misure = preanalisi.misura(_piatta((90, 120, 150), dimensioni))
        preanalisi.fasce(misure)
