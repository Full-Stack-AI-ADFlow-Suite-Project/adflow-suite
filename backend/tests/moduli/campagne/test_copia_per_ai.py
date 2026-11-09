"""La copia della foto per l'AI, preparata dal modulo (RT-03, ADR-124).

sRGB, al massimo 1024 px sul lato lungo, JPEG qualità 85; l'originale non cambia.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.errori import DatiNonValidi, NonTrovato
from app.moduli.campagne import service
from app.moduli.campagne.models import Foto
from tests import immagini
from tests.moduli.artigiani.fabbrica import profilo


@pytest.fixture
def archivio():
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


def _foto(db, archivio, dati: bytes, estensione: str, mime: str) -> Foto:
    record = Foto(
        profilo_id=profilo(db).id,
        file=archivio.salva(dati, estensione),
        mime=mime,
        larghezza=3000,
        altezza=2000,
        origine="caricata",
        da_usare=False,
        pubblicata_su={},
    )
    db.add(record)
    db.flush()
    return record


def _png_p3(larghezza: int, altezza: int, colore=(220, 60, 40)) -> bytes:
    return immagini.png_con_icc(
        immagini.tinta_unita(colore, (larghezza, altezza)), immagini.profilo_icc("p3")
    )


def test_la_copia_e_un_jpeg_di_al_massimo_1024_px(db, archivio) -> None:
    foto = _foto(db, archivio, _png_p3(3000, 2000), "png", "image/png")
    copia = Image.open(BytesIO(service.copia_per_ai(db, foto.id)))
    assert copia.format == "JPEG"
    assert max(copia.size) == 1024
    assert copia.size == (1024, 683)


def test_una_foto_piccola_non_si_ingrandisce(db, archivio) -> None:
    foto = _foto(db, archivio, _png_p3(400, 300), "png", "image/png")
    assert Image.open(BytesIO(service.copia_per_ai(db, foto.id))).size == (400, 300)


def test_l_ai_riceve_colori_srgb_non_numeri_p3(db, archivio) -> None:
    foto = _foto(db, archivio, _png_p3(1200, 800), "png", "image/png")
    copia = Image.open(BytesIO(service.copia_per_ai(db, foto.id)))
    r, g, b = copia.getpixel((100, 100))
    assert abs(r - 239) <= 4 and abs(g - 35) <= 4 and abs(b - 17) <= 4


def test_la_copia_e_dritta_e_senza_exif(db, archivio) -> None:
    dati = immagini.jpeg_con_exif(
        immagini.tinta_unita((90, 90, 90), (200, 100)), orientamento=6, gps=True
    )
    foto = _foto(db, archivio, dati, "jpg", "image/jpeg")
    copia = Image.open(BytesIO(service.copia_per_ai(db, foto.id)))
    assert copia.size == (100, 200)
    assert not copia.getexif()


def test_la_qualita_e_85(db, archivio) -> None:
    img = immagini.gradiente((1200, 800), (0, 0, 0), (255, 200, 120))
    buffer = BytesIO()
    img.save(buffer, "PNG")
    foto = _foto(db, archivio, buffer.getvalue(), "png", "image/png")
    tabelle = Image.open(BytesIO(service.copia_per_ai(db, foto.id))).quantization
    attese = Image.open(BytesIO(immagini.jpeg_qualita(img, 85))).quantization
    assert tabelle[0] == attese[0]


def test_l_originale_resta_intatto(db, archivio) -> None:
    dati = _png_p3(2000, 1500)
    foto = _foto(db, archivio, dati, "png", "image/png")
    service.copia_per_ai(db, foto.id)
    assert archivio.leggi(foto.file) == dati


def test_foto_inesistente_o_senza_file_non_si_trova(db, archivio) -> None:
    with pytest.raises(NonTrovato):
        service.copia_per_ai(db, 999_999)
    foto = _foto(db, archivio, _png_p3(100, 100), "png", "image/png")
    archivio.elimina(foto.file)
    with pytest.raises(NonTrovato):
        service.copia_per_ai(db, foto.id)


def test_file_illeggibile_solleva_dati_non_validi(db, archivio) -> None:
    foto = _foto(db, archivio, b"\xff\xd8\xff non e' un jpeg", "jpg", "image/jpeg")
    with pytest.raises(DatiNonValidi):
        service.copia_per_ai(db, foto.id)
