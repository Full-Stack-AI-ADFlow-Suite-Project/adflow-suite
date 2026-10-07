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

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.moduli.campagne.models import Foto
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_in_bozza,
    campagna_inviata,
    foto as fabbrica_foto,
)


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

        # 1. Carica prima foto senza gruppo_id: riceve nuovo UUID
        png_1 = _crea_png(1080, 1080)
        res_1 = client.post(
            f"/api/campagne/{camp.id}/foto",
            files={"file": ("foto1.png", BytesIO(png_1), "image/png")},
        )
        assert res_1.status_code == 201
        gruppo_id = res_1.json()["gruppo_id"]
        foto1_id = res_1.json()["id"]
        assert UUID(gruppo_id)

        # 2. Aggiorna descrizione gruppo via PUT
        res_put = client.put(
            f"/api/campagne/{camp.id}/gruppi/{gruppo_id}",
            json={"descrizione": "Ceramiche decorate a mano con smalti blu"},
        )
        assert res_put.status_code == 200
        assert (
            res_put.json()["descrizione"] == "Ceramiche decorate a mano con smalti blu"
        )

        # Verifica che foto 1 abbia ora la descrizione
        foto1_db = db.get(Foto, foto1_id)
        assert foto1_db.descrizione == "Ceramiche decorate a mano con smalti blu"

        # 3. Carica seconda foto specificando lo stesso gruppo_id: eredita automaticamente la descrizione!
        jpg_2 = _crea_jpeg(1200, 1200)
        res_2 = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": gruppo_id},
            files={"file": ("foto2.jpg", BytesIO(jpg_2), "image/jpeg")},
        )
        assert res_2.status_code == 201
        assert res_2.json()["gruppo_id"] == gruppo_id
        assert res_2.json()["descrizione"] == "Ceramiche decorate a mano con smalti blu"


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
        f"/api/campagne/{camp.id}/gruppi/{uuid4()}",
        json={"descrizione": "Nuova descrizione"},
    )
    assert risposta.status_code == 404
    assert "Gruppo di foto non trovato" in risposta.json()["detail"]


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

        # Verifica rimozione da DB e da disco
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

        # Entrambe le foto devono essere sparite da DB e disco
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
