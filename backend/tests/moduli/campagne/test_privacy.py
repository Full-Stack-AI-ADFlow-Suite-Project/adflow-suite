"""La privacy: sfocatura delle zone, e la zona che segue la foto (RT-18)."""

from __future__ import annotations

import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.core.errori import DatiNonValidi
from app.moduli.campagne import geometria, privacy
from app.moduli.campagne.esecutore import Comando, RegoleR42, esegui
from app.moduli.campagne.finestra import Finestra
from tests import immagini

PIENA = Finestra(b=(0.0, 0.0, 1.0, 1.0), rapporto=4 / 3)


def _testo(img: Image.Image, riquadro, parola="TARGA 1234") -> None:
    """Scrive testo nero grande dentro il riquadro: un dettaglio che si legge."""
    disegno = ImageDraw.Draw(img)
    x0, y0, x1, y1 = riquadro
    disegno.rectangle(riquadro, fill=(250, 250, 250))
    carattere = ImageFont.load_default(size=max(10, (y1 - y0) // 2))
    disegno.text((x0 + 8, y0 + (y1 - y0) // 4), parola, fill=(0, 0, 0), font=carattere)


def _scena():
    """Sfondo a gradiente con due targhe: A (da oscurare) e B (no)."""
    img = immagini.gradiente(
        (1600, 1200), (60, 70, 90), (160, 150, 130), verticale=True
    )
    _testo(img, (200, 200, 600, 320))  # A
    _testo(img, (1000, 800, 1400, 920))  # B
    return img


def _zona(riquadro, dimensioni=(1600, 1200), **extra) -> dict:
    x0, y0, x1, y1 = riquadro
    larghezza, altezza = dimensioni
    return {
        "b": [
            x0 / larghezza * 100,
            y0 / altezza * 100,
            (x1 - x0) / larghezza * 100,
            (y1 - y0) / altezza * 100,
        ],
        **extra,
    }


def _nitidezza(img: Image.Image, riquadro) -> float:
    x0, y0, x1, y1 = riquadro
    grigio = np.asarray(img.convert("L"), dtype=np.uint8)[y0:y1, x0:x1]
    return float(cv2.Laplacian(grigio, cv2.CV_64F).var())


def _jpeg(img) -> bytes:
    return immagini.jpeg_qualita(img, 95)


def test_nella_zona_il_testo_diventa_illeggibile_e_fuori_i_pixel_restano_uguali():
    scena = _scena()
    dati = _jpeg(scena)
    senza = immagini.apri(esegui(dati, Comando(finestra=PIENA)))
    con = immagini.apri(
        esegui(dati, Comando(finestra=PIENA), [_zona((200, 200, 600, 320))])
    )
    scala = 1080 / 1200
    a = tuple(int(v * scala) for v in (200, 200, 600, 320))
    b = tuple(int(v * scala) for v in (1000, 800, 1400, 920))
    assert _nitidezza(senza, a) > 500
    assert _nitidezza(con, a) < 0.03 * _nitidezza(senza, a), "il testo si legge ancora"
    # la targa B non è una zona: identica
    assert _nitidezza(con, b) == pytest.approx(_nitidezza(senza, b), rel=0.01)
    diff = np.abs(np.asarray(con).astype(int) - np.asarray(senza).astype(int)).sum(
        axis=2
    )
    lontano = diff.copy()
    x0, y0, x1, y1 = a
    lontano[max(0, y0 - 120) : y1 + 120, max(0, x0 - 120) : x1 + 120] = 0
    assert lontano.max() == 0, "sono cambiati pixel lontani dalla zona"


def test_la_zona_ha_un_margine_del_quindici_per_cento():
    img = Image.new("RGB", (1000, 1000), (250, 250, 250))
    ImageDraw.Draw(img).rectangle((380, 380, 619, 619), fill=(0, 0, 0))
    zona = {"b": [40, 40, 20, 20]}  # 400–600 px
    privacy.oscura_zone(img, [zona], geometria.Mappa.identita(1000, 1000))
    pixel = np.asarray(img)
    # il bordo nero fra 380 e 400 (dentro il margine di 30 px) è stato toccato
    assert (pixel[500, 385] != [0, 0, 0]).any(), "il margine non è stato sfocato"
    assert tuple(pixel[500, 350]) == (250, 250, 250)  # oltre il margine (370)
    assert tuple(pixel[500, 650]) == (250, 250, 250)


def test_zona_spenta_o_nessuna_zona_non_cambia_la_foto():
    dati = _jpeg(_scena())
    base = esegui(dati, Comando(finestra=PIENA))
    assert (
        esegui(
            dati, Comando(finestra=PIENA), [_zona((200, 200, 600, 320), attiva=False)]
        )
        == base
    )
    assert esegui(dati, Comando(finestra=PIENA), []) == base


@pytest.mark.parametrize(
    "zona",
    [
        {"b": [10, 10, 5]},
        {"b": [10, 10, 5, "x"]},
        {"b": [110, 10, 5, 5]},
        {"b": [10, 10, 0, 5]},
        {"b": [10, 10, 5, -5]},
        {"b": None},
        {"senza": "b"},
        "una stringa",
        {"b": [True, 1, 1, 1]},
    ],
)
def test_una_zona_malformata_non_si_ignora_si_rifiuta_il_render(zona):
    with pytest.raises(DatiNonValidi):
        esegui(_jpeg(_scena()), Comando(finestra=PIENA), [zona])


def test_la_zona_segue_la_rotazione_il_raddrizzamento_e_la_finestra():
    scena = _scena()
    dati = _jpeg(scena)
    comando = Comando(
        ruota=90,
        raddrizza={"tipo": "rotazione", "gradi": 3.0},
        finestra=Finestra(b=(0.0, 0.05, 1.0, 0.9), rapporto=1.0),
    )
    senza = immagini.apri(esegui(dati, comando))
    con = immagini.apri(esegui(dati, comando, [_zona((200, 200, 600, 320))]))
    # dove è finito il centro della targa A: lo dice la stessa mappa che usa l'esecutore
    mappa = geometria.Mappa.identita(1600, 1200)
    ruotata, mappa = geometria.ruota_90(scena, 90, mappa)
    ruotata, mappa = geometria.raddrizza_rotazione(ruotata, 3.0, mappa)
    cx, cy = mappa.punto(400, 260)
    x, y, w, h = (0.0, 0.05, 1.0, 0.9)
    px0, py0 = round(x * ruotata.width), round(y * ruotata.height)
    px1, py1 = round((x + w) * ruotata.width), round((y + h) * ruotata.height)
    scala = con.width / (px1 - px0)
    centro = ((cx - px0) * scala, (cy - py0) * scala)
    diff = np.abs(np.asarray(con).astype(int) - np.asarray(senza).astype(int)).sum(
        axis=2
    )
    righe, colonne = np.where(diff > 30)
    assert len(righe) > 100, "la zona non è stata sfocata"
    assert colonne.mean() == pytest.approx(centro[0], abs=60)
    assert righe.mean() == pytest.approx(centro[1], abs=60)
    # la targa B non è una zona: lì la foto è identica
    bx, by = mappa.punto(1200, 860)
    bx, by = int((bx - px0) * scala), int((by - py0) * scala)
    assert diff[max(0, by - 40) : by + 40, max(0, bx - 40) : bx + 40].max() == 0


def test_una_zona_fuori_dalla_foto_dopo_la_finestra_non_da_errori():
    dati = _jpeg(_scena())
    comando = Comando(finestra=Finestra(b=(0.5, 0.5, 0.5, 0.5), rapporto=1.0))
    base = esegui(dati, comando)
    assert esegui(dati, comando, [_zona((200, 200, 600, 320))]) == base


def test_la_privacy_vale_anche_per_l_originale_con_le_regole_di_r42():
    dati = _jpeg(_scena())
    scala = 1080 / 1200
    a = tuple(int(v * scala) for v in (200, 200, 600, 320))
    con = immagini.apri(
        esegui(dati, Comando(finestra=RegoleR42()), [_zona((200, 200, 600, 320))])
    )
    assert _nitidezza(con, a) < 20


def test_la_sfocatura_non_cambia_la_foto_originale():
    scena = _scena()
    prima = np.asarray(scena).copy()
    esegui(_jpeg(scena), Comando(finestra=PIENA), [_zona((200, 200, 600, 320))])
    assert np.array_equal(np.asarray(scena), prima)
