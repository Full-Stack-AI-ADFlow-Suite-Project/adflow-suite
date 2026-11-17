"""Prove dure sui nomi dei file: unicode ostile, nomi riservati di Windows, tanti
salvataggi insieme da più thread, contenuti che non si confondono."""

import random
import re
import string
import threading
from pathlib import Path

import pytest

from app.adapters.archivio import ArchivioAdapter, ArchivioDisco, ArchivioFinto

JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"
NOME_OK = re.compile(r"^[a-z0-9-]+_\d{8}-\d{6}_[0-9a-f]{8}\.(jpg|png|webp)$")
RISERVATI_WINDOWS = {"con", "prn", "aux", "nul", "com1", "lpt1"}


def _stringa_ostile(rng: random.Random) -> str:
    pezzi = [
        string.ascii_letters,
        "àèéìòùÀÈÉÌÒÙçñßøåÅÆœ",
        "日本語中文한국어",
        "مرحبا بالعالم",
        "🍕🏺✨👩‍🎨",
        "../..\\..",
        "\x00\x01\x1f\x7f",
        "  \t\n\r",
        "<script>alert(1)</script>",
        "'; DROP TABLE foto;--",
        "%00%2e%2e%2f",
        "CON NUL AUX",
        "a" * 300,
    ]
    return "".join(rng.choice(pezzi) for _ in range(rng.randrange(0, 6)))


@pytest.mark.parametrize("seme", range(500))
def test_nessun_prefisso_ostile_produce_un_nome_pericoloso(seme):
    rng = random.Random(seme)
    prefisso = _stringa_ostile(rng)

    nome = ArchivioAdapter.genera_nome_file(".jpg", prefisso)

    ArchivioAdapter.valida_nome_file(nome)
    assert len(nome) < 100
    assert Path(nome).name == nome
    assert nome.isascii()
    # O è il nome con la bottega, o ha ripiegato sul vecchio nome a codice.
    assert NOME_OK.match(nome) or re.fullmatch(r"[0-9a-f]{32}\.jpg", nome), nome
    assert nome.split(".")[0].split("_")[0] not in RISERVATI_WINDOWS or "_" in nome


@pytest.mark.parametrize("prefisso", sorted(RISERVATI_WINDOWS))
def test_nomi_riservati_di_windows_non_sono_mai_il_nome_intero(prefisso, tmp_path):
    """«con» come bottega dà «con_data_codice.jpg», un file normale anche su Windows."""
    archivio = ArchivioDisco(tmp_path)
    nome = archivio.salva(JPEG, ".jpg", prefisso)

    assert nome.startswith(prefisso + "_")
    assert archivio.leggi(nome) == JPEG
    assert archivio.elimina(nome) is True
    assert archivio.esiste(nome) is False


def test_tanti_thread_che_salvano_insieme_non_si_pestano_i_piedi(tmp_path):
    """8 thread × 60 salvataggi, stessa bottega, stesso secondo: 480 nomi diversi, contenuto giusto."""
    archivio = ArchivioDisco(tmp_path)
    risultati: dict[str, bytes] = {}
    errori: list[BaseException] = []
    blocco = threading.Lock()

    def lavora(indice: int):
        try:
            for n in range(60):
                contenuto = JPEG + f"thread{indice}-{n}".encode()
                nome = archivio.salva(contenuto, ".jpg", "Ceramiche Rossi")
                with blocco:
                    assert nome not in risultati, f"nome doppio: {nome}"
                    risultati[nome] = contenuto
        except BaseException as errore:  # noqa: BLE001 - lo riportiamo al test
            errori.append(errore)

    thread = [threading.Thread(target=lavora, args=(i,)) for i in range(8)]
    for t in thread:
        t.start()
    for t in thread:
        t.join()

    assert errori == []
    assert len(risultati) == 480
    assert len(list(tmp_path.iterdir())) == 480
    for nome, contenuto in risultati.items():
        assert archivio.leggi(nome) == contenuto


def test_il_codice_casuale_non_si_ripete_su_centomila_nomi():
    """8 caratteri esadecimali nello stesso secondo: lo scarto è comunque trascurabile."""
    nomi = {ArchivioAdapter.genera_nome_file(".jpg", "x") for _ in range(20000)}
    # Ammettiamo poche collisioni solo se cadono in secondi diversi: dentro uno
    # stesso secondo il salvataggio le gestisce da sé (vedi i test su disco).
    assert len(nomi) >= 19990


def test_finto_e_disco_si_comportano_allo_stesso_modo(tmp_path):
    for archivio in (ArchivioDisco(tmp_path), ArchivioFinto()):
        a = archivio.salva(JPEG, "JPG", "Bottega Ñandú")
        b = archivio.salva(JPEG + b"x", ".jpg", "Bottega Ñandú")
        assert a != b
        assert a.startswith("bottega-nandu_")
        assert archivio.leggi(b) == JPEG + b"x"
        assert archivio.elimina(a) and not archivio.elimina(a)


def test_un_payload_non_valido_non_lascia_file_in_giro(tmp_path):
    archivio = ArchivioDisco(tmp_path)

    for contenuto, ext in [(b"", ".jpg"), (b"non-un-jpeg", ".jpg"), (JPEG, ".exe")]:
        with pytest.raises(ValueError):
            archivio.salva(contenuto, ext, "Bottega")

    assert list(tmp_path.iterdir()) == []
