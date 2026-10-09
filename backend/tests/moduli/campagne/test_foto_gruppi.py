"""Test per il caricamento, gestione gruppi ed eliminazione delle foto (T1-23).

Verifica:
- CA-13, R-13: rifiuto non immagini, file > 10 MB, lato corto < 1080 px -> 422;
  accettazione PNG, JPEG e WebP conformi -> 201;
- Protezione DoS: MAX_WIDTH/MAX_HEIGHT (8192 px) e MAX_PIXELS (36 MPixel) -> 422;
- CA-04: tentativo di caricare/eliminare foto o gruppi altrui -> 404 (anti-disclosure);
- Transizioni: upload, modifica ed eliminazione permesse solo in bozza -> 409;
- Gestione gruppi: creazione, accodamento, propagazione ed ereditarietà descrizione;
- Eliminazione atomica: cancellazione DB e pulizia disco (anti-file orfani);
- Download file: autorizzazione per proprietario e operatore;
- Compensazione anti-TOCTOU: se il database fallisce, il file su disco viene rimosso.
"""

from io import BytesIO
from pathlib import Path
import struct
from unittest.mock import patch
from uuid import UUID, uuid4
import zlib

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.moduli.campagne.models import Foto, GruppoFoto
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_in_bozza,
    campagna_inviata,
    foto as fabbrica_foto,
    gruppo as fabbrica_gruppo,
)


def _gruppo_caricate(db: Session, campagna) -> int:
    """Id di un gruppo `caricate` della campagna: il caricamento lo richiede (plan §3).

    Riusa il primo gruppo `caricate` della campagna, se c'è; altrimenti lo crea.
    """
    esistente = db.scalar(
        select(GruppoFoto.id)
        .where(GruppoFoto.campagna_id == campagna.id, GruppoFoto.origine == "caricate")
        .order_by(GruppoFoto.id)
    )
    if esistente is not None:
        return esistente
    return fabbrica_gruppo(db, campagna).id


def _crea_png(larghezza: int, altezza: int) -> bytes:
    """Genera un PNG binario minimale e valido con dimensioni arbitrarie."""
    header = b"\x89PNG\r\n\x1a\n"
    ihdr_dati = struct.pack(">IIBBBBB", larghezza, altezza, 8, 2, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_dati) & 0xFFFFFFFF)
    ihdr = struct.pack(">I", len(ihdr_dati)) + b"IHDR" + ihdr_dati + ihdr_crc
    iend = b"\x00\x00\x00\x00IEND\xaeB`\x82"
    return header + ihdr + iend


def _crea_jpeg(larghezza: int, altezza: int) -> bytes:
    """Genera un JPEG binario minimale e valido con marker SOF0."""
    soi = b"\xff\xd8"
    app0_dati = b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    app0 = b"\xff\xe0" + struct.pack(">H", len(app0_dati) + 2) + app0_dati
    sof_payload = (
        b"\x08"
        + struct.pack(">HH", altezza, larghezza)
        + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
    )
    sof0 = b"\xff\xc0" + struct.pack(">H", len(sof_payload) + 2) + sof_payload
    eoi = b"\xff\xd9"
    return soi + app0 + sof0 + eoi


def _crea_webp(larghezza: int, altezza: int) -> bytes:
    """Genera un WebP binario con chunk VP8X valido."""
    chunk_dati = (
        b"\x00\x00\x00\x00"
        + (larghezza - 1).to_bytes(3, "little")
        + (altezza - 1).to_bytes(3, "little")
    )
    riff_payload = b"WEBPVP8X" + struct.pack("<I", len(chunk_dati)) + chunk_dati
    header = b"RIFF" + struct.pack("<I", len(riff_payload)) + riff_payload
    return header


# ==============================================================================
# CA-13: Validazione tipo reale, peso e dimensioni
# ==============================================================================


def test_ca13_rifiuto_file_non_immagine(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-13: Caricamento di un file non immagine (es. file di testo) solleva 422."""
    artigiano = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=artigiano.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    file_finto = (
        "documento.txt",
        BytesIO(b"Questo e' solo un file di testo"),
        "text/plain",
    )
    risposta = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": file_finto},
    )

    assert risposta.status_code == 422
    assert "Il file non è un'immagine valida o supportata" in risposta.json()["detail"]


def test_ca13_rifiuto_payload_oltre_10mb(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-13: Caricamento di un file superiore a 10 MB solleva 422."""
    artigiano = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=artigiano.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    # 10 MB + 1024 byte
    payload_enorme = b"X" * (10 * 1024 * 1024 + 1024)
    file_grande = ("troppo_grande.jpg", BytesIO(payload_enorme), "image/jpeg")

    risposta = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": file_grande},
    )

    assert risposta.status_code == 422
    assert "supera il limite massimo di 10 MB" in risposta.json()["detail"]


def test_ca13_rifiuto_lato_corto_inferiore_1080px(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-13: Immagine con lato corto < 1080 px solleva 422 con motivo descrittivo."""
    artigiano = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=artigiano.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    # Larghezza 1000 px, altezza 1500 px -> min = 1000 < 1080
    png_piccolo = _crea_png(1000, 1500)
    risposta = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("piccola.png", BytesIO(png_piccolo), "image/png")},
    )

    assert risposta.status_code == 422
    dettaglio = risposta.json()["detail"]
    assert "1000 px" in dettaglio
    assert "inferiore al minimo richiesto di 1080 px" in dettaglio


def test_ca13_accettazione_png_jpeg_webp_conformi(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """CA-13: Caricamento di PNG, JPEG e WebP con lato corto >= 1080 px accettati con 201."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        artigiano = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=artigiano.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        # 1. Test PNG (1080x1080)
        png_bytes = _crea_png(1080, 1080)
        res_png = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("quadrata.png", BytesIO(png_bytes), "image/png")},
        )
        assert res_png.status_code == 201
        dati_png = res_png.json()
        assert dati_png["larghezza"] == 1080
        assert dati_png["altezza"] == 1080
        assert dati_png["mime"] == "image/png"
        assert dati_png["file"].endswith(".png")
        assert (tmp_path / dati_png["file"]).is_file()

        # 2. Test JPEG (1920x1080)
        jpg_bytes = _crea_jpeg(1920, 1080)
        res_jpg = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("orizzontale.jpg", BytesIO(jpg_bytes), "image/jpeg")},
        )
        assert res_jpg.status_code == 201
        dati_jpg = res_jpg.json()
        assert dati_jpg["larghezza"] == 1920
        assert dati_jpg["altezza"] == 1080
        assert dati_jpg["mime"] == "image/jpeg"
        assert dati_jpg["file"].endswith(".jpg")
        assert (tmp_path / dati_jpg["file"]).is_file()

        # 3. Test WebP (1200x1600)
        webp_bytes = _crea_webp(1200, 1600)
        res_webp = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("verticale.webp", BytesIO(webp_bytes), "image/webp")},
        )
        assert res_webp.status_code == 201
        dati_webp = res_webp.json()
        assert dati_webp["larghezza"] == 1200
        assert dati_webp["altezza"] == 1600
        assert dati_webp["mime"] == "image/webp"
        assert dati_webp["file"].endswith(".webp")
        assert (tmp_path / dati_webp["file"]).is_file()


# ==============================================================================
# Limiti di sicurezza Defense in Depth (MAX_WIDTH, MAX_HEIGHT, MAX_PIXELS)
# ==============================================================================


def test_sicurezza_rifiuto_dimensioni_eccessive(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che immagini con dimensioni superiori a 8192 px vengano rifiutate con 422."""
    artigiano = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=artigiano.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    # Larghezza 9000 px > 8192 max
    png_sproporzionato = _crea_png(9000, 1200)
    risposta = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("enorme.png", BytesIO(png_sproporzionato), "image/png")},
    )

    assert risposta.status_code == 422
    assert (
        "superano il limite massimo consentito di 8192x8192 px"
        in risposta.json()["detail"]
    )


def test_sicurezza_rifiuto_decompression_bomb_max_pixels(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che immagini oltre 36 Megapixel totali vengano rifiutate con 422."""
    artigiano = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=artigiano.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    # 7000 x 6000 = 42.000.000 pixel > 36.000.000 max
    png_bomb = _crea_png(7000, 6000)
    risposta = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("bomb.png", BytesIO(png_bomb), "image/png")},
    )

    assert risposta.status_code == 422
    assert "supera il limite massimo di densità consentito" in risposta.json()["detail"]


# ==============================================================================
# CA-04 & Autorizzazioni
# ==============================================================================


def test_ca04_upload_su_campagna_altrui_da_404(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-04: L'artigiano che tenta di caricare foto su campagna altrui riceve 404."""
    art_a = utente_di_prova("artigiano")
    prof_a = profilo(db, utente_id=art_a.id)
    camp_a = campagna_in_bozza(db, profilo_id=prof_a.id)

    art_b = utente_di_prova("artigiano")
    profilo(db, utente_id=art_b.id)

    png_valido = _crea_png(1080, 1080)
    risposta = client.post(
        f"/api/campagne/{camp_a.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp_a)},
        files={"file": ("foto.png", BytesIO(png_valido), "image/png")},
    )

    assert risposta.status_code == 404
    assert risposta.json()["detail"] == "Campagna non trovata."


def test_upload_richiede_ruolo_artigiano(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che operatori e ruoli diversi da artigiano ricevano 403 all'upload."""
    operatore = utente_di_prova("operatore")
    camp = campagna_in_bozza(db)

    png_valido = _crea_png(1080, 1080)
    risposta = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("foto.png", BytesIO(png_valido), "image/png")},
    )

    assert risposta.status_code == 403


# ==============================================================================
# Vincolo stato bozza (409 per stati non ammessi)
# ==============================================================================


def test_upload_su_campagna_non_in_bozza_da_409(
    client: TestClient, utente_di_prova, db: Session
):
    """Tentativo di caricare foto su una campagna già 'inviata' restituisce 409."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_inviata(db, profilo_id=prof.id)

    png_valido = _crea_png(1080, 1080)
    risposta = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("foto.png", BytesIO(png_valido), "image/png")},
    )

    assert risposta.status_code == 409
    assert "solo per campagne in bozza" in risposta.json()["detail"]


# ==============================================================================
# Gestione gruppi, accodamento ed ereditarietà descrizione
# ==============================================================================


def test_gestione_gruppi_e_descrizione(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Verifica creazione gruppo, aggiornamento descrizione e propagazione."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        # 1. Carica la prima foto in un gruppo 'caricate' già creato (id intero)
        png_1 = _crea_png(1080, 1080)
        res_1 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto1.png", BytesIO(png_1), "image/png")},
        )
        assert res_1.status_code == 201
        gruppo_id = res_1.json()["gruppo_id"]
        foto1_id = res_1.json()["id"]
        assert isinstance(gruppo_id, int)

        # 2. Aggiorna descrizione gruppo via PUT
        res_put = client.put(
            f"/api/campagne/{camp.id}/gruppi/{gruppo_id}",
            json={"descrizione": "Ceramiche decorate a mano con smalti blu"},
        )
        assert res_put.status_code == 200
        assert (
            res_put.json()["descrizione"] == "Ceramiche decorate a mano con smalti blu"
        )

        # Verifica che il gruppo a DB abbia la descrizione aggiornata
        db.expire_all()
        from app.moduli.campagne.models import GruppoFoto

        gruppo_db = db.get(GruppoFoto, gruppo_id)
        assert gruppo_db.descrizione == "Ceramiche decorate a mano con smalti blu"

        # 3. Carica seconda foto specificando lo stesso gruppo_id
        jpg_2 = _crea_jpeg(1200, 1200)
        res_2 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": gruppo_id},
            files={"file": ("foto2.jpg", BytesIO(jpg_2), "image/jpeg")},
        )
        assert res_2.status_code == 201
        assert res_2.json()["gruppo_id"] == gruppo_id


def test_aggiornamento_descrizione_gruppo_campagna_non_in_bozza_da_409(
    client: TestClient, utente_di_prova, db: Session
):
    """PUT descrizione gruppo su campagna non in bozza solleva 409."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_inviata(db, profilo_id=prof.id)
    foto_inv = fabbrica_foto(db, campagna=camp)

    risposta = client.put(
        f"/api/campagne/{camp.id}/gruppi/{foto_inv.gruppo_id}",
        json={"descrizione": "Nuova descrizione"},
    )
    assert risposta.status_code == 409


def test_aggiornamento_descrizione_gruppo_inesistente_da_404(
    client: TestClient, utente_di_prova, db: Session
):
    """PUT descrizione con gruppo_id inesistente solleva 404."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    risposta = client.put(
        f"/api/campagne/{camp.id}/gruppi/99999",
        json={"descrizione": "Nuova descrizione"},
    )
    assert risposta.status_code == 404
    assert "Gruppo non trovato nella campagna" in risposta.json()["detail"]


# ==============================================================================
# Eliminazione singola foto (DELETE /foto/{id})
# ==============================================================================


def test_eliminazione_foto_singola(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Eliminazione singola foto rimuove il record a database e cancella il file da disco."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        png = _crea_png(1080, 1080)
        res = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto.png", BytesIO(png), "image/png")},
        )
        assert res.status_code == 201
        foto_id = res.json()["id"]
        nome_file = res.json()["file"]
        percorso_file = tmp_path / nome_file

        assert percorso_file.is_file()
        assert db.get(Foto, foto_id) is not None

        # Esegue DELETE
        res_del = client.delete(f"/api/foto/{foto_id}")
        assert res_del.status_code == 204

        # Prima del commit il file deve esistere ancora (nulla è definitivo)
        assert percorso_file.is_file()

        # Commit di fine richiesta: solo ora il file viene rimosso
        db.commit()
        assert db.get(Foto, foto_id) is None
        assert not percorso_file.exists()


def test_eliminazione_foto_campagna_non_in_bozza_da_409(
    client: TestClient, utente_di_prova, db: Session
):
    """Tentativo di eliminare foto da campagna inviata solleva 409."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_inviata(db, profilo_id=prof.id)
    f = fabbrica_foto(db, campagna=camp)

    res = client.delete(f"/api/foto/{f.id}")
    assert res.status_code == 409
    assert "solo per campagne in bozza" in res.json()["detail"]


def test_ca04_eliminazione_foto_altrui_da_404(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-04: Eliminare una foto di un altro artigiano restituisce 404."""
    art_a = utente_di_prova("artigiano")
    prof_a = profilo(db, utente_id=art_a.id)
    camp_a = campagna_in_bozza(db, profilo_id=prof_a.id)
    foto_a = fabbrica_foto(db, campagna=camp_a)

    art_b = utente_di_prova("artigiano")
    profilo(db, utente_id=art_b.id)

    res = client.delete(f"/api/foto/{foto_a.id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Foto non trovata."


# ==============================================================================
# Eliminazione intero gruppo (DELETE /campagne/{id}/gruppi/{gruppo_id})
# ==============================================================================


def test_eliminazione_gruppo_completo(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Eliminazione gruppo rimuove tutte le foto associate sia da DB che da disco."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        # Foto 1
        res_1 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto1.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        gruppo_id = res_1.json()["gruppo_id"]
        foto1_id = res_1.json()["id"]
        file1 = tmp_path / res_1.json()["file"]

        # Foto 2 (stesso gruppo)
        res_2 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": gruppo_id},
            files={
                "file": (
                    "foto2.jpg",
                    BytesIO(_crea_jpeg(1080, 1080)),
                    "image/jpeg",
                )
            },
        )
        foto2_id = res_2.json()["id"]
        file2 = tmp_path / res_2.json()["file"]

        assert file1.is_file() and file2.is_file()

        # Elimina intero gruppo
        res_del = client.delete(f"/api/campagne/{camp.id}/gruppi/{gruppo_id}")
        assert res_del.status_code == 204

        # Prima del commit i file esistono ancora
        assert file1.is_file() and file2.is_file()

        # Dopo il commit entrambe le foto sono sparite da DB e disco
        db.commit()
        assert db.get(Foto, foto1_id) is None
        assert db.get(Foto, foto2_id) is None
        assert not file1.exists()
        assert not file2.exists()


# ==============================================================================
# Download file foto (GET /foto/{id}/file)
# ==============================================================================


def test_download_file_foto(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Verifica download del file da proprietario e operatore, e blocco per estranei."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art_a = utente_di_prova("artigiano")
        prof_a = profilo(db, utente_id=art_a.id)
        camp_a = campagna_in_bozza(db, profilo_id=prof_a.id)

        png_bytes = _crea_png(1080, 1080)
        res_up = client.post(
            f"/api/campagne/{camp_a.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp_a)},
            files={"file": ("originale.png", BytesIO(png_bytes), "image/png")},
        )
        foto_id = res_up.json()["id"]

        # 1. Proprietario scarica con successo
        res_down_proprietario = client.get(f"/api/foto/{foto_id}/file")
        assert res_down_proprietario.status_code == 200
        assert res_down_proprietario.content == png_bytes
        assert res_down_proprietario.headers["content-type"] == "image/png"

        # 2. Operatore scarica con successo
        utente_di_prova("operatore")
        res_down_operatore = client.get(f"/api/foto/{foto_id}/file")
        assert res_down_operatore.status_code == 200
        assert res_down_operatore.content == png_bytes

        # 3. Artigiano B estraneo riceve 404 (CA-04)
        art_b = utente_di_prova("artigiano")
        profilo(db, utente_id=art_b.id)
        res_down_estraneo = client.get(f"/api/foto/{foto_id}/file")
        assert res_down_estraneo.status_code == 404


# ==============================================================================
# Compensazione Transazionale (Anti-TOCTOU)
# ==============================================================================


def test_compensazione_rollback_disco_se_db_fallisce(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Se il database fallisce durante la registrazione della foto, il file fisico viene ripulito."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        png_bytes = _crea_png(1080, 1080)

        # Simuliamo un errore inaspettato durante il db.flush() per testare la compensazione
        with patch.object(
            db, "flush", side_effect=RuntimeError("Simulazione errore DB")
        ):
            try:
                client.post(
                    f"/api/campagne/{camp.id}/foto",
                    data={"gruppo_id": _gruppo_caricate(db, camp)},
                    files={
                        "file": (
                            "test_crash.png",
                            BytesIO(png_bytes),
                            "image/png",
                        )
                    },
                )
            except RuntimeError:
                pass

        # Verifichiamo che la cartella dell'archivio non contenga file orfani
        file_rimasti = list(tmp_path.iterdir())
        assert file_rimasti == [], f"Trovati file orfani non compensati: {file_rimasti}"


# ==============================================================================
# Sezione Debug Avanzato, Stress Test e Casi Limite
# ==============================================================================


def test_debug_jpeg_malformato_marker_inatteso(
    client: TestClient, utente_di_prova, db: Session
):
    """Debug: Stream JPEG con byte non-0xFF dopo SOI viene respinto con 422."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    app0_dati = b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    app0 = b"\xff\xe0" + struct.pack(">H", len(app0_dati) + 2) + app0_dati
    # Dopo APP0 invece di 0xFF c'è 0x42 (marker inatteso)
    jpeg_corrotto = b"\xff\xd8" + app0 + b"\x42\x43\x44\x45"
    res = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("corrotto.jpg", BytesIO(jpeg_corrotto), "image/jpeg")},
    )
    assert res.status_code == 422
    assert "File JPEG non valido o corrotto: marker inatteso" in res.json()["detail"]


def test_debug_jpeg_malformato_senza_sof(
    client: TestClient, utente_di_prova, db: Session
):
    """Debug: Stream JPEG valido fino ad APP0 ma privo di Start of Frame solleva 422."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    soi = b"\xff\xd8"
    app0_dati = b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    app0 = b"\xff\xe0" + struct.pack(">H", len(app0_dati) + 2) + app0_dati
    eoi = b"\xff\xd9"
    jpeg_senza_sof = soi + app0 + eoi

    res = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("senza_sof.jpg", BytesIO(jpeg_senza_sof), "image/jpeg")},
    )
    assert res.status_code == 422
    assert "Impossibile estrarre le dimensioni" in res.json()["detail"]


def test_debug_png_troncato_o_senza_ihdr(
    client: TestClient, utente_di_prova, db: Session
):
    """Debug: Stream PNG privo di chunk IHDR iniziale solleva 422."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    # Magic bytes PNG seguiti da un chunk non-IHDR (es. sBIT)
    png_errato = (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 4)
        + b"sBIT"
        + b"\x08\x08\x08\x08"
        + b"\x00\x00\x00\x00"
    )

    res = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("senza_ihdr.png", BytesIO(png_errato), "image/png")},
    )
    assert res.status_code == 422
    assert "Intestazione IHDR non trovata" in res.json()["detail"]


def test_debug_webp_chunk_sconosciuto(client: TestClient, utente_di_prova, db: Session):
    """Debug: Stream WebP con sottoformato non supportato solleva 422."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    webp_sconosciuto = b"RIFF\x14\x00\x00\x00WEBPVP8Z\x08\x00\x00\x0012345678"
    res = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("sconosciuto.webp", BytesIO(webp_sconosciuto), "image/webp")},
    )
    assert res.status_code == 422
    assert "Formato WEBP non supportato" in res.json()["detail"]


def test_debug_confini_esatti_1080_e_1079(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Debug: Confini esatti al pixel per lato minimo, massimo e pixel totali."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        # 1. 1080x1080 esatto -> OK (201)
        res_1080 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("1080.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res_1080.status_code == 201

        # 2. 1079x1080 (1 px sotto minimo) -> Rifiutato (422)
        res_1079 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("1079.png", BytesIO(_crea_png(1079, 1080)), "image/png")},
        )
        assert res_1079.status_code == 422

        # 3. 8192x1080 esatto -> OK (201)
        res_8192 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("8192.png", BytesIO(_crea_png(8192, 1080)), "image/png")},
        )
        assert res_8192.status_code == 201

        # 4. 8193x1080 (1 px sopra massimo) -> Rifiutato (422)
        res_8193 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("8193.png", BytesIO(_crea_png(8193, 1080)), "image/png")},
        )
        assert res_8193.status_code == 422

        # 5. 6000x6000 (esattamente 36.000.000 px) -> OK (201)
        res_36m = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("36m.png", BytesIO(_crea_png(6000, 6000)), "image/png")},
        )
        assert res_36m.status_code == 201

        # 6. 6001x6000 (36.006.000 px > 36M) -> Rifiutato (422)
        res_36m_plus = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={
                "file": ("36m_plus.png", BytesIO(_crea_png(6001, 6000)), "image/png")
            },
        )
        assert res_36m_plus.status_code == 422


def test_debug_gruppo_di_altra_campagna_vietato(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Debug: Vietato associare una foto a un gruppo appartenente ad un'altra campagna."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp_a = campagna_in_bozza(db, profilo_id=prof.id, titolo="Campagna A")

        # Carica foto su Campagna A (crea gruppo A)
        res_a = client.post(
            f"/api/campagne/{camp_a.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp_a)},
            files={"file": ("foto_a.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res_a.status_code == 201
        gruppo_a = res_a.json()["gruppo_id"]

        # Chiude Campagna A portandola in inviata per poter creare la Campagna B
        from app.moduli.campagne import service as camp_service

        camp_service.cambia_stato(db, camp_a, "inviata")

        # Crea Campagna B
        camp_b = campagna_in_bozza(db, profilo_id=prof.id, titolo="Campagna B")

        # Tenta di caricare foto su Campagna B riutilizzando gruppo_a -> 422
        res_b = client.post(
            f"/api/campagne/{camp_b.id}/foto",
            data={"gruppo_id": gruppo_a},
            files={"file": ("foto_b.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res_b.status_code == 422
        assert "appartiene a un'altra campagna" in res_b.json()["detail"]


def test_debug_descrizione_gruppo_caratteri_non_validi(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Debug: Aggiornamento descrizione con spazi vuoti o byte NUL solleva 422."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        res_foto = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        gruppo_id = res_foto.json()["gruppo_id"]

        # 1. Solo spazi bianchi -> 422
        res_spazi = client.put(
            f"/api/campagne/{camp.id}/gruppi/{gruppo_id}",
            json={"descrizione": "     "},
        )
        assert res_spazi.status_code == 422

        # 2. Byte NUL -> 422
        res_nul = client.put(
            f"/api/campagne/{camp.id}/gruppi/{gruppo_id}",
            json={"descrizione": "Descrizione\x00con NUL"},
        )
        assert res_nul.status_code == 422


def test_debug_download_file_non_trovato_su_disco_da_404(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Debug: Se il file fisico viene accidentalmente cancellato da disco, il download restituisce 404."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        res = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        foto_id = res.json()["id"]
        nome_file = res.json()["file"]

        # Rimuoviamo il file fisico da disco per simulare danno accidentale
        (tmp_path / nome_file).unlink()

        # Download deve restituire 404
        res_down = client.get(f"/api/foto/{foto_id}/file")
        assert res_down.status_code == 404
        assert "non trovato nell'archivio" in res_down.json()["detail"]


def test_debug_upload_multipli_nello_stesso_gruppo(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Debug: Caricamento sequenziale di 5 immagini nello stesso gruppo mantiene coerenza."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        # Prima foto: crea gruppo
        res1 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto1.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        gruppo_id = res1.json()["gruppo_id"]

        # Imposta descrizione
        client.put(
            f"/api/campagne/{camp.id}/gruppi/{gruppo_id}",
            json={"descrizione": "Set completo sculture in legno"},
        )

        # Carica altre 4 foto specificando gruppo_id
        for i in range(2, 6):
            res_i = client.post(
                f"/api/campagne/{camp.id}/foto",
                data={"gruppo_id": gruppo_id},
                files={
                    "file": (
                        f"foto{i}.jpg",
                        BytesIO(_crea_jpeg(1080, 1080)),
                        "image/jpeg",
                    )
                },
            )
            assert res_i.status_code == 201
            assert res_i.json()["gruppo_id"] == gruppo_id

        # Verifica totale foto nel gruppo a DB
        totale = (
            db.query(Foto)
            .filter(
                Foto.campagne_id
                if hasattr(Foto, "campagne_id")
                else Foto.campagna_id == camp.id,
                Foto.gruppo_id == gruppo_id,
            )
            .count()
        )
        assert totale == 5


def _crea_webp_vp8(larghezza: int, altezza: int) -> bytes:
    """Genera un flusso WebP VP8 (lossy standard) valido."""
    # Header VP8 non compresso (3 byte) + start code 0x9D 0x01 0x2A (3 byte) + width e height a 14-bit (4 byte)
    vp8_payload = (
        b"\x00\x00\x00\x9d\x01\x2a"
        + struct.pack("<H", larghezza & 0x3FFF)
        + struct.pack("<H", altezza & 0x3FFF)
    )
    chunk = b"VP8 " + struct.pack("<I", len(vp8_payload)) + vp8_payload
    riff_payload = b"WEBP" + chunk
    return b"RIFF" + struct.pack("<I", len(riff_payload)) + riff_payload


def _crea_webp_vp8l(larghezza: int, altezza: int) -> bytes:
    """Genera un flusso WebP VP8L (lossless bit-packed) valido."""
    # Firma 0x2F (1 byte) + 32-bit: 14 bit width-1, 14 bit height-1 (4 byte)
    valore_bit = ((larghezza - 1) & 0x3FFF) | (((altezza - 1) & 0x3FFF) << 14)
    vp8l_payload = b"\x2f" + struct.pack("<I", valore_bit)
    chunk = b"VP8L" + struct.pack("<I", len(vp8l_payload)) + vp8l_payload
    riff_payload = b"WEBP" + chunk
    return b"RIFF" + struct.pack("<I", len(riff_payload)) + riff_payload


def test_debug_webp_vp8_lossy_e_vp8l_lossless(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Debug: Collaudo specifico dei parser WebP VP8 (lossy) e VP8L (lossless)."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        # 1. WebP VP8 Lossy (1200x1200)
        webp_lossy = _crea_webp_vp8(1200, 1200)
        res_lossy = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("lossy.webp", BytesIO(webp_lossy), "image/webp")},
        )
        assert res_lossy.status_code == 201
        assert res_lossy.json()["larghezza"] == 1200
        assert res_lossy.json()["altezza"] == 1200
        assert res_lossy.json()["mime"] == "image/webp"

        # 2. WebP VP8L Lossless (1400x1400)
        webp_lossless = _crea_webp_vp8l(1400, 1400)
        res_lossless = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("lossless.webp", BytesIO(webp_lossless), "image/webp")},
        )
        assert res_lossless.status_code == 201
        assert res_lossless.json()["larghezza"] == 1400
        assert res_lossless.json()["altezza"] == 1400
        assert res_lossless.json()["mime"] == "image/webp"


def test_debug_anti_spoofing_estensione_file(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Debug: Invio JPEG rinominato in .png -> riconosciuto come JPEG e salvato con .jpg (CWE-434)."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        jpeg_reale = _crea_jpeg(1080, 1080)
        # Client tenta spoofing estensione dichiarando .png e mime image/png
        res = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("falso.png", BytesIO(jpeg_reale), "image/png")},
        )
        assert res.status_code == 201
        # Il server rileva i magic bytes reali del JPEG
        assert res.json()["mime"] == "image/jpeg"
        assert res.json()["file"].endswith(".jpg")
        # Il file fisico su disco deve essere salvato con l'estensione reale .jpg
        assert (tmp_path / res.json()["file"]).is_file()


def test_debug_upload_file_vuoto_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """Debug: Caricamento di un file da 0 byte solleva 422 descrittivo."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    res = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("vuoto.jpg", BytesIO(b""), "image/jpeg")},
    )
    assert res.status_code == 422
    assert "vuoto" in res.json()["detail"].lower()


def test_debug_matrice_stati_non_bozza_vietati(
    client: TestClient, utente_di_prova, db: Session
):
    """Debug: Upload, modifica gruppo ed eliminazione vietati per tutti gli stati non-bozza (409)."""
    from app.moduli.campagne import domain, service as camp_service

    stati_non_bozza = [
        domain.INVIATA,
        domain.IN_GENERAZIONE,
        domain.GENERAZIONE_FALLITA,
        domain.IN_REVISIONE,
        domain.ATTIVA,
        domain.SOSPESA,
        domain.RESPINTA,
        domain.SCADUTA,
        domain.ANNULLATA,
        domain.CONCLUSA,
    ]

    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)

    for st in stati_non_bozza:
        # Creiamo una campagna direttamente nello stato target (bypassando la transizione per testare la guardia)
        camp = campagna_in_bozza(db, profilo_id=prof.id, stato=st)
        foto_fabbrica = fabbrica_foto(db, campagna=camp)

        # 1. Upload deve dare 409
        res_up = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res_up.status_code == 409, f"Upload fallito per stato {st}"

        # 2. Aggiornamento gruppo deve dare 409
        res_put = client.put(
            f"/api/campagne/{camp.id}/gruppi/{foto_fabbrica.gruppo_id}",
            json={"descrizione": "Nuova descrizione"},
        )
        assert res_put.status_code == 409, f"Put gruppo fallito per stato {st}"

        # 3. Delete foto deve dare 409
        res_del = client.delete(f"/api/foto/{foto_fabbrica.id}")
        assert res_del.status_code == 409, f"Delete foto fallito per stato {st}"


def test_debug_dettaglio_campagna_con_struttura_foto_completa(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Debug: GET /api/campagne/{id} restituisce l'aggregato completo di foto e gruppi."""
    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        # Carica 2 foto in gruppo 1
        res1 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto1.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        g1 = res1.json()["gruppo_id"]
        client.put(
            f"/api/campagne/{camp.id}/gruppi/{g1}",
            json={"descrizione": "Gruppo 1 Ceramiche"},
        )

        res2 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": g1},
            files={
                "file": ("foto2.jpg", BytesIO(_crea_jpeg(1200, 1200)), "image/jpeg")
            },
        )

        # Carica 1 foto in gruppo 2
        res3 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": fabbrica_gruppo(db, camp).id},
            files={
                "file": ("foto3.webp", BytesIO(_crea_webp(1300, 1300)), "image/webp")
            },
        )
        g2 = res3.json()["gruppo_id"]

        # Richiede dettaglio campagna
        res_dett = client.get(f"/api/campagne/{camp.id}")
        assert res_dett.status_code == 200
        dati_camp = res_dett.json()
        gruppi = dati_camp["gruppi"]
        assert len(gruppi) >= 2
        totale_foto = sum(len(g["foto"]) for g in gruppi)
        assert totale_foto == 3

        gruppo_g1 = next((g for g in gruppi if g["id"] == g1), None)
        assert gruppo_g1 is not None
        assert gruppo_g1["descrizione"] == "Gruppo 1 Ceramiche"
        assert len(gruppo_g1["foto"]) == 2


def test_debug_concorrenza_reale_upload_multi_thread(motore_test, tmp_path: Path):
    """Debug: Caricamento simultaneo multi-thread con 4 sessioni DB indipendenti sullo stesso gruppo."""
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy import text
    from sqlalchemy.orm import Session as SessionClass
    from app.moduli.campagne import service as camp_service

    archivio_test = ArchivioDisco(tmp_path)
    with usa_archivio(archivio_test):
        # Setup iniziale con sessione dedicata
        with SessionClass(motore_test) as s, s.begin():
            p = profilo(s)
            u_id = p.utente_id
            prof_id = p.id
            camp = campagna_in_bozza(s, profilo_id=prof_id)
            camp_id = camp.id
            gruppo_id = fabbrica_gruppo(s, camp).id

        try:
            # Prima foto del gruppo
            with SessionClass(motore_test) as s, s.begin():
                camp_service.carica_foto(
                    db=s,
                    utente_id=u_id,
                    ruolo="artigiano",
                    campagna_id=camp_id,
                    contenuto=_crea_png(1080, 1080),
                    gruppo_id=gruppo_id,
                )

            def carica_singola(indice: int) -> str:
                file_bytes = _crea_png(1080 + indice, 1080)
                with SessionClass(motore_test) as sessione:
                    with sessione.begin():
                        f = camp_service.carica_foto(
                            db=sessione,
                            utente_id=u_id,
                            ruolo="artigiano",
                            campagna_id=camp_id,
                            contenuto=file_bytes,
                            gruppo_id=gruppo_id,
                        )
                        return "ok" if f.id is not None else "errore"

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(carica_singola, i) for i in range(1, 5)]
                esiti = [f.result() for f in futures]

            # Tutti e 4 i thread devono aver caricato con successo
            assert esiti == ["ok", "ok", "ok", "ok"]

            # Verifica totale 5 foto nel gruppo (1 iniziale + 4 concorrenti)
            with SessionClass(motore_test) as s:
                totale = (
                    s.query(Foto)
                    .filter(Foto.campagna_id == camp_id, Foto.gruppo_id == gruppo_id)
                    .count()
                )
                assert totale == 5
        finally:
            # Cleanup deterministico DB (Regola 4)
            with SessionClass(motore_test) as s, s.begin():
                s.execute(
                    text("DELETE FROM foto WHERE campagna_id = :cid"),
                    {"cid": camp_id},
                )
                s.execute(
                    text("DELETE FROM gruppo_foto WHERE campagna_id = :cid"),
                    {"cid": camp_id},
                )
                s.execute(
                    text("DELETE FROM campagna WHERE id = :cid"),
                    {"cid": camp_id},
                )
                s.execute(
                    text("DELETE FROM account_social WHERE profilo_id = :pid"),
                    {"pid": prof_id},
                )
                s.execute(
                    text("DELETE FROM profilo_bottega WHERE id = :pid"),
                    {"pid": prof_id},
                )
                s.execute(text("DELETE FROM utente WHERE id = :uid"), {"uid": u_id})


# ==============================================================================
# Ordine disco/transazione: nulla di irreversibile prima del commit
# ==============================================================================


def test_upload_con_rollback_rimuove_il_file_orfano(
    utente_di_prova, db: Session, tmp_path: Path
):
    """Se la transazione termina con un rollback dopo l'upload, il file non resta su disco."""
    from app.moduli.campagne import service as camp_service

    with usa_archivio(ArchivioDisco(tmp_path)):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        foto = camp_service.carica_foto(
            db,
            art.id,
            "artigiano",
            camp.id,
            _crea_png(1080, 1080),
            fabbrica_gruppo(db, camp).id,
        )
        assert (tmp_path / foto.file).is_file()

        db.rollback()

        assert list(tmp_path.iterdir()) == []


def test_rollback_successivo_non_tocca_i_file_gia_confermati(
    utente_di_prova, db: Session, tmp_path: Path
):
    """Un listener di una foto già confermata non deve cancellarla in un rollback futuro."""
    from app.moduli.campagne import service as camp_service

    with usa_archivio(ArchivioDisco(tmp_path)):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        gruppo_id = fabbrica_gruppo(db, camp).id
        prima = camp_service.carica_foto(
            db, art.id, "artigiano", camp.id, _crea_png(1080, 1080), gruppo_id
        )
        nome_prima = prima.file
        db.commit()

        seconda = camp_service.carica_foto(
            db, art.id, "artigiano", camp.id, _crea_png(1200, 1200), gruppo_id
        )
        nome_seconda = seconda.file
        db.rollback()

        assert (tmp_path / nome_prima).is_file()
        assert not (tmp_path / nome_seconda).exists()


def test_eliminazione_con_rollback_conserva_file_e_record(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Se la transazione di una DELETE viene annullata, record e file restano entrambi."""
    with usa_archivio(ArchivioDisco(tmp_path)):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        res = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        foto_id = res.json()["id"]
        nome_file = res.json()["file"]
        db.commit()

        assert client.delete(f"/api/foto/{foto_id}").status_code == 204
        db.rollback()

        assert (tmp_path / nome_file).is_file()
        assert db.get(Foto, foto_id) is not None


def test_ca13_limite_massimo_20_foto_per_gruppo(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """CA-13: la ventunesima foto di un gruppo dà 422 senza file su disco; un altro gruppo resta libero (R-13)."""
    from app.moduli.campagne.models import GruppoFoto

    with usa_archivio(ArchivioDisco(tmp_path)):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        gruppo_db = GruppoFoto(
            profilo_id=prof.id,
            campagna_id=camp.id,
            origine="caricate",
        )
        db.add(gruppo_db)
        db.flush()

        for i in range(20):
            db.add(
                Foto(
                    profilo_id=prof.id,
                    campagna_id=camp.id,
                    gruppo_id=gruppo_db.id,
                    origine="caricata",
                    file=f"foto_{i}.png",
                    mime="image/png",
                    larghezza=1080,
                    altezza=1080,
                )
            )
        db.commit()

        res = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": gruppo_db.id},
            files={"file": ("foto21.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res.status_code == 422
        assert "massimo 20 foto" in res.json()["detail"]
        assert list(tmp_path.iterdir()) == []

        # Il limite vale per gruppo: un secondo gruppo della stessa campagna accetta foto
        secondo = GruppoFoto(
            profilo_id=prof.id, campagna_id=camp.id, origine="caricate"
        )
        db.add(secondo)
        db.commit()
        res_secondo = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": secondo.id},
            files={"file": ("altra.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res_secondo.status_code == 201
        assert res_secondo.json()["gruppo_id"] == secondo.id


# ==============================================================================
# CA-46, CA-47 & Stella (T1-23 specifici)
# ==============================================================================


def test_ca46_creazione_gruppo_create_ai_con_descrizione_e_n_immagini(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-46: bozza -> gruppo create_ai con descrizione e n_immagini -> salvato e restituito nel dettaglio."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    res = client.post(
        f"/api/campagne/{camp.id}/gruppi",
        json={
            "origine": "create_ai",
            "descrizione": "Immagini generate AI ispirate alla tradizione sarda",
            "n_immagini": 5,
        },
    )
    assert res.status_code == 201
    dati_g = res.json()
    assert dati_g["origine"] == "create_ai"
    assert (
        dati_g["descrizione"] == "Immagini generate AI ispirate alla tradizione sarda"
    )
    assert dati_g["n_immagini"] == 5
    gruppo_id = dati_g["id"]

    # Dettaglio campagna include il gruppo create_ai
    res_dett = client.get(f"/api/campagne/{camp.id}")
    assert res_dett.status_code == 200
    gruppi = res_dett.json()["gruppi"]
    gruppo_trovato = next((g for g in gruppi if g["id"] == gruppo_id), None)
    assert gruppo_trovato is not None
    assert gruppo_trovato["origine"] == "create_ai"
    assert gruppo_trovato["n_immagini"] == 5


def test_ca47_gruppo_create_ai_n_immagini_fuori_limite_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-47: gruppo create_ai con n_immagini fuori da 1-20 -> 422."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    # Troppe immagini (> 20)
    res_troppe = client.post(
        f"/api/campagne/{camp.id}/gruppi",
        json={"origine": "create_ai", "n_immagini": 25},
    )
    assert res_troppe.status_code == 422

    # Zero immagini (< 1)
    res_zero = client.post(
        f"/api/campagne/{camp.id}/gruppi",
        json={"origine": "create_ai", "n_immagini": 0},
    )
    assert res_zero.status_code == 422


def test_ca47_foto_caricata_in_gruppo_create_ai_da_422(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """CA-47: foto caricata in un gruppo create_ai -> 422."""
    with usa_archivio(ArchivioDisco(tmp_path)):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        res_g = client.post(
            f"/api/campagne/{camp.id}/gruppi",
            json={"origine": "create_ai", "n_immagini": 3},
        )
        assert res_g.status_code == 201
        gruppo_ai_id = res_g.json()["id"]

        # Caricamento foto indicando gruppo_ai_id solleva 422
        res_foto = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": gruppo_ai_id},
            files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res_foto.status_code == 422
        assert (
            "non è consentito caricare foto in un gruppo create_ai"
            in res_foto.json()["detail"].lower()
        )


def test_ca47_gruppo_da_usare_il_fuori_dal_periodo_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-47: gruppo con da_usare_il fuori dal periodo della campagna -> 422."""
    from datetime import timedelta

    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    # Data precedente all'inizio della campagna
    data_fuori = (camp.inizio - timedelta(days=2)).isoformat()
    res = client.post(
        f"/api/campagne/{camp.id}/gruppi",
        json={"origine": "caricate", "da_usare_il": data_fuori},
    )
    assert res.status_code == 422
    assert "periodo della campagna" in res.json()["detail"]


def test_stella_foto_put_da_usare(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Plan §3: PUT /foto/{id} con {"da_usare": bool} imposta o rimuove la stella."""
    with usa_archivio(ArchivioDisco(tmp_path)):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        # Upload foto iniziale
        res = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res.status_code == 201
        foto_id = res.json()["id"]
        assert res.json()["da_usare"] is False

        # Accendi stella
        res_on = client.put(f"/api/foto/{foto_id}", json={"da_usare": True})
        assert res_on.status_code == 200
        assert res_on.json()["da_usare"] is True

        db.expire_all()
        assert db.get(Foto, foto_id).da_usare is True

        # Spegni stella
        res_off = client.put(f"/api/foto/{foto_id}", json={"da_usare": False})
        assert res_off.status_code == 200
        assert res_off.json()["da_usare"] is False


def test_upload_senza_gruppo_id_o_con_gruppo_id_vuoto_da_422(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Issue #41: il gruppo è obbligatorio (plan §3). Senza `gruppo_id`, o con la stringa vuota, 422 e nessun gruppo creato."""
    with usa_archivio(ArchivioDisco(tmp_path)):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        res = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": ""},
            files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res.status_code == 422
        assert "Indica il gruppo" in res.json()["detail"]

        res_senza = client.post(
            f"/api/campagne/{camp.id}/foto",
            files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res_senza.status_code == 422
        assert "Indica il gruppo" in res_senza.json()["detail"]

        assert db.scalar(select(GruppoFoto.id)) is None
        assert list(tmp_path.iterdir()) == []


def test_debug_form_upload_con_gruppo_id_alfanumerico_invalido(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che un FormData con gruppo_id non numerico sollevi 422 con messaggio chiaro."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    res = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": "non_un_numero"},
        files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
    )
    assert res.status_code == 422
    assert "ID gruppo non valido" in res.json()["detail"]


def test_debug_png_con_dimensioni_zero_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """Un PNG con larghezza o altezza a zero byte nell'IHDR viene rifiutato con 422."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    png_zero = _crea_png(0, 1080)
    res = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("zero.png", BytesIO(png_zero), "image/png")},
    )
    assert res.status_code == 422
    assert "non valide" in res.json()["detail"].lower()


def test_debug_webp_con_dimensioni_zero_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """Un WebP con dimensioni a zero viene rifiutato con 422."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    # WebP VP8 con dimensioni 0
    header = b"RIFF\x20\x00\x00\x00WEBPVP8 \x14\x00\x00\x00"
    payload = b"\x00\x00\x00\x9d\x01\x2a\x00\x00\x00\x00" + b"\x00" * 10
    file_bytes = header + payload

    res = client.post(
        f"/api/campagne/{camp.id}/foto",
        data={"gruppo_id": _gruppo_caricate(db, camp)},
        files={"file": ("zero.webp", BytesIO(file_bytes), "image/webp")},
    )
    assert res.status_code == 422


def test_debug_gruppo_da_usare_il_uguale_a_inizio_e_fine(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che da_usare_il coincidente con inizio o fine sia ammesso sia in POST che in PUT."""
    art = utente_di_prova("artigiano")
    prof = profilo(db, utente_id=art.id)
    camp = campagna_in_bozza(db, profilo_id=prof.id)

    # POST con da_usare_il == camp.inizio -> 201
    res_inizio = client.post(
        f"/api/campagne/{camp.id}/gruppi",
        json={"origine": "caricate", "da_usare_il": camp.inizio.isoformat()},
    )
    assert res_inizio.status_code == 201
    gruppo_id = res_inizio.json()["id"]

    # PUT con da_usare_il == camp.fine -> 200
    res_fine = client.put(
        f"/api/campagne/{camp.id}/gruppi/{gruppo_id}",
        json={"da_usare_il": camp.fine.isoformat()},
    )
    assert res_fine.status_code == 200
    assert res_fine.json()["da_usare_il"] == camp.fine.isoformat()


def test_debug_operatore_puo_scaricare_foto_in_campagna_conclusa(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """Verifica che un operatore possa scaricare la foto originale anche quando la campagna è in stato conclusa."""
    from app.moduli.campagne import domain

    with usa_archivio(ArchivioDisco(tmp_path)):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)

        # Upload foto in bozza
        res_upload = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": _gruppo_caricate(db, camp)},
            files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res_upload.status_code == 201
        foto_id = res_upload.json()["id"]

        # Avanzamento forzato della campagna a 'conclusa'
        camp.stato = domain.CONCLUSA
        db.flush()

        # Operatore scarica la foto con successo (200)
        utente_di_prova("operatore")
        res_dl = client.get(f"/api/foto/{foto_id}/file")
        assert res_dl.status_code == 200
        assert res_dl.headers["content-type"] == "image/png"


def test_debug_concorrenza_upload_limite_20_foto(motore_test, tmp_path: Path):
    """Verifica che il row-lock su gruppo_foto prevenga race condition: con 19 foto, solo 1 su 2 thread concorrenti entra."""
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy import text
    from sqlalchemy.orm import Session as SessionClass
    from app.core.errori import DatiNonValidi
    from app.moduli.campagne import service as camp_service
    from app.moduli.campagne.models import GruppoFoto

    with usa_archivio(ArchivioDisco(tmp_path)):
        with SessionClass(motore_test) as s, s.begin():
            p = profilo(s, canali=["instagram"])
            u_id = p.utente_id
            prof_id = p.id
            camp = campagna_in_bozza(s, profilo_id=prof_id)
            camp_id = camp.id
            g = GruppoFoto(profilo_id=prof_id, campagna_id=camp_id, origine="caricate")
            s.add(g)
            s.flush()
            g_id = g.id

            # Inseriamo 19 foto
            for i in range(19):
                s.add(
                    Foto(
                        profilo_id=prof_id,
                        campagna_id=camp_id,
                        gruppo_id=g_id,
                        origine="caricata",
                        file=f"concurr_{i}.png",
                        mime="image/png",
                        larghezza=1080,
                        altezza=1080,
                    )
                )

        try:
            file_bytes = _crea_png(1080, 1080)

            def tenta_upload(indice: int) -> str:
                with SessionClass(motore_test) as sess:
                    try:
                        with sess.begin():
                            camp_service.carica_foto(
                                sess,
                                u_id,
                                "artigiano",
                                camp_id,
                                file_bytes,
                                gruppo_id=g_id,
                            )
                        return "ok"
                    except DatiNonValidi:
                        return "422"

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(tenta_upload, i) for i in range(2)]
                esiti = [f.result() for f in futures]

            # Esattamente 1 thread deve essere entrato (20-esima foto) e 1 respinto con 422
            assert esiti.count("ok") == 1
            assert esiti.count("422") == 1

            with SessionClass(motore_test) as s:
                totale = (
                    s.query(Foto)
                    .filter(Foto.campagna_id == camp_id, Foto.gruppo_id == g_id)
                    .count()
                )
                assert totale == 20
        finally:
            with SessionClass(motore_test) as s, s.begin():
                s.execute(
                    text("DELETE FROM foto WHERE campagna_id = :cid"),
                    {"cid": camp_id},
                )
                s.execute(
                    text("DELETE FROM gruppo_foto WHERE campagna_id = :cid"),
                    {"cid": camp_id},
                )
                s.execute(
                    text("DELETE FROM campagna WHERE id = :cid"),
                    {"cid": camp_id},
                )
                s.execute(
                    text("DELETE FROM account_social WHERE profilo_id = :pid"),
                    {"pid": prof_id},
                )
                s.execute(
                    text("DELETE FROM profilo_bottega WHERE id = :pid"),
                    {"pid": prof_id},
                )
                s.execute(text("DELETE FROM utente WHERE id = :uid"), {"uid": u_id})
