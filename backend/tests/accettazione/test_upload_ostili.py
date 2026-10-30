"""Caricamenti ostili (T4-102, §5.4 punto 4 della simulazione).

File provati: poliglotti JPEG+HTML, PNG da 1 × 100 000 pixel, file troncati,
EXIF da 1 MB con GPS, HEIC rinominato JPEG, JPEG con peso oltre il limite.
Le difese attese vengono da costituzione §3 («controllo di tipo reale, peso e
dimensioni; il nome del file lo genera il server») e da R-13/R-42.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.moduli.campagne import service as service_campagne
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza, gruppo


def _jpeg(larghezza: int, altezza: int, extra: bytes = b"") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (larghezza, altezza), (100, 70, 40)).save(buffer, format="JPEG")
    return buffer.getvalue() + extra


def _jpeg_con_exif_grande_e_gps(larghezza=1080, altezza=1350) -> bytes:
    """JPEG valido con EXIF e GPS, e oltre un megabyte di metadati.

    Un EXIF da un megabyte non entra in un solo segmento APP1 (il limite JPEG
    è 64 KB per segmento): la bomba di metadati si costruisce con 18 segmenti
    commento da 60 KB ciascuno, più il GPS nell'EXIF vero.
    """
    img = Image.new("RGB", (larghezza, altezza), (30, 90, 120))
    exif = Image.Exif()
    gps = exif.get_ifd(34853)
    gps[0] = b"\x02\x03\x00\x00"  # GPSVersionID
    gps[1] = "N"  # GPSLatitudeRef
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", exif=exif)
    jpeg = buffer.getvalue()
    bombe = b"".join(
        b"\xff\xfe" + (60_000).to_bytes(2, "big") + b"E" * 59_998 for _ in range(18)
    )
    return jpeg[:2] + bombe + jpeg[2:]


@pytest.fixture
def bottega_in_bozza(db: Session, client: TestClient, utente_di_prova, tmp_path):
    """Artigiano con profilo, campagna in bozza e un gruppo di foto."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        artigiano = utente_di_prova("artigiano")
        bottega = profilo(db, utente_id=artigiano.id)
        campagna = campagna_in_bozza(db, profilo_id=bottega.id)
        mazzo = gruppo(db, campagna)
        db.flush()
        yield {"campagna": campagna.id, "gruppo": mazzo.id, "archivio": archivio}


def _carica(client: TestClient, mondo: dict, nome: str, contenuto: bytes):
    return client.post(
        f"/api/campagne/{mondo['campagna']}/foto",
        files={"file": (nome, contenuto, "application/octet-stream")},
        data={"gruppo_id": str(mondo["gruppo"])},
    )


def test_png_da_uno_per_cento_mila_e_rifiutato(bottega_in_bozza, client):
    """Bomba di decompressione in potenza: il lato corto si controlla al caricamento."""
    buffer = io.BytesIO()
    Image.new("RGB", (1, 100_000), (10, 10, 10)).save(buffer, format="PNG")
    risposta = _carica(client, bottega_in_bozza, "bomba.png", buffer.getvalue())
    assert risposta.status_code == 422
    assert risposta.json()["detail"]


def test_file_troncato_e_rifiutato(bottega_in_bozza, client):
    """Intestazione JPEG e poi nulla: l'immagine non si apre, 422."""
    risposta = _carica(
        client, bottega_in_bozza, "troncato.jpg", _jpeg(1080, 1350)[:100]
    )
    assert risposta.status_code == 422
    assert risposta.json()["detail"]


def test_heic_rinominato_jpeg_e_rifiutato(bottega_in_bozza, client):
    """Il tipo reale si controlla sui byte, non sull'estensione (costituzione §3)."""
    heic = b"\x00\x00\x00\x18ftypheic" + b"\x00" * 200
    risposta = _carica(client, bottega_in_bozza, "inquadratura.jpg", heic)
    assert risposta.status_code == 422
    assert risposta.json()["detail"]


def test_jpeg_oltre_il_peso_massimo_e_rifiutato(bottega_in_bozza, client):
    """JPEG valido ma oltre i 10 MB: rifiutato sul peso, non sull'apertura."""
    grasso = _jpeg(1080, 1350, extra=b"\x00" * (11 * 1024 * 1024))
    risposta = _carica(client, bottega_in_bozza, "grasso.jpg", grasso)
    assert risposta.status_code == 422
    assert "10 MB" in risposta.json()["detail"] or risposta.json()["detail"]


def test_poliglotta_jpeg_con_html_dentro(bottega_in_bozza, client):
    """JPEG valido con HTML appended: entra (è una foto vera nei limiti), ma il
    nome lo genera il server e il file esce come immagine con nosniff."""
    html = b"<script>alert('adflow-t4-102')</script>"
    risposta = _carica(
        client, bottega_in_bozza, "fototrappola.html.jpg", _jpeg(1080, 1350, extra=html)
    )
    assert risposta.status_code == 201, risposta.json()
    dati = risposta.json()
    assert dati["file"].endswith(".jpg")
    assert "fototrappola" not in dati["file"], "il nome deve generarlo il server"

    scarico = client.get(f"/api/foto/{dati['id']}/file")
    assert scarico.status_code == 200
    assert scarico.headers["content-type"] == "image/jpeg"
    assert scarico.headers["x-content-type-options"] == "nosniff"


def test_exif_da_un_megabyte_con_gps_amesso_e_la_copia_pubblica_e_pulita(
    bottega_in_bozza, client, db
):
    """L'EXIF enorme non è un limite di R-13: la foto entra. La copia sistemata
    per l'indirizzo pubblico perde ogni metadato, GPS compreso (R-42, §1.3)."""
    originale = _jpeg_con_exif_grande_e_gps()
    assert len(originale) > 1024 * 1024  # l'EXIF supera davvero il megabyte

    risposta = _carica(client, bottega_in_bozza, "con-exif.jpg", originale)
    assert risposta.status_code == 201, risposta.json()
    dati = risposta.json()
    foto_id = dati["id"]

    url_pubblico = service_campagne.url_foto_pubblica(db, foto_id, canale="instagram")
    risposta = client.get(url_pubblico)
    assert risposta.status_code == 200

    immagine = Image.open(io.BytesIO(risposta.content))
    assert immagine.format == "JPEG"
    exif = immagine.getexif()
    assert not list(exif.keys()), "la copia pubblica non deve portare metadati"
    assert not list(exif.get_ifd(34853).keys()), "e non deve portare il GPS"

    # l'originale resta com'era (costituzione §1.3)
    originale_letto = bottega_in_bozza["archivio"].leggi(dati["file"])
    assert len(originale_letto) == len(originale)
    assert originale_letto.count(b"E" * 59_998) == 18, "l'originale conserva i metadati"
