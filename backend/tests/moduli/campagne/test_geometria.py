"""Geometria dell'esecutore: rotazioni, raddrizzamento e mappa delle coordinate (RT-15)."""

from __future__ import annotations

import math
from io import BytesIO

import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw

from app.moduli.campagne import geometria, preanalisi
from app.moduli.campagne.esecutore import Comando, RegoleR42, esegui
from tests import immagini

pytest.importorskip("hypothesis")

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402


def _apri(dati: bytes) -> Image.Image:
    return immagini.apri(dati)


# --- Rotazioni di 90° --------------------------------------------------------------


def _con_segno(dimensioni=(300, 200)) -> tuple[Image.Image, tuple[float, float]]:
    """Una foto con un quadratino rosso in alto a sinistra e il suo centro."""
    img = Image.new("RGB", dimensioni, (200, 200, 200))
    ImageDraw.Draw(img).rectangle([10, 10, 29, 29], fill=(255, 0, 0))
    return img, (20.0, 20.0)


@pytest.mark.parametrize("gradi", [90, 180, 270])
def test_le_rotazioni_di_90_portano_il_segno_dove_dice_la_mappa(gradi):
    img, (x, y) = _con_segno()
    ruotata, mappa = geometria.ruota_90(img, gradi, geometria.Mappa.identita(*img.size))
    assert ruotata.size == ((200, 300) if gradi != 180 else (300, 200))
    assert (mappa.larghezza, mappa.altezza) == ruotata.size
    px, py = mappa.punto(x, y)
    assert ruotata.getpixel((int(px), int(py))) == (255, 0, 0)


def test_la_rotazione_di_90_e_in_senso_orario():
    img, _ = _con_segno()
    ruotata, _ = geometria.ruota_90(img, 90, geometria.Mappa.identita(*img.size))
    # il segno era in alto a sinistra: ruotando in senso orario va in alto a destra
    assert ruotata.getpixel((180, 20)) == (255, 0, 0)
    assert ruotata.getpixel((20, 20)) != (255, 0, 0)


def test_ruotare_quattro_volte_rida_la_foto_e_la_mappa_identica():
    img, _ = _con_segno()
    mappa = geometria.Mappa.identita(*img.size)
    for _ in range(4):
        img_n, mappa = geometria.ruota_90(img if _ == 0 else img_n, 90, mappa)
    assert np.array_equal(np.asarray(img_n), np.asarray(_con_segno()[0]))
    assert np.allclose(mappa.matrice, np.eye(3), atol=1e-9)


def test_il_riquadro_del_soggetto_segue_la_rotazione():
    img = Image.new("RGB", (300, 200))
    _, mappa = geometria.ruota_90(img, 90, geometria.Mappa.identita(*img.size))
    box = mappa.box_norm({"x": 0.1, "y": 0.2, "larghezza": 0.2, "altezza": 0.3})
    assert box == pytest.approx({"x": 0.5, "y": 0.1, "larghezza": 0.3, "altezza": 0.2})


def test_un_riquadro_fuori_dalla_foto_diventa_nessuno():
    mappa = geometria.Mappa.identita(100, 100)
    assert mappa.box_norm(None) is None
    assert (
        mappa.box_norm({"x": 1.2, "y": 0.1, "larghezza": 0.1, "altezza": 0.1}) is None
    )


def test_rotazione_non_ammessa():
    with pytest.raises(ValueError):
        geometria.ruota_90(
            Image.new("RGB", (10, 10)), 45, geometria.Mappa.identita(10, 10)
        )


# --- Rotazione fine ----------------------------------------------------------------


@pytest.mark.parametrize("gradi", [3.0, -4.0, 0.8])
def test_rettangolo_inclinato_raddrizzato_entro_mezzo_grado(gradi):
    immagine, _ = immagini.rettangolo_inclinato(
        (1600, 1200), gradi, (1000, 700), colore=(220, 200, 150), sfondo=(250, 250, 250)
    )
    prima = preanalisi.misura(immagine)["angolo_linee"]
    assert prima == pytest.approx(gradi, abs=0.5)
    uscita = _apri(
        esegui(
            immagini.jpeg_qualita(immagine, 95),
            Comando(raddrizza={"tipo": "rotazione", "gradi": prima}),
        )
    )
    dopo = preanalisi.misura(uscita)["angolo_linee"]
    assert dopo is not None and abs(dopo) < 0.5


def test_la_rotazione_fine_non_lascia_angoli_vuoti():
    immagine = Image.new("RGB", (1600, 1200), (250, 250, 250))
    uscita = _apri(
        esegui(
            immagini.jpeg_qualita(immagine, 95),
            Comando(raddrizza={"tipo": "rotazione", "gradi": 4.0}),
        )
    )
    scuro = (np.asarray(uscita).min(axis=2) < 200).mean()
    assert scuro == 0.0, "angoli vuoti dopo la rotazione"


@pytest.mark.parametrize("gradi", [2.0, -3.5, 5.0])
def test_la_mappa_della_rotazione_fine_porta_gli_angoli_del_rettangolo_su_linee_dritte(
    gradi,
):
    immagine, veri = immagini.rettangolo_inclinato((1600, 1200), gradi, (1000, 700))
    ruotata, mappa = geometria.raddrizza_rotazione(
        immagine, gradi, geometria.Mappa.identita(*immagine.size)
    )
    tl, tr, br, bl = (np.array(mappa.punto(*p)) for p in veri)
    assert abs(tl[1] - tr[1]) < 2.0 and abs(bl[1] - br[1]) < 2.0
    assert abs(tl[0] - bl[0]) < 2.0 and abs(tr[0] - br[0]) < 2.0
    assert np.hypot(*(tr - tl)) == pytest.approx(1000, abs=3)
    # e l'angolo mappato cade su un pixel del rettangolo, non sullo sfondo
    cx, cy = (tl + br) / 2
    assert ruotata.getpixel((int(cx), int(cy))) == (200, 180, 140)


def test_rettangolo_inscritto():
    assert geometria.rettangolo_inscritto(1600, 1200, 0.0) == pytest.approx(1.0)
    k = geometria.rettangolo_inscritto(1600, 1200, 5.0)
    assert 0.85 < k < 1.0
    a = math.radians(5.0)
    assert 1600 * k * math.cos(a) + 1200 * k * math.sin(a) <= 1600 + 1e-6
    assert 1600 * k * math.sin(a) + 1200 * k * math.cos(a) <= 1200 + 1e-6


# --- Prospettiva -------------------------------------------------------------------


def _trapezio():
    img = Image.new("RGB", (800, 600), (30, 30, 30))
    angoli = [(200, 120), (600, 150), (640, 480), (160, 500)]
    ImageDraw.Draw(img).polygon(angoli, fill=(255, 255, 255))
    return img, [[x / 800, y / 600] for x, y in angoli], angoli


def test_la_prospettiva_porta_la_superficie_di_fronte():
    img, norm, angoli = _trapezio()
    esito = geometria.raddrizza_prospettiva(
        img, norm, geometria.Mappa.identita(*img.size), deformazione_max=0.9
    )
    assert esito is not None
    raddrizzata, mappa = esito
    larghezza, altezza = raddrizzata.size
    bianchi = (np.asarray(raddrizzata).min(axis=2) > 240).mean()
    assert bianchi > 0.97, "la superficie non riempie l'uscita"
    attesi = [(0, 0), (larghezza, 0), (larghezza, altezza), (0, altezza)]
    for (x, y), (ex, ey) in zip(angoli, attesi):
        assert mappa.punto(x, y) == pytest.approx((ex, ey), abs=0.5)


def test_coefficienti_inversi_per_pillow():
    """Pillow vuole la trasformazione inversa: con la diretta la foto verrebbe storta al contrario."""
    rng = np.random.default_rng(7)
    base = rng.integers(0, 255, (60, 80, 3), dtype=np.uint8)
    img = Image.fromarray(cv2.GaussianBlur(base, (0, 0), 3), "RGB")
    origine = np.array([[10, 8], [70, 14], [74, 52], [6, 50]], dtype=float)
    destinazione = np.array([[0, 0], [64, 0], [64, 40], [0, 40]], dtype=float)

    giusta = img.transform(
        (64, 40),
        Image.Transform.PERSPECTIVE,
        geometria.coefficienti_prospettiva(origine, destinazione),
        Image.Resampling.BILINEAR,
    )
    riferimento = cv2.warpPerspective(
        np.asarray(img),
        cv2.getPerspectiveTransform(
            origine.astype(np.float32), destinazione.astype(np.float32)
        ),
        (64, 40),
        flags=cv2.INTER_LINEAR,
    )
    diretta = cv2.getPerspectiveTransform(
        origine.astype(np.float32), destinazione.astype(np.float32)
    )
    diretta = diretta / diretta[2, 2]
    sbagliata = img.transform(
        (64, 40),
        Image.Transform.PERSPECTIVE,
        tuple(diretta.ravel()[:8]),
        Image.Resampling.BILINEAR,
    )

    errore_giusta = np.abs(
        np.asarray(giusta).astype(int) - riferimento.astype(int)
    ).mean()
    errore_sbagliata = np.abs(
        np.asarray(sbagliata).astype(int) - riferimento.astype(int)
    ).mean()
    assert errore_giusta < 2.0
    assert errore_sbagliata > 5 * max(errore_giusta, 0.5)


def test_deformazione():
    rettangolo = np.array([[0, 0], [100, 0], [100, 60], [0, 60]], dtype=float)
    assert geometria.deformazione(rettangolo) == pytest.approx(0.0)
    ruotato = np.array([[0, 0], [90, 40], [60, 100], [-30, 60]], dtype=float)
    assert geometria.deformazione(ruotato) < 0.05
    trapezio = np.array([[20, 0], [80, 0], [100, 60], [0, 60]], dtype=float)
    assert geometria.deformazione(trapezio) == pytest.approx(0.4)


def test_deformazione_oltre_soglia_il_passo_si_salta():
    img, norm, _ = _trapezio()
    mappa = geometria.Mappa.identita(*img.size)
    assert (
        geometria.raddrizza_prospettiva(img, norm, mappa, deformazione_max=0.01) is None
    )
    avvisi: list[str] = []
    dati = immagini.jpeg_qualita(img, 95)
    senza = esegui(dati, Comando())
    con = esegui(
        dati,
        Comando(raddrizza={"tipo": "prospettiva", "angoli": norm, "max": 0.01}),
        avvisi=avvisi,
    )
    assert avvisi == ["raddrizza_saltato"]
    assert con == senza, "un passo saltato deve lasciare la foto com'era"


@pytest.mark.parametrize(
    "angoli",
    [
        [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9]],  # tre punti
        [[0.1, 0.1], [0.9, 0.9], [0.9, 0.1], [0.1, 0.9]],  # a farfalla
        [[-0.5, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]],  # fuori dalla foto
        [[0.5, 0.5], [0.5, 0.5], [0.5, 0.5], [0.5, 0.5]],  # un punto
    ],
)
def test_angoli_non_validi_saltano_il_passo(angoli):
    img = Image.new("RGB", (400, 300), (90, 90, 90))
    assert (
        geometria.raddrizza_prospettiva(
            img, angoli, geometria.Mappa.identita(*img.size), 0.9
        )
        is None
    )


@pytest.mark.parametrize(
    "passo",
    [
        {"tipo": "rotazione", "gradi": 20.0},
        {"tipo": "rotazione", "gradi": 0.2},
        {"tipo": "rotazione"},
        {"tipo": "sconosciuto"},
    ],
)
def test_rotazioni_fuori_misura_o_malformate_saltano_il_passo(passo):
    dati = immagini.jpeg_qualita(Image.new("RGB", (400, 300), (90, 90, 90)), 90)
    avvisi: list[str] = []
    assert esegui(dati, Comando(raddrizza=passo), avvisi=avvisi) == esegui(
        dati, Comando()
    )
    assert avvisi == ["raddrizza_saltato"]


def test_il_tetto_della_variante_si_passa_nel_comando():
    dati = immagini.jpeg_qualita(Image.new("RGB", (400, 300), (90, 90, 90)), 90)
    standard, spinta = [], []
    esegui(
        dati, Comando(raddrizza={"tipo": "rotazione", "gradi": 7.0}), avvisi=standard
    )
    esegui(
        dati,
        Comando(raddrizza={"tipo": "rotazione", "gradi": 7.0, "max": 8.0}),
        avvisi=spinta,
    )
    assert standard == ["raddrizza_saltato"] and spinta == []


# --- Nel comando intero ------------------------------------------------------------


def test_il_soggetto_segue_la_foto_ruotata_e_ritagliata():
    """Una foto larga girata di 90° diventa alta: il soggetto che era a sinistra va in alto, e resta nel taglio."""
    larghezza, altezza = 3000, 1000
    img = Image.new("RGB", (larghezza, altezza), (60, 60, 60))
    ImageDraw.Draw(img).rectangle(
        [150, 300, 450, 700], fill=(255, 0, 0)
    )  # soggetto a sinistra
    box = {
        "x": 150 / larghezza,
        "y": 300 / altezza,
        "larghezza": 300 / larghezza,
        "altezza": 400 / altezza,
    }
    comando = Comando(
        ruota=90, finestra=RegoleR42(canale="instagram", soggetto_box=box)
    )
    uscita = _apri(esegui(immagini.jpeg_qualita(img, 95), comando))
    rosso = (np.asarray(uscita)[..., 0] > 200) & (np.asarray(uscita)[..., 1] < 80)
    assert rosso.any(), "il soggetto è stato tagliato via"
    # dopo la rotazione oraria di 90° il soggetto che stava a sinistra sta in alto
    righe = np.where(rosso.any(axis=1))[0]
    assert righe.mean() < uscita.height / 2


def test_la_rotazione_di_90_e_la_prima_cosa_anche_con_il_resto():
    img = Image.new("RGB", (1200, 1800), (90, 90, 90))
    uscita = _apri(esegui(immagini.jpeg_qualita(img, 90), Comando(ruota=90)))
    assert uscita.width > uscita.height  # 1800×1200, rapporto 1,5
    assert min(uscita.size) == 1080


@settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    st.integers(300, 700),
    st.integers(300, 700),
    st.floats(-5.0, 5.0),
    st.sampled_from([0, 90, 180, 270]),
)
def test_proprieta_nessuna_eccezione_con_comandi_validi(
    larghezza, altezza, gradi, ruota
):
    dati = immagini.jpeg_qualita(
        immagini.gradiente((larghezza, altezza), (10, 20, 30), (200, 180, 160)), 85
    )
    uscita = _apri(
        esegui(
            dati,
            Comando(
                ruota=ruota,
                raddrizza={"tipo": "rotazione", "gradi": gradi},
                finestra=RegoleR42(),
            ),
        )
    )
    assert min(uscita.size) == 1080
    assert 0.8 - 0.02 <= uscita.width / uscita.height <= 1.91 + 0.02
