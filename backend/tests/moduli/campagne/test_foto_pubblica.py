"""Test per l'indirizzo pubblico della foto con firma a tempo (spec R-42, CA-81).

Verifica:
1. Calcolo e validazione crittografica della firma HMAC-SHA256 con scadenza;
2. Rifiuto (404) su firma manomessa, firma scaduta, canale non valido o foto inesistente;
3. Accessibilità pubblica senza autenticazione né cookie di sessione;
4. Restituzione dell'immagine JPEG conforme (lato corto 1080 px, rimozione EXIF/GPS);
5. Invariante costituzionale §1.3: il file originale archiviato resta inalterato;
6. Supporto all'impostazione foto_url_pubblico (FOTO_URL_PUBBLICO) per tunnel locali.
"""

from datetime import datetime, timedelta, timezone
import io
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
import pytest
from sqlalchemy.orm import Session

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.core.config import leggi_impostazioni
from app.core.errori import DatiNonValidi, NonTrovato
from app.moduli.campagne import foto_pubblica, service
from app.moduli.campagne.models import Foto
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_in_bozza,
    foto as fabbrica_foto,
    gruppo,
)


def _crea_immagine_raw(
    larghezza: int = 1500,
    altezza: int = 1500,
    colore: tuple[int, int, int] = (120, 80, 40),
) -> bytes:
    """Crea un'immagine JPEG di test con metadati fittizi."""
    img = Image.new("RGB", (larghezza, altezza), color=colore)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


# ==============================================================================
# 1. Test unitari per logica di firma (foto_pubblica.py)
# ==============================================================================


def test_calcolo_e_verifica_firma_valida():
    """Firma calcolata correttamente viene validata con successo."""
    foto_id = 42
    canale = "instagram"
    scadenza_ts = int(datetime.now(timezone.utc).timestamp()) + 3600

    firma = foto_pubblica.componi_firma(foto_id, canale, scadenza_ts)
    assert "_" in firma

    valida = foto_pubblica.verifica_firma(foto_id, canale, firma)
    assert valida is True


def test_verifica_firma_manomessa():
    """Qualsiasi alterazione della firma, del canale o dell'ID viene respinta."""
    foto_id = 10
    canale = "instagram"
    scadenza_ts = int(datetime.now(timezone.utc).timestamp()) + 3600
    firma = foto_pubblica.componi_firma(foto_id, canale, scadenza_ts)

    # 1. Firma alterata di 1 carattere nel MAC
    firma_alterata = firma[:-1] + ("0" if firma[-1] != "0" else "1")
    assert foto_pubblica.verifica_firma(foto_id, canale, firma_alterata) is False

    # 2. Foto ID differente
    assert foto_pubblica.verifica_firma(foto_id + 1, canale, firma) is False

    # 3. Canale differente
    assert foto_pubblica.verifica_firma(foto_id, "facebook", firma) is False

    # 4. Canale non supportato
    assert foto_pubblica.verifica_firma(foto_id, "tiktok", firma) is False

    # 5. ID non valido
    assert foto_pubblica.verifica_firma(0, canale, firma) is False
    assert foto_pubblica.verifica_firma(-1, canale, firma) is False

    # 6. Firma malformata
    assert foto_pubblica.verifica_firma(foto_id, canale, "senza_separatore") is False
    assert foto_pubblica.verifica_firma(foto_id, canale, "abc_123") is False
    assert foto_pubblica.verifica_firma(foto_id, canale, "") is False


def test_verifica_firma_scaduta():
    """Firma scaduta rispetto all'istante di riferimento viene respinta."""
    foto_id = 15
    canale = "instagram"
    ora_base = datetime(2030, 5, 1, 12, 0, tzinfo=timezone.utc)
    scadenza_ts = int((ora_base - timedelta(seconds=1)).timestamp())

    firma = foto_pubblica.componi_firma(foto_id, canale, scadenza_ts)

    # Scaduta rispetto a ora_base
    assert foto_pubblica.verifica_firma(foto_id, canale, firma, ora=ora_base) is False


def test_supporto_formato_esplicito_e_compatto():
    """Verifica sia il formato compatto sia il passaggio con scadenza_ts esplicito."""
    foto_id = 20
    canale = "instagram"
    ora_base = datetime(2030, 5, 1, 12, 0, tzinfo=timezone.utc)
    scadenza_ts = int((ora_base + timedelta(hours=2)).timestamp())

    mac = foto_pubblica.calcola_mac(foto_id, canale, scadenza_ts)

    # Formato esplicito: firma = solo MAC, scadenza_ts passato separatamente
    assert (
        foto_pubblica.verifica_firma(
            foto_id, canale, mac, scadenza_ts=scadenza_ts, ora=ora_base
        )
        is True
    )

    # Se scadenza_ts esplicito differisce da quello nel token compatto -> False
    token_compatto = f"{scadenza_ts}_{mac}"
    assert (
        foto_pubblica.verifica_firma(
            foto_id,
            canale,
            token_compatto,
            scadenza_ts=scadenza_ts + 10,
            ora=ora_base,
        )
        is False
    )


def test_genera_url_pubblico(monkeypatch):
    """Generazione dell'URL pubblico: relativo, con url_base e con foto_url_pubblico."""
    impostazioni = leggi_impostazioni()
    monkeypatch.setattr(impostazioni, "foto_url_pubblico", "")
    foto_id = 5
    url_relativo = foto_pubblica.genera_url_pubblico(
        foto_id, canale="instagram", durata_secondi=3600
    )
    assert url_relativo.startswith("/api/foto/5/pubblica?canale=instagram&firma=")

    # Con url_base esplicito
    url_assoluto = foto_pubblica.genera_url_pubblico(
        foto_id,
        canale="instagram",
        durata_secondi=3600,
        url_base="https://adflow.bottega.it",
    )
    assert url_assoluto.startswith(
        "https://adflow.bottega.it/api/foto/5/pubblica?canale=instagram&firma="
    )

    # Con foto_url_pubblico nelle impostazioni (FOTO_URL_PUBBLICO di .env)
    monkeypatch.setattr(
        impostazioni, "foto_url_pubblico", "https://adflow.ngrok-free.app/"
    )
    url_cfg = foto_pubblica.genera_url_pubblico(foto_id, canale="instagram")
    assert url_cfg.startswith(
        "https://adflow.ngrok-free.app/api/foto/5/pubblica?canale=instagram&firma="
    )

    # Canale o ID non validi sollevano DatiNonValidi
    with pytest.raises(DatiNonValidi):
        foto_pubblica.genera_url_pubblico(-1)

    with pytest.raises(DatiNonValidi):
        foto_pubblica.genera_url_pubblico(foto_id, canale="canale_inesistente")


# ==============================================================================
# 2. Test per service.url_foto_pubblica
# ==============================================================================


def test_service_url_foto_pubblica(db: Session):
    """Il servizio verifica l'esistenza della foto prima di generare l'URL."""
    prof = profilo(db)
    camp = campagna_in_bozza(db, profilo_id=prof.id)
    grp = gruppo(db, camp)
    foto_db = fabbrica_foto(db, gruppo=grp)

    url = service.url_foto_pubblica(db, foto_db.id, canale="instagram")
    assert f"/api/foto/{foto_db.id}/pubblica?canale=instagram&firma=" in url

    # Foto inesistente solleva NonTrovato
    with pytest.raises(NonTrovato):
        service.url_foto_pubblica(db, foto_id=999999, canale="instagram")


# ==============================================================================
# 3. Test API endpoint GET /api/foto/{id}/pubblica
# ==============================================================================


def test_api_download_foto_pubblica_anonimo_successo(
    client: TestClient, db: Session, tmp_path: Path
):
    """Download pubblico riuscito senza cookie né sessione, con immagine elaborata."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        prof = profilo(db)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        grp = gruppo(db, camp)

        dati_originali = _crea_immagine_raw(1600, 1200)
        nome_file = archivio.salva(dati_originali, "jpg")
        foto_db = fabbrica_foto(db, gruppo=grp, file=nome_file)

        # Genera URL pubblico tramite service
        url_pubblico = service.url_foto_pubblica(db, foto_db.id, canale="instagram")

        # Richiesta anonima al client (senza header o sessione di autenticazione)
        res = client.get(url_pubblico)

        assert res.status_code == 200
        assert res.headers["content-type"] == "image/jpeg"
        assert res.headers["x-content-type-options"] == "nosniff"
        assert "public" in res.headers.get("cache-control", "")

        # Verifica che l'immagine restituita sia un JPEG valido conforme a spec R-42
        img = Image.open(io.BytesIO(res.content))
        assert img.format == "JPEG"
        # Il lato corto deve essere esattamente 1080 px
        assert min(img.width, img.height) == 1080

        # Invariante §1.3: il file originale salvato in archivio è rimasto inalterato
        assert archivio.leggi(nome_file) == dati_originali


def test_api_download_foto_pubblica_firma_alterata_restituisce_404(
    client: TestClient, db: Session, tmp_path: Path
):
    """Se la firma è alterata, risponde 404 senza dettagli interni."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        prof = profilo(db)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        grp = gruppo(db, camp)
        nome_file = archivio.salva(_crea_immagine_raw(1080, 1080), "jpg")
        foto_db = fabbrica_foto(db, gruppo=grp, file=nome_file)

        url = service.url_foto_pubblica(db, foto_db.id, canale="instagram")
        url_alterato = url[:-2] + "99"

        res = client.get(url_alterato)
        assert res.status_code == 404
        assert res.json() == {"detail": "Foto non trovata."}


def test_api_download_foto_pubblica_firma_scaduta_restituisce_404(
    client: TestClient, db: Session, tmp_path: Path
):
    """Se la firma a tempo è scaduta, risponde 404."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        prof = profilo(db)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        grp = gruppo(db, camp)
        nome_file = archivio.salva(_crea_immagine_raw(1080, 1080), "jpg")
        foto_db = fabbrica_foto(db, gruppo=grp, file=nome_file)

        # Firma scaduta nel passato (durata negativa o scadenza nel passato)
        scadenza_passata = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
        firma_passata = foto_pubblica.componi_firma(
            foto_db.id, "instagram", scadenza_passata
        )

        res = client.get(
            f"/api/foto/{foto_db.id}/pubblica?canale=instagram&firma={firma_passata}"
        )
        assert res.status_code == 404
        assert res.json() == {"detail": "Foto non trovata."}


def test_api_download_foto_pubblica_inesistente_restituisce_404(
    client: TestClient, db: Session
):
    """Se la foto non esiste a database ma la firma è sintatticamente valida, risponde 404."""
    scadenza_futura = int(datetime.now(timezone.utc).timestamp()) + 3600
    firma = foto_pubblica.componi_firma(999999, "instagram", scadenza_futura)

    res = client.get(f"/api/foto/999999/pubblica?canale=instagram&firma={firma}")
    assert res.status_code == 404
    assert res.json() == {"detail": "Foto non trovata."}


def test_api_download_foto_pubblica_senza_parametri_restituisce_404(
    client: TestClient, db: Session
):
    """Richieste prive di canale o firma ricevono 404 difensivo (anti-probe)."""
    res = client.get("/api/foto/1/pubblica")
    assert res.status_code == 404
    assert res.json() == {"detail": "Foto non trovata."}

    res_senza_firma = client.get("/api/foto/1/pubblica?canale=instagram")
    assert res_senza_firma.status_code == 404

    res_canale_non_valido = client.get(
        "/api/foto/1/pubblica?canale=sconosciuto&firma=abc"
    )
    assert res_canale_non_valido.status_code == 404


def test_api_download_con_parametro_scadenza_esplicito(
    client: TestClient, db: Session, tmp_path: Path
):
    """Download pubblico funzionante anche con query param 'scadenza' separato."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        prof = profilo(db)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        grp = gruppo(db, camp)
        nome_file = archivio.salva(_crea_immagine_raw(1080, 1080), "jpg")
        foto_db = fabbrica_foto(db, gruppo=grp, file=nome_file)

        scadenza_ts = int(datetime.now(timezone.utc).timestamp()) + 3600
        mac = foto_pubblica.calcola_mac(foto_db.id, "instagram", scadenza_ts)

        res = client.get(
            f"/api/foto/{foto_db.id}/pubblica?canale=instagram&scadenza={scadenza_ts}&firma={mac}"
        )
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/jpeg"


def test_api_download_con_scadenza_stringa_non_valida_restituisce_404(
    client: TestClient, db: Session
):
    """Parametro query 'scadenza' non numerico risponde 404 difensivo (anti-probe, non 422)."""
    res = client.get(
        "/api/foto/1/pubblica?canale=instagram&scadenza=non_un_numero&firma=abc"
    )
    assert res.status_code == 404
    assert res.json() == {"detail": "Foto non trovata."}


def test_api_download_con_id_zero_o_negativo_restituisce_404(
    client: TestClient, db: Session
):
    """ID foto zero o negativo risponde 404 senza consultare il database."""
    res_zero = client.get("/api/foto/0/pubblica?canale=instagram&firma=123_abc")
    assert res_zero.status_code == 404
    assert res_zero.json() == {"detail": "Foto non trovata."}

    res_neg = client.get("/api/foto/-5/pubblica?canale=instagram&firma=123_abc")
    assert res_neg.status_code == 404
    assert res_neg.json() == {"detail": "Foto non trovata."}


def test_api_download_canale_case_insensitive_e_spazi(
    client: TestClient, db: Session, tmp_path: Path
):
    """Il canale accetta maiuscole e spazi iniziali/finali purché valido."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        prof = profilo(db)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        grp = gruppo(db, camp)
        nome_file = archivio.salva(_crea_immagine_raw(1080, 1080), "jpg")
        foto_db = fabbrica_foto(db, gruppo=grp, file=nome_file)

        url = service.url_foto_pubblica(db, foto_db.id, canale="instagram")
        # Sostituisce 'instagram' con 'INSTAGRAM' nella query string
        url_maiuscolo = url.replace("canale=instagram", "canale=INSTAGRAM")

        res = client.get(url_maiuscolo)
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/jpeg"


def test_api_download_canale_facebook(client: TestClient, db: Session, tmp_path: Path):
    """L'endpoint funziona correttamente anche per il canale 'facebook'."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        prof = profilo(db)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        grp = gruppo(db, camp)
        nome_file = archivio.salva(_crea_immagine_raw(1200, 1200), "jpg")
        foto_db = fabbrica_foto(db, gruppo=grp, file=nome_file)

        url = service.url_foto_pubblica(db, foto_db.id, canale="facebook")
        res = client.get(url)

        assert res.status_code == 200
        assert res.headers["content-type"] == "image/jpeg"
        img = Image.open(io.BytesIO(res.content))
        assert min(img.width, img.height) == 1080


def test_api_download_foto_png_con_trasparenza_convertita_a_jpeg(
    client: TestClient, db: Session, tmp_path: Path
):
    """File originale PNG con canale Alpha viene convertito ed esportato come JPEG conforme."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        prof = profilo(db)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        grp = gruppo(db, camp)

        # Crea un'immagine PNG RGBA con trasparenza
        img_rgba = Image.new("RGBA", (1400, 1400), color=(100, 150, 200, 128))
        buf = io.BytesIO()
        img_rgba.save(buf, format="PNG")
        nome_file = archivio.salva(buf.getvalue(), "png")
        foto_db = fabbrica_foto(db, gruppo=grp, file=nome_file, mime="image/png")

        url = service.url_foto_pubblica(db, foto_db.id, canale="instagram")
        res = client.get(url)

        assert res.status_code == 200
        assert res.headers["content-type"] == "image/jpeg"
        img_res = Image.open(io.BytesIO(res.content))
        assert img_res.format == "JPEG"
        assert min(img_res.width, img_res.height) == 1080


def test_api_download_foto_con_metadati_gps_rimossi(
    client: TestClient, db: Session, tmp_path: Path
):
    """I metadati GPS presenti nell'originale vengono rimossi dall'immagine servita (spec R-42)."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        prof = profilo(db)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        grp = gruppo(db, camp)

        # Crea immagine JPEG con EXIF GPS
        img = Image.new("RGB", (1200, 1200), color=(50, 100, 150))
        exif = img.getexif()
        gps_ifd = exif.get_ifd(0x8825)
        gps_ifd[1] = "N"
        gps_ifd[2] = (41, 53, 30)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", exif=exif)
        nome_file = archivio.salva(buf.getvalue(), "jpg")
        foto_db = fabbrica_foto(db, gruppo=grp, file=nome_file)

        url = service.url_foto_pubblica(db, foto_db.id, canale="instagram")
        res = client.get(url)

        assert res.status_code == 200
        img_res = Image.open(io.BytesIO(res.content))
        exif_res = img_res.getexif()
        gps_res = exif_res.get_ifd(0x8825)
        # Il tag IFD GPS deve essere completamente assente o vuoto
        assert len(gps_res) == 0


def test_api_download_foto_con_file_su_disco_mancante(
    client: TestClient, db: Session, tmp_path: Path
):
    """Se il file fisico non esiste su disco, l'endpoint risponde 404 senza errori 500."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        prof = profilo(db)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        grp = gruppo(db, camp)
        # Record Foto registrato a DB con file non presente in ArchivioDisco
        foto_db = fabbrica_foto(db, gruppo=grp, file="file_inesistente_su_disco.jpg")

        url = service.url_foto_pubblica(db, foto_db.id, canale="instagram")
        res = client.get(url)

        assert res.status_code == 404
        assert res.json() == {"detail": "Foto non trovata."}


def test_api_download_foto_con_file_corrotto_su_disco(
    client: TestClient, db: Session, tmp_path: Path
):
    """Se il file archiviato è corrotto (non decodificabile), risponde 404 difensivo."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        prof = profilo(db)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        grp = gruppo(db, camp)
        # Salva un file valido ma poi corrompilo su disco
        nome_file = archivio.salva(_crea_immagine_raw(1080, 1080), "jpg")
        percorso_file = tmp_path / nome_file
        # Sovrascrive con byte corrotti non validi per Pillow
        percorso_file.write_bytes(b"\xff\xd8\xffcorrotto-non-immagine-valida" * 10)

        foto_db = fabbrica_foto(db, gruppo=grp, file=nome_file)

        url = service.url_foto_pubblica(db, foto_db.id, canale="instagram")
        res = client.get(url)

        assert res.status_code == 404
        assert res.json() == {"detail": "Foto non trovata."}
