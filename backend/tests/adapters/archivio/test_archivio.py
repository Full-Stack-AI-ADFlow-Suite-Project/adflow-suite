"""Test per l'adattatore archivio foto (Corsia 2 · Task T1-21).

Verifica sia l'implementazione finta in memoria (ArchivioFinto) sia l'implementazione
reale su disco (ArchivioDisco su directory temporanea isolata), inclusi i controlli di sicurezza
anti-path traversal e la generazione del nome file da parte del server.
"""

from pathlib import Path
import pytest

from app.adapters.archivio import (
    ArchivioAdapter,
    ArchivioDisco,
    ArchivioFinto,
    imposta_archivio,
    ottieni_archivio,
)


def test_generazione_nome_file_sicuro():
    """Il server genera sempre un nome univoco e sanitizza l'estensione."""
    nome1 = ArchivioAdapter.genera_nome_file(".jpg")
    nome2 = ArchivioAdapter.genera_nome_file("png")
    nome3 = ArchivioAdapter.genera_nome_file(".JPEG")
    nome4 = ArchivioAdapter.genera_nome_file("..exe")
    nome5 = ArchivioAdapter.genera_nome_file("")
    nome6 = ArchivioAdapter.genera_nome_file("   ")

    assert nome1.endswith(".jpg")
    assert nome2.endswith(".png")
    assert nome3.endswith(".jpeg")
    assert nome4.endswith(".exe")
    assert nome5.endswith(".bin")
    assert nome6.endswith(".bin")
    assert nome1 != nome2
    assert len(nome1) > 32  # UUID esadecimale + estensione


def test_archivio_finto_salva_leggi_elimina():
    """ArchivioFinto memorizza e gestisce i file interamente in memoria senza toccare il disco."""
    archivio = ArchivioFinto()
    contenuto = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # Header JPEG finto

    nome = archivio.salva(contenuto, "jpg")
    assert archivio.esiste(nome) is True
    assert archivio.leggi(nome) == contenuto
    assert nome in archivio.file_salvati

    # Eliminazione
    assert archivio.elimina(nome) is True
    assert archivio.esiste(nome) is False
    assert archivio.elimina(nome) is False

    with pytest.raises(FileNotFoundError):
        archivio.leggi(nome)


def test_archivio_finto_svuota():
    """Il metodo svuota azzera i dati memorizzati."""
    archivio = ArchivioFinto()
    nome1 = archivio.salva(b"dati1", "png")
    nome2 = archivio.salva(b"dati2", "webp")
    assert len(archivio.file_salvati) == 2

    archivio.svuota()
    assert len(archivio.file_salvati) == 0
    assert archivio.esiste(nome1) is False
    assert archivio.esiste(nome2) is False


def test_archivio_disco_operazioni_base(tmp_path: Path):
    """ArchivioDisco opera correttamente sulla cartella configurata (tmp_path isolata)."""
    archivio = ArchivioDisco(radice=tmp_path)
    contenuto = b"dati-immagine-di-prova"

    nome = archivio.salva(contenuto, ".png")
    assert archivio.esiste(nome) is True

    # Verifica presenza fisica del file nella directory temporanea
    file_fisico = tmp_path / nome
    assert file_fisico.is_file()
    assert file_fisico.read_bytes() == contenuto

    # Lettura tramite adattatore
    assert archivio.leggi(nome) == contenuto
    assert archivio.percorso_file(nome) == file_fisico

    # Eliminazione
    assert archivio.elimina(nome) is True
    assert archivio.esiste(nome) is False
    assert not file_fisico.exists()
    assert archivio.elimina(nome) is False

    with pytest.raises(FileNotFoundError):
        archivio.leggi(nome)

    with pytest.raises(FileNotFoundError):
        archivio.percorso_file(nome)


def test_archivio_disco_sicurezza_path_traversal(tmp_path: Path):
    """Tentativi di risalita directory o manipolazione percorso vengono bloccati con sicurezza."""
    archivio = ArchivioDisco(radice=tmp_path)

    tentativi_malevoli = [
        "../../etc/passwd",
        "..\\..\\windows\\system32\\calc.exe",
        "sub/../../segreto.txt",
        "/assoluto/file.png",
        "file.txt:stream",
        "nome\x00nullo.jpg",
        "file*asterisco.png",
        "",
    ]

    for tentativo in tentativi_malevoli:
        with pytest.raises(ValueError):
            archivio.leggi(tentativo)

        with pytest.raises(ValueError):
            archivio.elimina(tentativo)

        assert archivio.esiste(tentativo) is False


def test_ottieni_e_imposta_archivio():
    """La factory globale permette di iniettare l'adattatore finto per i test."""
    finto = ArchivioFinto()
    imposta_archivio(finto)
    try:
        assert ottieni_archivio() is finto
    finally:
        imposta_archivio(None)  # Reset allo stato predefinito


def test_estensione_troppo_lunga_usa_bin(tmp_path: Path):
    """Un'estensione oltre il limite non produce nomi che il disco non può scrivere."""
    nome = ArchivioAdapter.genera_nome_file("a" * 300)
    assert nome.endswith(".bin")
    assert len(nome) < 255

    # Il nome generato si può davvero salvare su disco
    archivio = ArchivioDisco(radice=tmp_path)
    assert archivio.esiste(archivio.salva(b"dati", "a" * 300))

    # Al limite esatto l'estensione è accettata
    assert ArchivioAdapter.genera_nome_file("a" * 10).endswith("." + "a" * 10)


@pytest.mark.parametrize("contenuto", ["testo", 5, None, ["a"]])
def test_archivio_finto_rifiuta_contenuto_non_bytes(contenuto):
    """Il finto è severo come il disco: niente conversioni silenziose."""
    with pytest.raises(TypeError):
        ArchivioFinto().salva(contenuto, "jpg")


@pytest.mark.parametrize(
    "nome_non_valido",
    ["../x.png", "a/b.png", "x.png:ads", "x*.png", "", None, 123],
)
def test_finto_e_disco_rifiutano_gli_stessi_nomi(tmp_path: Path, nome_non_valido):
    """Finto e disco hanno lo stesso comportamento sui nomi non validi."""
    for archivio in (ArchivioFinto(), ArchivioDisco(radice=tmp_path)):
        with pytest.raises(ValueError):
            archivio.leggi(nome_non_valido)
        with pytest.raises(ValueError):
            archivio.elimina(nome_non_valido)
        assert archivio.esiste(nome_non_valido) is False
