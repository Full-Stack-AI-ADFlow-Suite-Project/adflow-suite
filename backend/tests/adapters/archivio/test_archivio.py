"""Test completi per l'adattatore archivio foto.

Copre:
1. Protezione DoS: limite dimensione massima payload (10 MB come da Spec R-13);
2. Integrità ed estensioni: whitelist formati (JPG, PNG, WEBP) e verifica magic bytes;
3. Anti-TOCTOU: eliminazione concorrente sicura senza eccezioni non gestite;
4. Isolamento stato: context manager `usa_archivio` con ripristino deterministico;
5. Sicurezza Directory Traversal (CWE-22) su nomi e percorsi;
6. Coerenza completa tra ArchivioDisco e ArchivioFinto.
"""

from pathlib import Path
import re
import pytest

from app.adapters.archivio import (
    DIMENSIONE_MAX_BYTE,
    ArchivioAdapter,
    ArchivioDisco,
    ArchivioFinto,
    ottieni_archivio,
    usa_archivio,
)

# Header di esempio validi per i formati supportati
PNG_TEST = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
JPEG_TEST = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"
WEBP_TEST = b"RIFF\x14\x00\x00\x00WEBPVP8 \x08\x00\x00\x00"


def test_generazione_nome_file_sicuro():
    """Il server genera sempre un nome univoco e sanitizza l'estensione consentita."""
    nome1 = ArchivioAdapter.genera_nome_file(".jpg")
    nome2 = ArchivioAdapter.genera_nome_file("png")
    nome3 = ArchivioAdapter.genera_nome_file(".JPEG")
    nome4 = ArchivioAdapter.genera_nome_file("webp")

    assert nome1.endswith(".jpg")
    assert nome2.endswith(".png")
    assert nome3.endswith(".jpeg")
    assert nome4.endswith(".webp")
    assert len(nome1) > 32  # UUID esadecimale + estensione
    assert nome1 != nome2


def test_nome_file_leggibile_con_prefisso_data_e_codice():
    """Con un prefisso il nome è ``bottega_AAAAMMGG-HHMMSS_codice.ext``, senza accenti né simboli."""
    nome = ArchivioAdapter.genera_nome_file(".jpg", "Ceramiche D'Èrùta & Figli!")

    assert re.fullmatch(r"ceramiche-d-eruta-figli_\d{8}-\d{6}_[0-9a-f]{8}\.jpg", nome)
    ArchivioAdapter.valida_nome_file(nome)


def test_nome_file_con_prefisso_non_scappa_dalla_cartella():
    """Il prefisso passa dal filtro: niente separatori, risalite o caratteri riservati."""
    nome = ArchivioAdapter.genera_nome_file("png", "../../etc/passwd\x00:*?")

    assert "/" not in nome and "\\" not in nome and ".." not in nome
    ArchivioAdapter.valida_nome_file(nome)


def test_nome_file_prefisso_vuoto_o_senza_lettere_torna_al_codice():
    """Un prefisso che non lascia lettere o cifre dà il vecchio nome ``<uuid>.ext``."""
    for prefisso in ("", "   ", "§§§", None):
        nome = ArchivioAdapter.genera_nome_file(".webp", prefisso)  # type: ignore[arg-type]
        assert re.fullmatch(r"[0-9a-f]{32}\.webp", nome)


def test_nome_file_prefisso_lungo_viene_accorciato():
    """Il pezzo della bottega non supera 40 caratteri."""
    nome = ArchivioAdapter.genera_nome_file(".jpg", "a" * 200)

    assert nome.split("_")[0] == "a" * 40


def test_due_salvataggi_nello_stesso_secondo_hanno_nomi_diversi(tmp_path: Path):
    """Stessa bottega, stesso secondo: il codice casuale evita i doppioni, anche su disco."""
    for archivio in (ArchivioDisco(tmp_path), ArchivioFinto()):
        nomi = {archivio.salva(JPEG_TEST, ".jpg", "Bottega Rossi") for _ in range(50)}
        assert len(nomi) == 50
        assert all(archivio.esiste(n) for n in nomi)


def test_disco_non_sovrascrive_un_nome_gia_preso(tmp_path: Path, monkeypatch):
    """Se il nome generato esiste già, ArchivioDisco ne genera un altro senza toccare il file."""
    archivio = ArchivioDisco(tmp_path)
    (tmp_path / "occupato.jpg").write_bytes(b"originale")
    nomi = iter(["occupato.jpg", "libero.jpg"])
    monkeypatch.setattr(
        ArchivioAdapter,
        "genera_nome_file",
        classmethod(lambda cls, e, p="": next(nomi)),
    )

    nome = archivio.salva(JPEG_TEST, ".jpg", "x")

    assert nome == "libero.jpg"
    assert (tmp_path / "occupato.jpg").read_bytes() == b"originale"


def test_estensioni_rifiutate_se_non_in_whitelist():
    """Estensioni non appartenenti a immagini supportate (JPG, PNG, WEBP) vengono rifiutate."""
    estensioni_vietate = [".exe", ".sh", ".php", ".py", ".bin", "tar.gz", "", None]
    for ext in estensioni_vietate:
        with pytest.raises(ValueError):
            ArchivioAdapter.genera_nome_file(ext)  # type: ignore[arg-type]


def test_valida_dimensione_payload_limite_10mb():
    """Payload vuoti o oltre il limite di 10 MB (Spec R-13) vengono bloccati (anti-DoS)."""
    # Payload vuoto
    with pytest.raises(ValueError, match="non può essere vuoto"):
        ArchivioAdapter.valida_dimensione_payload(b"")

    # Payload oltre 10 MB
    payload_eccessivo = b"x" * (DIMENSIONE_MAX_BYTE + 1)
    with pytest.raises(ValueError, match="supera il limite massimo"):
        ArchivioAdapter.valida_dimensione_payload(payload_eccessivo)

    # Tipo non binario
    with pytest.raises(TypeError):
        ArchivioAdapter.valida_dimensione_payload("stringa")  # type: ignore[arg-type]


def test_valida_magic_bytes_integrita():
    """Viene verificata la coerenza tra estensione dichiarata e magic bytes reali del file."""
    # JPEG valido
    ArchivioAdapter.valida_magic_bytes(JPEG_TEST, ".jpg")

    # PNG valido
    ArchivioAdapter.valida_magic_bytes(PNG_TEST, ".png")

    # WEBP valido
    ArchivioAdapter.valida_magic_bytes(WEBP_TEST, ".webp")

    # Script di testo mascherato da JPEG -> rifiutato
    with pytest.raises(ValueError, match="immagine JPEG valida"):
        ArchivioAdapter.valida_magic_bytes(b"<?php echo 'malware'; ?>", ".jpg")

    # Header PNG etichettato come JPEG -> rifiutato
    with pytest.raises(ValueError, match="immagine JPEG valida"):
        ArchivioAdapter.valida_magic_bytes(PNG_TEST, ".jpg")


def test_archivio_finto_salva_leggi_elimina():
    """ArchivioFinto memorizza e gestisce i file interamente in memoria senza toccare il disco."""
    archivio = ArchivioFinto()

    nome = archivio.salva(JPEG_TEST, "jpg")
    assert archivio.esiste(nome) is True
    assert archivio.leggi(nome) == JPEG_TEST
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
    nome1 = archivio.salva(PNG_TEST, "png")
    nome2 = archivio.salva(WEBP_TEST, "webp")
    assert len(archivio.file_salvati) == 2

    archivio.svuota()
    assert len(archivio.file_salvati) == 0
    assert archivio.esiste(nome1) is False
    assert archivio.esiste(nome2) is False


def test_archivio_disco_operazioni_base(tmp_path: Path):
    """ArchivioDisco opera correttamente sulla cartella configurata (tmp_path isolata)."""
    archivio = ArchivioDisco(radice=tmp_path)

    nome = archivio.salva(PNG_TEST, ".png")
    assert archivio.esiste(nome) is True

    # Verifica presenza fisica del file nella directory temporanea
    file_fisico = tmp_path / nome
    assert file_fisico.is_file()
    assert file_fisico.read_bytes() == PNG_TEST

    # Lettura tramite adattatore
    assert archivio.leggi(nome) == PNG_TEST
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


def test_archivio_disco_eliminazione_anti_toctou(tmp_path: Path):
    """Eliminazione concorrente (file rimosso esternamente prima di unlink) gestita senza crash."""
    archivio = ArchivioDisco(radice=tmp_path)
    nome = archivio.salva(PNG_TEST, ".png")

    # Rimuoviamo il file prima di chiamare elimina (simulazione race condition)
    (tmp_path / nome).unlink()

    # Non deve sollevare eccezioni non gestite, ma restituire False con grazia
    assert archivio.elimina(nome) is False


def test_archivio_disco_permission_error_propagato(tmp_path: Path, monkeypatch):
    """PermissionError (es. permessi OS o antivirus) viene propagato al monitoring."""
    archivio = ArchivioDisco(radice=tmp_path)
    nome = archivio.salva(PNG_TEST, ".png")

    def mock_unlink(*args, **kwargs):
        raise PermissionError("Accesso negato dal sistema operativo o antivirus")

    monkeypatch.setattr(Path, "unlink", mock_unlink)
    with pytest.raises(PermissionError):
        archivio.elimina(nome)


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


def test_usa_archivio_context_manager():
    """Il context manager ripristina deterministicamente l'adattatore evitando test flaky."""
    originale = ottieni_archivio()
    finto1 = ArchivioFinto()
    finto2 = ArchivioFinto()

    with usa_archivio(finto1) as attivo1:
        assert attivo1 is finto1
        assert ottieni_archivio() is finto1

        # Annidamento
        with usa_archivio(finto2) as attivo2:
            assert attivo2 is finto2
            assert ottieni_archivio() is finto2

        assert ottieni_archivio() is finto1

    assert ottieni_archivio() is originale

    # Ripristino garantito anche in caso di eccezione
    try:
        with usa_archivio(finto1):
            raise RuntimeError("Errore simulato")
    except RuntimeError:
        pass

    assert ottieni_archivio() is originale


@pytest.mark.parametrize(
    "nome_non_valido",
    ["../x.png", "a/b.png", "x.png:ads", "x*.png", "", None, 123],
)
def test_finto_e_disco_rifiutano_gli_stessi_nomi(tmp_path: Path, nome_non_valido):
    """Finto e disco hanno lo stesso identico comportamento sui nomi non validi."""
    for archivio in (ArchivioFinto(), ArchivioDisco(radice=tmp_path)):
        with pytest.raises(ValueError):
            archivio.leggi(nome_non_valido)
        with pytest.raises(ValueError):
            archivio.elimina(nome_non_valido)
        assert archivio.esiste(nome_non_valido) is False
