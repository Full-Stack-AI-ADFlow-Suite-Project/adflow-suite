"""L'esecutore a passi fissi (RT-04, ADR-124, nota 7.5).

Immagini sintetiche (`tests/immagini.py`); nessun database. Le regole di rapporto
di R-42 le coprono già i test di `test_sistemazione_foto.py`, che passano dallo
stesso esecutore.
"""

from __future__ import annotations

from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from app.core.errori import DatiNonValidi
from app.moduli.campagne import esecutore
from app.moduli.campagne.colore import profilo_srgb_bytes
from app.moduli.campagne.esecutore import (
    PASSI,
    Comando,
    RegoleR42,
    comando_originale,
    esegui,
    sistema_foto_buffer,
)
from tests import immagini


def _apri(dati: bytes) -> Image.Image:
    return Image.open(BytesIO(dati))


def _png(img: Image.Image) -> bytes:
    buffer = BytesIO()
    img.save(buffer, "PNG")
    return buffer.getvalue()


def _foto_buona(larghezza: int = 1600, altezza: int = 1200) -> Image.Image:
    """Una foto «normale»: toni medi, contrasto pieno, grana leggera (nessun difetto)."""
    base = immagini.gradiente((larghezza, altezza), (30, 40, 60), (225, 215, 190))
    rumore = np.random.default_rng(7).integers(-3, 4, (altezza, larghezza, 1))
    matrice = np.clip(np.asarray(base, dtype=int) + rumore, 0, 255).astype(np.uint8)
    return Image.fromarray(matrice, "RGB")


# --- Ordine e forma ------------------------------------------------------------


def test_i_dieci_passi_girano_in_ordine_fisso() -> None:
    traccia: list[str] = []
    esegui(_png(immagini.nitida((200, 150))), comando_originale(), traccia=traccia)
    assert traccia == list(PASSI)
    assert PASSI == (
        "decodifica",
        "srgb",
        "ruota",
        "privacy",
        "raddrizza",
        "finestra",
        "lato_corto",
        "luce",
        "nitidezza",
        "codifica",
    )


def test_il_comando_originale_e_quello_di_r42() -> None:
    comando = comando_originale(canale="facebook", proporzione="4:5")
    assert comando.finestra == RegoleR42("facebook", "4:5", None)
    assert comando.ruota == 0 and comando.luce is None and not comando.nitidezza
    assert comando.versione == esecutore.VERSIONE_ESECUTORE


def test_il_riquadro_del_soggetto_si_prende_dall_analisi_della_foto() -> None:
    class Foto:
        analisi_ai = {
            "soggetto_box": {"x": 0.1, "y": 0.2, "larghezza": 0.3, "altezza": 0.4}
        }

    assert comando_originale(Foto()).finestra.soggetto_box == {
        "x": 0.1,
        "y": 0.2,
        "larghezza": 0.3,
        "altezza": 0.4,
    }
    assert (
        comando_originale(Foto(), soggetto_box=None).finestra.soggetto_box is not None
    )
    assert comando_originale(object()).finestra.soggetto_box is None


def test_rotazione_non_ammessa_solleva() -> None:
    with pytest.raises(DatiNonValidi):
        Comando(ruota=45)
    assert Comando(ruota=270).ruota == 270


def test_il_sistema_foto_buffer_e_l_esecutore_con_il_comando_originale() -> None:
    dati = _png(_foto_buona(1500, 1000))
    assert sistema_foto_buffer(dati, "instagram", None, None) == esegui(
        dati, comando_originale()
    )


# --- Uscita --------------------------------------------------------------------


def test_nessun_metadato_e_profilo_srgb() -> None:
    dati = immagini.jpeg_con_exif(
        _foto_buona(1400, 1000),
        orientamento=1,
        flash=1,
        gps=True,
        profilo=immagini.profilo_icc("p3"),
    )
    uscita = _apri(esegui(dati, comando_originale()))
    exif = uscita.getexif()
    assert not exif and not exif.get_ifd(0x8825) and not exif.get_ifd(0x8769)
    assert uscita.info.get("icc_profile") == profilo_srgb_bytes()
    assert uscita.format == "JPEG" and uscita.mode == "RGB"


@pytest.mark.parametrize(
    "dimensioni", [(3000, 2000), (800, 800), (500, 1500), (4000, 900), (1200, 1500)]
)
def test_lato_corto_1080(dimensioni) -> None:
    uscita = _apri(esegui(_png(immagini.nitida(dimensioni, 40)), comando_originale()))
    assert min(uscita.size) == 1080


def test_senza_finestra_non_si_taglia_nulla() -> None:
    uscita = _apri(esegui(_png(immagini.nitida((3000, 1000), 40)), Comando()))
    assert uscita.size == (3240, 1080)


def test_canale_o_proporzione_non_validi_sollevano_prima_di_decodificare() -> None:
    with pytest.raises(DatiNonValidi, match="Canale"):
        esegui(b"non importa", comando_originale(canale="tiktok"))
    with pytest.raises(DatiNonValidi, match="Proporzione"):
        esegui(_png(immagini.nitida((200, 200))), comando_originale(proporzione="9:16"))
    with pytest.raises(DatiNonValidi, match="Nessun dato"):
        esegui(b"", comando_originale())


def test_il_limite_di_pixel_si_legge_a_ogni_chiamata(monkeypatch) -> None:
    from app.moduli.campagne import sistemazione_foto

    monkeypatch.setattr(sistemazione_foto, "MAX_PIXEL_TOTALI", 100)
    with pytest.raises(DatiNonValidi, match="troppo grande"):
        esegui(_png(immagini.nitida((50, 50))), comando_originale())


# --- Fine dell'autocontrasto ---------------------------------------------------


def test_le_foto_buone_escono_come_sono_senza_autocontrasto() -> None:
    originale = _foto_buona(1600, 1200)
    uscita = _apri(esegui(_png(originale), comando_originale()))
    attesa = originale.resize(uscita.size, Image.Resampling.LANCZOS)
    assert immagini.delta_e(uscita, attesa) < 1.0  # criterio del piano (RT-04)
    # Il tono medio non si sposta: il resto della distanza è il rumore del JPEG.
    spostamento = np.subtract(immagini.media_lab(uscita), immagini.media_lab(attesa))
    assert np.abs(spostamento).max() < 0.5


def test_una_foto_a_basso_contrasto_non_viene_stirata() -> None:
    # Con l'autocontrasto di prima i toni 100–150 sarebbero andati verso 0–255.
    piatta = immagini.gradiente((1200, 900), (100, 100, 100), (150, 150, 150))
    uscita = np.asarray(_apri(esegui(_png(piatta), comando_originale())))
    assert uscita.min() >= 96 and uscita.max() <= 154


def test_una_foto_bruciata_o_scura_non_cambia_di_tono() -> None:
    scura = immagini.gradiente((1200, 900), (5, 5, 5), (70, 70, 70))
    uscita = np.asarray(_apri(esegui(_png(scura), comando_originale())))
    assert uscita.max() <= 74
