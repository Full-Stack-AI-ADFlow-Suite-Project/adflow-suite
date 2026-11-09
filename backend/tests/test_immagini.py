"""Prove degli strumenti di test per le immagini (RT-01, ADR-124).

Ogni generatore deve produrre ciò che dichiara: se questi test sbagliano, tutti
i test numerici del ritocco che si appoggiano a `tests/immagini.py` sono
inaffidabili. Non toccano il database.
"""

from io import BytesIO

import numpy as np
import pytest
from PIL import Image, ImageCms

from tests import immagini


def _converti(img: Image.Image, da: bytes, a: bytes) -> Image.Image:
    profilo_da = ImageCms.ImageCmsProfile(BytesIO(da))
    profilo_a = ImageCms.ImageCmsProfile(BytesIO(a))
    return ImageCms.profileToProfile(
        img,
        profilo_da,
        profilo_a,
        renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
        outputMode="RGB",
    )


# --- Profili ICC ---------------------------------------------------------------


@pytest.mark.parametrize("nome", ["srgb", "p3"])
def test_il_profilo_e_letto_da_littlecms(nome: str) -> None:
    profilo = ImageCms.ImageCmsProfile(BytesIO(immagini.profilo_icc(nome)))
    assert ImageCms.getProfileName(profilo).strip()
    assert profilo.profile.xcolor_space.strip() == "RGB"


def test_srgb_generato_riconverte_i_colori_senza_cambiarli() -> None:
    sorgente = immagini.gradiente((256, 4))
    colori = Image.new("RGB", (6, 1))
    colori.putdata(
        [
            (0, 0, 0),
            (255, 255, 255),
            (128, 128, 128),
            (239, 35, 17),
            (10, 200, 90),
            (7, 7, 250),
        ]
    )
    for img in (sorgente, colori):
        uscita = _converti(
            img, immagini.profilo_icc("srgb"), immagini.profilo_icc("srgb")
        )
        differenza = np.abs(
            np.asarray(uscita, dtype=int) - np.asarray(img, dtype=int)
        ).max()
        assert differenza <= 1


def test_srgb_generato_coincide_con_quello_di_littlecms() -> None:
    colori = Image.new("RGB", (5, 1))
    colori.putdata(
        [(0, 0, 0), (255, 255, 255), (128, 128, 128), (239, 35, 17), (10, 200, 90)]
    )
    interno = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    uscita = _converti(colori, immagini.profilo_icc("srgb"), interno)
    differenza = np.abs(
        np.asarray(uscita, dtype=int) - np.asarray(colori, dtype=int)
    ).max()
    assert differenza <= 2


def test_i_grigi_p3_restano_grigi_in_srgb() -> None:
    grigi = Image.new("RGB", (4, 1))
    grigi.putdata([(0, 0, 0), (60, 60, 60), (128, 128, 128), (255, 255, 255)])
    uscita = _converti(grigi, immagini.profilo_icc("p3"), immagini.profilo_icc("srgb"))
    differenza = np.abs(
        np.asarray(uscita, dtype=int) - np.asarray(grigi, dtype=int)
    ).max()
    assert differenza <= 1


def test_il_rosso_p3_esce_dalla_gamma_srgb() -> None:
    rosso = Image.new("RGB", (1, 1), (255, 0, 0))
    uscita = _converti(rosso, immagini.profilo_icc("p3"), immagini.profilo_icc("srgb"))
    r, g, b = uscita.getpixel((0, 0))
    assert r == 255 and g <= 5 and b <= 5


@pytest.mark.parametrize(
    ("p3", "srgb"),
    [
        ((220, 60, 40), (239, 35, 17)),  # pomodoro
        ((60, 150, 60), (0, 152, 44)),  # basilico
        ((230, 90, 140), (249, 77, 141)),  # rosa
        ((205, 160, 110), (213, 158, 102)),  # pane
    ],
)
def test_i_colori_p3_della_nota_diventano_quelli_attesi_in_srgb(p3, srgb) -> None:
    # Valori della nota 12.1, ottenuti con lo stesso metodo (primari pubblici,
    # Bradford a D50, curva sRGB) e LittleCMS: ±2 per le approssimazioni.
    uscita = _converti(
        Image.new("RGB", (1, 1), p3),
        immagini.profilo_icc("p3"),
        immagini.profilo_icc("srgb"),
    ).getpixel((0, 0))
    assert all(abs(u - a) <= 2 for u, a in zip(uscita, srgb)), (uscita, srgb)


# --- Immagini ------------------------------------------------------------------


def test_tinta_unita_ha_dimensioni_e_colore_dichiarati() -> None:
    img = immagini.tinta_unita((10, 20, 30), (7, 5))
    assert img.size == (7, 5)
    assert {tuple(p) for p in np.asarray(img).reshape(-1, 3)} == {(10, 20, 30)}


def test_gradiente_orizzontale_e_verticale() -> None:
    orizzontale = immagini.gradiente((256, 8))
    assert orizzontale.getpixel((0, 0)) == (0, 0, 0)
    assert orizzontale.getpixel((255, 7)) == (255, 255, 255)
    assert orizzontale.getpixel((100, 0)) == orizzontale.getpixel((100, 7))
    verticale = immagini.gradiente((8, 256), verticale=True)
    assert verticale.getpixel((0, 0)) == (0, 0, 0)
    assert verticale.getpixel((7, 255)) == (255, 255, 255)
    assert verticale.getpixel((0, 100)) == verticale.getpixel((7, 100))


def test_con_dominante_sposta_i_canali_e_taglia() -> None:
    img = immagini.con_dominante(immagini.tinta_unita((100, 100, 100)), (50, 0, -200))
    assert img.getpixel((0, 0)) == (150, 100, 0)


def test_rettangolo_inclinato_ha_gli_angoli_dichiarati() -> None:
    img, angoli = immagini.rettangolo_inclinato((800, 600), 3.0, (480, 320))
    assert img.size == (800, 600)
    assert len(angoli) == 4
    # Lo spigolo alto è inclinato di 3 gradi rispetto all'orizzontale.
    (x0, y0), (x1, y1) = angoli[0], angoli[1]
    angolo = np.degrees(np.arctan2(y1 - y0, x1 - x0))
    assert angolo == pytest.approx(3.0, abs=1e-6)
    # Il centro è del colore del rettangolo, l'angolo dell'immagine dello sfondo.
    assert img.getpixel((400, 300)) == (200, 180, 140)
    assert img.getpixel((2, 2)) == (30, 30, 30)


def test_linee_inclinate_hanno_la_pendenza_dichiarata() -> None:
    img = immagini.linee_inclinate((800, 600), angolo_gradi=3.0, passo=60)
    grigio = np.asarray(img.convert("L"), dtype=int)
    chiari = np.argwhere(grigio > 200)
    # Prima colonna e ultima colonna della stessa linea: la y sale di tan(3°)·larghezza.
    prima = chiari[chiari[:, 1] == 0][:, 0]
    ultima = chiari[chiari[:, 1] == 799][:, 0]
    assert len(prima) and len(ultima)
    scarto = [abs(ultima_y - prima_y) for prima_y in prima[:1] for ultima_y in ultima]
    atteso = np.tan(np.radians(3.0)) * 799
    assert min(abs(s - atteso) for s in scarto) <= 4


def test_sfocata_ha_meno_dettaglio_della_nitida() -> None:
    nitida = immagini.nitida((128, 128))
    sfocata = immagini.sfocata(nitida, 4.0)

    def contrasto(img: Image.Image) -> float:
        a = np.asarray(img.convert("L"), dtype=float)
        return float(np.abs(np.diff(a, axis=1)).mean())

    assert contrasto(sfocata) < contrasto(nitida) / 3


# --- File codificati -----------------------------------------------------------


def test_jpeg_qualita_dichiarata_si_legge_dalle_tabelle() -> None:
    img = immagini.gradiente((128, 128))
    bassa = immagini.apri(immagini.jpeg_qualita(img, 30)).quantization
    alta = immagini.apri(immagini.jpeg_qualita(img, 95)).quantization
    assert sum(bassa[0]) > sum(alta[0]) * 3
    assert immagini.apri(immagini.jpeg_qualita(img, 90)).format == "JPEG"


def test_jpeg_con_exif_porta_orientamento_flash_e_gps() -> None:
    dati = immagini.jpeg_con_exif(
        immagini.tinta_unita((90, 90, 90), (40, 20)), orientamento=6, flash=1, gps=True
    )
    exif = immagini.apri(dati).getexif()
    assert exif[0x0112] == 6
    assert exif.get_ifd(0x8769)[0x9209] == 1
    assert exif.get_ifd(0x8825)[1] == "N"


def test_jpeg_con_exif_senza_opzioni_non_ha_orientamento_ne_gps() -> None:
    exif = immagini.apri(
        immagini.jpeg_con_exif(immagini.tinta_unita((1, 2, 3)))
    ).getexif()
    assert 0x0112 not in exif
    assert not exif.get_ifd(0x8825)


def test_png_con_icc_ha_il_chunk_iccp() -> None:
    profilo = immagini.profilo_icc("p3")
    dati = immagini.png_con_icc(immagini.tinta_unita((200, 20, 20)), profilo)
    assert b"iCCP" in dati
    assert immagini.apri(dati).info["icc_profile"] == profilo


def test_webp_con_icc_porta_il_profilo() -> None:
    profilo = immagini.profilo_icc("p3")
    dati = immagini.webp_con_icc(immagini.tinta_unita((200, 20, 20)), profilo)
    assert immagini.apri(dati).format == "WEBP"
    assert immagini.apri(dati).info.get("icc_profile") == profilo


def test_jpeg_cmyk_e_cmyk() -> None:
    img = immagini.apri(immagini.jpeg_cmyk((16, 16)))
    assert img.format == "JPEG"
    assert img.mode == "CMYK"


# --- Colore e distanze ---------------------------------------------------------


def test_delta_e_di_colori_noti() -> None:
    assert immagini.delta_e((120, 80, 200), (120, 80, 200)) == 0.0
    # Bianco e nero: ΔE76 = L* del bianco = 100.
    assert immagini.delta_e((0, 0, 0), (255, 255, 255)) == pytest.approx(
        100.0, abs=0.05
    )
    # Una differenza di un solo livello su un canale è sotto la soglia di notabilità.
    assert 0 < immagini.delta_e((120, 120, 120), (121, 120, 120)) < 1.0


def test_delta_e_tra_immagini_e_tra_immagine_e_colore() -> None:
    a = immagini.tinta_unita((10, 200, 10), (8, 8))
    b = immagini.tinta_unita((200, 10, 10), (8, 8))
    assert immagini.delta_e(a, a) == 0.0
    assert immagini.delta_e(a, b) == immagini.delta_e(b, a) > 50
    assert immagini.delta_e(a, (10, 200, 10)) == 0.0


def test_media_lab_su_tutta_l_immagine_e_su_un_riquadro() -> None:
    img = Image.new("RGB", (20, 10), (0, 0, 0))
    img.paste((255, 255, 255), (10, 0, 20, 10))
    assert immagini.media_lab(img)[0] == pytest.approx(50.0, abs=0.05)
    assert immagini.media_lab(img, (10, 0, 20, 10))[0] == pytest.approx(100.0, abs=0.05)
    assert immagini.media_lab(img, (0, 0, 10, 10))[0] == pytest.approx(0.0, abs=0.05)
