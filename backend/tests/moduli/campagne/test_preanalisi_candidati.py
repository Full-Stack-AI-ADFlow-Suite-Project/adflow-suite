"""I candidati della pre-analisi: volti e quadrilateri, e i segni sulla copia per l'AI (RT-14)."""

from __future__ import annotations

import math

import numpy as np
import pytest
from PIL import Image

from app.moduli.campagne import preanalisi
from tests import immagini


def _errore_angoli(trovati: list[list[float]], veri, dimensioni) -> float:
    """Il peggior scarto fra un angolo vero e il più vicino trovato, in quota del lato lungo."""
    lato = max(dimensioni)
    scarti = []
    for vx, vy in veri:
        scarti.append(
            min(
                math.hypot(x * dimensioni[0] - vx, y * dimensioni[1] - vy)
                for x, y in trovati
            )
        )
    return max(scarti) / lato


# --- Quadrilateri ------------------------------------------------------------------


@pytest.mark.parametrize("gradi", [0.0, 3.0, -4.0, 8.0])
def test_rettangolo_inclinato_trovato_con_errore_sotto_l_uno_per_cento(gradi):
    immagine, veri = immagini.rettangolo_inclinato((800, 600), gradi)
    quadri = preanalisi.candidati(immagine, lambda _: [])["quadrilateri"]
    assert quadri, "il rettangolo non è stato trovato"
    primo = quadri[0]
    assert primo["id"] == "Q1"
    assert _errore_angoli(primo["angoli"], veri, immagine.size) < 0.01
    assert primo["area"] == pytest.approx(480 * 320 / (800 * 600), rel=0.05)


def test_gli_angoli_sono_in_ordine_e_normalizzati():
    immagine, veri = immagini.rettangolo_inclinato((800, 600), 3.0)
    angoli = preanalisi.candidati(immagine, lambda _: [])["quadrilateri"][0]["angoli"]
    assert len(angoli) == 4
    assert all(0.0 <= v <= 1.0 for punto in angoli for v in punto)
    # alto-sinistra, alto-destra, basso-destra, basso-sinistra come la verità
    for trovato, vero in zip(angoli, veri):
        assert math.hypot(trovato[0] * 800 - vero[0], trovato[1] * 600 - vero[1]) < 8


def test_nessun_quadrilatero_su_un_gradiente():
    assert (
        preanalisi.candidati(immagini.gradiente((800, 600)), lambda _: [])[
            "quadrilateri"
        ]
        == []
    )


def test_nessun_quadrilatero_su_tinta_unita():
    assert (
        preanalisi.candidati(
            immagini.tinta_unita((90, 90, 90), (400, 300)), lambda _: []
        )["quadrilateri"]
        == []
    )


def test_un_oggetto_troppo_piccolo_non_e_un_candidato():
    immagine, _ = immagini.rettangolo_inclinato((800, 600), 3.0, lati=(100, 80))
    assert preanalisi.candidati(immagine, lambda _: [])["quadrilateri"] == []


def test_al_massimo_tre_quadrilateri():
    immagine = Image.new("RGB", (900, 900), (20, 20, 20))
    from PIL import ImageDraw

    pennello = ImageDraw.Draw(immagine)
    for i in range(5):
        x = 20 + (i % 3) * 290
        y = 20 + (i // 3) * 440
        pennello.rectangle([x, y, x + 260, y + 260], fill=(200 - i * 20, 180, 140))
    assert len(preanalisi.candidati(immagine, lambda _: [])["quadrilateri"]) == 3


# --- Volti (con il rilevatore finto, D8) -------------------------------------------


def _finto(*volti):
    return lambda _: list(volti)


def test_i_volti_diventano_v1_v2_da_sinistra_a_destra():
    rilevatore = _finto(
        (0.60, 0.30, 0.06, 0.08, 0.7),  # a destra, ma dato per primo
        (0.10, 0.28, 0.07, 0.09, 0.9),
    )
    volti = preanalisi.candidati(
        immagini.tinta_unita((90, 90, 90), (400, 300)), rilevatore
    )["volti"]
    assert [v["id"] for v in volti] == ["V1", "V2"]
    assert volti[0]["box"]["x"] == pytest.approx(0.10)
    assert volti[1]["box"]["x"] == pytest.approx(0.60)
    assert volti[0]["affidabilita"] == pytest.approx(0.9)


def test_i_codici_non_dipendono_dall_ordine_del_rilevatore():
    a = (0.10, 0.28, 0.07, 0.09, 0.9)
    b = (0.60, 0.30, 0.06, 0.08, 0.7)
    foto = immagini.tinta_unita((90, 90, 90), (400, 300))
    assert (
        preanalisi.candidati(foto, _finto(a, b))["volti"]
        == preanalisi.candidati(foto, _finto(b, a))["volti"]
    )


def test_due_riquadri_sullo_stesso_volto_restano_uno_il_piu_affidabile():
    foto = immagini.tinta_unita((90, 90, 90), (400, 300))
    volti = preanalisi.candidati(
        foto, _finto((0.10, 0.28, 0.07, 0.09, 0.5), (0.105, 0.285, 0.07, 0.09, 0.8))
    )["volti"]
    assert len(volti) == 1 and volti[0]["affidabilita"] == pytest.approx(0.8)


def test_al_massimo_dodici_volti():
    foto = immagini.tinta_unita((90, 90, 90), (400, 300))
    tanti = [(0.01 + 0.07 * i, 0.4, 0.05, 0.07, 0.6) for i in range(14)]
    assert (
        len(preanalisi.candidati(foto, _finto(*tanti))["volti"]) == preanalisi.MAX_VOLTI
    )


def test_nessun_candidato_su_una_foto_senza_niente():
    trovati = preanalisi.candidati(
        immagini.tinta_unita((90, 90, 90), (400, 300)), _finto()
    )
    assert trovati == {"volti": [], "quadrilateri": []}


# --- Il rilevatore vero (Haar) -----------------------------------------------------


def test_le_cascate_di_haar_si_caricano_e_non_trovano_volti_in_una_scacchiera():
    assert not preanalisi._cascata("haarcascade_frontalface_default.xml").empty()
    assert not preanalisi._cascata("haarcascade_profileface.xml").empty()
    for immagine in (
        immagini.nitida((800, 600)),
        immagini.gradiente((800, 600)),
        immagini.tinta_unita((9, 9, 9), (50, 40)),
    ):
        assert preanalisi.rileva_volti_haar(immagine) == []


def test_il_rilevatore_vero_e_quello_predefinito():
    trovati = preanalisi.candidati(immagini.gradiente((400, 300)))
    assert trovati["volti"] == []


# --- I segni -----------------------------------------------------------------------


def test_senza_candidati_i_segni_non_cambiano_l_immagine():
    foto = immagini.tinta_unita((90, 90, 90), (400, 300))
    assert preanalisi.disegna_segni(foto, {"volti": [], "quadrilateri": []}) is foto


def test_i_segni_si_disegnano_su_una_copia_e_solo_dove_servono():
    foto = immagini.tinta_unita((90, 90, 90), (400, 300))
    prima = np.asarray(foto).copy()
    trovati = preanalisi.candidati(foto, _finto((0.30, 0.30, 0.20, 0.30, 0.9)))
    disegnata = preanalisi.disegna_segni(foto, trovati)
    assert disegnata is not foto
    assert np.array_equal(np.asarray(foto), prima), "l'originale è stato toccato"
    dopo = np.asarray(disegnata).astype(int)
    cambiati = np.argwhere(np.abs(dopo - prima.astype(int)).sum(axis=2) > 0)
    assert len(cambiati) > 50
    # il riquadro è sottile: i pixel cambiati stanno tutti vicino al bordo o nell'etichetta
    colore = np.array(preanalisi.COLORE_SEGNI)
    assert (dopo[cambiati[:, 0], cambiati[:, 1]] == colore).all(axis=1).mean() > 0.5
    # il centro del volto resta intatto
    assert (dopo[150, 160] == prima[150, 160]).all()


def test_i_segni_dei_quadrilateri_seguono_i_lati():
    immagine, veri = immagini.rettangolo_inclinato((800, 600), 3.0)
    trovati = preanalisi.candidati(immagine, _finto())
    disegnata = np.asarray(preanalisi.disegna_segni(immagine, trovati))
    colore = np.array(preanalisi.COLORE_SEGNI)
    sul_primo_lato = []
    (x0, y0), (x1, y1) = veri[0], veri[1]
    for t in np.linspace(0.1, 0.9, 9):
        x, y = int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)
        vicino = disegnata[y - 4 : y + 5, x - 4 : x + 5].reshape(-1, 3)
        sul_primo_lato.append((vicino == colore).all(axis=1).any())
    assert all(sul_primo_lato)


def test_i_segni_sono_spenti_per_impostazione():
    from app.core.config import Impostazioni

    assert (
        Impostazioni(
            _env_file=None,
            database_url="postgresql+psycopg://a:b@h/d",
            database_url_test="postgresql+psycopg://a:b@h/t",
        ).ritocco_segni
        is False
    )
