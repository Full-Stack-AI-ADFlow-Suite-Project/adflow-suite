"""File derivati dell'archivio (RT-06, ADR-124): `derivate/<foto_id>/<chiave>.jpg`.

Stesse regole per il disco e per il finto; i metodi di prima non cambiano.
"""

import hashlib
import os

import pytest

from app.adapters.archivio import ArchivioDisco, ArchivioFinto

JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01 derivato"
PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
CHIAVE = hashlib.sha256(b"uno").hexdigest()
ALTRA = hashlib.sha256(b"due").hexdigest()


@pytest.fixture(params=["disco", "finto"])
def archivio(request, tmp_path):
    if request.param == "disco":
        return ArchivioDisco(tmp_path)
    return ArchivioFinto()


def test_salva_leggi_esiste_elimina(archivio):
    assert not archivio.esiste_derivato(7, CHIAVE)
    archivio.salva_derivato(7, CHIAVE, JPEG)
    assert archivio.esiste_derivato(7, CHIAVE)
    assert archivio.leggi_derivato(7, CHIAVE) == JPEG
    assert archivio.elimina_derivato(7, CHIAVE) is True
    assert not archivio.esiste_derivato(7, CHIAVE)
    assert archivio.elimina_derivato(7, CHIAVE) is False


def test_leggere_un_derivato_che_manca(archivio):
    with pytest.raises(FileNotFoundError):
        archivio.leggi_derivato(7, CHIAVE)


def test_salvare_due_volte_lascia_un_solo_file(archivio):
    archivio.salva_derivato(7, CHIAVE, JPEG)
    archivio.salva_derivato(7, CHIAVE, JPEG)
    assert [(d.foto_id, d.chiave) for d in archivio.elenca_derivati()] == [(7, CHIAVE)]


def test_elenca_i_derivati_di_piu_foto(archivio):
    archivio.salva_derivato(7, CHIAVE, JPEG)
    archivio.salva_derivato(8, ALTRA, JPEG)
    assert {(d.foto_id, d.chiave) for d in archivio.elenca_derivati()} == {
        (7, CHIAVE),
        (8, ALTRA),
    }


@pytest.mark.parametrize(
    "chiave",
    [
        "",
        "abc",
        "../" * 21 + "a",
        "A" * 64,  # maiuscole
        "g" * 64,  # non esadecimale
        "a" * 63,
        "a" * 65,
        "a" * 60 + "/../",
        "a" * 63 + "\n",
        "a" * 61 + "\x00ab",
    ],
)
def test_chiave_non_valida(archivio, chiave):
    with pytest.raises(ValueError):
        archivio.salva_derivato(7, chiave, JPEG)
    with pytest.raises(ValueError):
        archivio.leggi_derivato(7, chiave)
    with pytest.raises(ValueError):
        archivio.elimina_derivato(7, chiave)
    assert archivio.esiste_derivato(7, chiave) is False


@pytest.mark.parametrize("foto_id", [0, -1, "7", "../x", 7.0, None, True])
def test_foto_id_non_valido(archivio, foto_id):
    with pytest.raises(ValueError):
        archivio.salva_derivato(foto_id, CHIAVE, JPEG)
    with pytest.raises(ValueError):
        archivio.leggi_derivato(foto_id, CHIAVE)
    assert archivio.esiste_derivato(foto_id, CHIAVE) is False


def test_un_derivato_e_sempre_un_jpeg_non_vuoto(archivio):
    with pytest.raises(ValueError):
        archivio.salva_derivato(7, CHIAVE, PNG)
    with pytest.raises(ValueError):
        archivio.salva_derivato(7, CHIAVE, b"")
    assert not archivio.esiste_derivato(7, CHIAVE)


def test_il_derivato_non_tocca_gli_originali(archivio):
    originale = archivio.salva(JPEG, "jpg")
    archivio.salva_derivato(7, CHIAVE, JPEG + b"altro")
    assert archivio.leggi(originale) == JPEG
    assert archivio.esiste(originale)
    # un derivato non è visibile come originale, né con il suo nome né con la chiave
    assert not archivio.esiste(f"{CHIAVE}.jpg")
    assert not archivio.esiste("derivate")


def test_su_disco_il_file_sta_in_derivate(tmp_path):
    archivio = ArchivioDisco(tmp_path)
    archivio.salva_derivato(7, CHIAVE, JPEG)
    assert (tmp_path / "derivate" / "7" / f"{CHIAVE}.jpg").read_bytes() == JPEG
    assert [p.name for p in tmp_path.iterdir()] == ["derivate"]


def test_su_disco_un_collegamento_simbolico_fuori_non_si_segue(tmp_path):
    radice = tmp_path / "archivio"
    fuori = tmp_path / "fuori"
    fuori.mkdir()
    archivio = ArchivioDisco(radice)
    (radice / "derivate").mkdir()
    os.symlink(fuori, radice / "derivate" / "7")
    with pytest.raises(ValueError):
        archivio.salva_derivato(7, CHIAVE, JPEG)
    assert list(fuori.iterdir()) == []
    assert archivio.esiste_derivato(7, CHIAVE) is False


def test_su_disco_i_file_estranei_non_si_elencano(tmp_path):
    archivio = ArchivioDisco(tmp_path)
    archivio.salva_derivato(7, CHIAVE, JPEG)
    (tmp_path / "derivate" / "7" / "nota.jpg").write_bytes(JPEG)
    (tmp_path / "derivate" / "x").mkdir()
    (tmp_path / "derivate" / "x" / f"{ALTRA}.jpg").write_bytes(JPEG)
    assert [(d.foto_id, d.chiave) for d in archivio.elenca_derivati()] == [(7, CHIAVE)]


def test_i_metodi_di_prima_rifiutano_ancora_i_percorsi(archivio):
    with pytest.raises(ValueError):
        archivio.valida_nome_file("derivate/7/x.jpg")
    assert archivio.esiste("derivate/7/x.jpg") is False
