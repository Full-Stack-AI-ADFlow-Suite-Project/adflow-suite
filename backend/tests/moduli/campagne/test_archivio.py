"""Test per l'archivio della bottega e le funzioni di archivio (T2a-22, spec R-13, R-27, CA-76).

Copre:
- `foto_di_archivio()` secondo R-27 e CA-76 con ogni singola esclusione/inclusione;
- `segna_pubblicata()` secondo R-27 e CA-76;
- `GET /api/archivio`: elenco gruppi senza campagna dell'artigiano;
- `POST /api/archivio/gruppi`: creazione gruppo archivio senza campagna;
- `POST /api/archivio/foto`: upload con ispezione binaria R-13;
- `GET /api/foto/{id}/file`: download foto d'archivio per proprietario e operatore;
- `DELETE /api/archivio/foto/{id}` e `DELETE /api/archivio/gruppi/{id}`: 204 con pulizia disco, 409 con n_utilizzi > 0.
"""

from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
import struct
import zlib

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.adapters.archivio import ottieni_archivio
from app.core.errori import NonTrovato
from app.moduli.campagne import service as campagne_service
from app.moduli.campagne.models import Campagna, DecisioneCampagna, Foto, GruppoFoto
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    ANALISI_IDONEA,
    campagna_conclusa,
    campagna_in_bozza,
    campagna_inviata,
    foto,
    gruppo,
    gruppo_di_archivio,
)

ORA_BASE = datetime(2030, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


def _crea_png(larghezza: int, altezza: int) -> bytes:
    """Genera un PNG binario minimale e valido con dimensioni arbitrarie."""
    header = b"\x89PNG\r\n\x1a\n"
    ihdr_dati = struct.pack(">IIBBBBB", larghezza, altezza, 8, 2, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_dati) & 0xFFFFFFFF)
    ihdr = struct.pack(">I", len(ihdr_dati)) + b"IHDR" + ihdr_dati + ihdr_crc
    iend = b"\x00\x00\x00\x00IEND\xaeB`\x82"
    return header + ihdr + iend


# ==============================================================================
# CA-76 / R-27: Unit test per foto_di_archivio e segna_pubblicata
# ==============================================================================


def test_ca76_foto_di_archivio_include_gruppo_senza_campagna(db: Session):
    """Una foto idonea caricata in un gruppo d'archivio compare con mai_uscita=True."""
    bottega = profilo(db)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=1)
    img = mazzo.foto[0]

    risultati = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="instagram", adesso=ORA_BASE
    )

    assert len(risultati) == 1
    assert risultati[0].foto.id == img.id
    assert risultati[0].gruppo.id == mazzo.id
    assert risultati[0].mai_uscita is True


def test_ca76_foto_di_archivio_include_campagna_conclusa(db: Session):
    """Una foto idonea di una campagna conclusa compare con mai_uscita=True se mai pubblicata."""
    bottega = profilo(db)
    chiusa = campagna_conclusa(db, profilo_id=bottega.id)
    immagini_chiuse = list(
        db.scalars(select(Foto).where(Foto.campagna_id == chiusa.id))
    )

    risultati = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="instagram", adesso=ORA_BASE
    )

    ids = [r.foto.id for r in risultati]
    for img in immagini_chiuse:
        assert img.id in ids


def test_ca76_esclusione_r27_foto_non_idonea(db: Session):
    """Una foto con analisi_ai.idonea=False viene esclusa (R-27)."""
    bottega = profilo(db)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=2)
    scartata = mazzo.foto[0]
    scartata.analisi_ai = {"idonea": False, "motivo": "sfocata"}
    buona = mazzo.foto[1]
    db.flush()

    risultati = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="instagram", adesso=ORA_BASE
    )

    ids = [r.foto.id for r in risultati]
    assert scartata.id not in ids
    assert buona.id in ids


def test_ca76_esclusione_r27_foto_respinta_nella_decisione(db: Session):
    """Una foto segnata in una decisione respinta viene esclusa (R-27)."""
    bottega = profilo(db)
    # Campagna respinta
    camp = Campagna(
        profilo_id=bottega.id,
        titolo="Campagna Respinta",
        inizio=date(2029, 5, 1),
        fine=date(2029, 5, 31),
        stato="respinta",
        canali=["instagram"],
        frequenza="bassa",
        obiettivo="brand",
        inviata_il=datetime(2029, 4, 20, tzinfo=timezone.utc),
        chiusa_il=datetime(2029, 4, 25, tzinfo=timezone.utc),
    )
    db.add(camp)
    db.flush()

    g = gruppo(db, camp)
    f_ok = foto(db, gruppo=g, analisi_ai=dict(ANALISI_IDONEA))
    f_respinta = foto(db, gruppo=g, analisi_ai=dict(ANALISI_IDONEA))

    # Decisione con esito respinta che segna f_respinta
    dec = DecisioneCampagna(
        campagna_id=camp.id,
        utente_id=bottega.utente_id,
        esito="respinta",
        foto_segnate=[f_respinta.id],
    )
    db.add(dec)
    db.flush()

    risultati = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="instagram", adesso=ORA_BASE
    )

    ids = [r.foto.id for r in risultati]
    assert f_respinta.id not in ids
    assert f_ok.id in ids


def test_ca76_esclusione_r27_uscita_da_meno_di_90_giorni(db: Session):
    """Una foto pubblicata sul canale da meno di 90 giorni viene esclusa (R-27)."""
    bottega = profilo(db)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=1)
    img = mazzo.foto[0]
    # Uscita 89 giorni prima di ORA_BASE
    img.pubblicata_su = {"instagram": (ORA_BASE - timedelta(days=89)).isoformat()}
    db.flush()

    risultati = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="instagram", adesso=ORA_BASE
    )

    ids = [r.foto.id for r in risultati]
    assert img.id not in ids

    # Ma su un altro canale (es. facebook) non è mai uscita, quindi lì c'è!
    risultati_fb = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="facebook", adesso=ORA_BASE
    )
    assert img.id in [r.foto.id for r in risultati_fb]
    assert next(r for r in risultati_fb if r.foto.id == img.id).mai_uscita is True


def test_ca76_inclusione_r27_uscita_da_almeno_90_giorni_ha_mai_uscita_false(
    db: Session,
):
    """Una foto uscita sul canale da almeno 90 giorni viene inclusa con mai_uscita=False (R-27, R-28)."""
    bottega = profilo(db)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=1)
    img = mazzo.foto[0]
    # Uscita esattamente 90 giorni prima di ORA_BASE
    img.pubblicata_su = {"instagram": (ORA_BASE - timedelta(days=90)).isoformat()}
    db.flush()

    risultati = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="instagram", adesso=ORA_BASE
    )

    ids = [r.foto.id for r in risultati]
    assert img.id in ids
    item = next(r for r in risultati if r.foto.id == img.id)
    assert item.mai_uscita is False


def test_ca76_inclusione_r27_foto_non_ancora_analizzata_ha_mai_uscita_true(
    db: Session,
):
    """Una foto d'archivio ancora da analizzare (analisi_ai=None) è compresa con mai_uscita=True (plan §6)."""
    bottega = profilo(db)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)
    da_analizzare = foto(db, gruppo=mazzo, analisi_ai=None)
    db.flush()

    risultati = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="instagram", adesso=ORA_BASE
    )

    ids = [r.foto.id for r in risultati]
    assert da_analizzare.id in ids
    item = next(r for r in risultati if r.foto.id == da_analizzare.id)
    assert item.mai_uscita is True


def test_ca76_esclusione_campagne_non_chiuse(db: Session):
    """Foto di campagne in bozza o inviate non entrano nell'archivio."""
    bottega = profilo(db)
    bozza = campagna_in_bozza(db, profilo_id=bottega.id)
    f_bozza = foto(db, gruppo=gruppo(db, bozza), analisi_ai=dict(ANALISI_IDONEA))

    inviata = campagna_inviata(db, profilo_id=bottega.id)
    f_inviata = db.scalars(select(Foto).where(Foto.campagna_id == inviata.id)).first()

    risultati = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="instagram", adesso=ORA_BASE
    )

    ids = [r.foto.id for r in risultati]
    assert f_bozza.id not in ids
    assert f_inviata.id not in ids


def test_ca76_foto_di_archivio_ordinamento_per_gruppo_e_foto_id(db: Session):
    """Le foto restituite sono ordinate per gruppo_id e per Foto.id (plan §6)."""
    bottega = profilo(db)
    g1 = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=2)
    g2 = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=2)

    risultati = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="instagram", adesso=ORA_BASE
    )

    coppie = [(r.gruppo.id, r.foto.id) for r in risultati]
    assert coppie == sorted(coppie)


def test_ca76_isolamento_profili_archivio(db: Session):
    """foto_di_archivio restituisce solo le foto del profilo richiesto."""
    bottega1 = profilo(db)
    bottega2 = profilo(db)

    mazzo1 = gruppo_di_archivio(db, profilo_id=bottega1.id, n_foto=1)
    mazzo2 = gruppo_di_archivio(db, profilo_id=bottega2.id, n_foto=1)

    risultati1 = campagne_service.foto_di_archivio(
        db, profilo_id=bottega1.id, canale="instagram", adesso=ORA_BASE
    )
    ids1 = [r.foto.id for r in risultati1]
    assert mazzo1.foto[0].id in ids1
    assert mazzo2.foto[0].id not in ids1


def test_ca76_segna_pubblicata_e_idempotenza(db: Session):
    """segna_pubblicata scrive il canale e l'istante ISO, ed è idempotente (CA-76)."""
    f = foto(db)
    quando1 = datetime(2030, 2, 1, 14, 30, tzinfo=timezone.utc)
    campagne_service.segna_pubblicata(db, f.id, "instagram", quando1)

    db.expire(f)
    assert f.pubblicata_su == {"instagram": quando1.isoformat()}

    quando2 = datetime(2030, 2, 5, 9, 0, tzinfo=timezone.utc)
    campagne_service.segna_pubblicata(db, f.id, "facebook", quando2)

    db.expire(f)
    assert f.pubblicata_su == {
        "instagram": quando1.isoformat(),
        "facebook": quando2.isoformat(),
    }

    # Re-invocazione idempotente sullo stesso canale aggiorna la data
    quando3 = datetime(2030, 3, 1, 10, 0, tzinfo=timezone.utc)
    campagne_service.segna_pubblicata(db, f.id, "instagram", quando3)
    db.expire(f)
    assert f.pubblicata_su["instagram"] == quando3.isoformat()


def test_ca76_segna_pubblicata_inesistente_solleva_non_trovato(db: Session):
    """segna_pubblicata solleva NonTrovato se l'id non esiste."""
    with pytest.raises(NonTrovato):
        campagne_service.segna_pubblicata(
            db, 999999, "instagram", datetime.now(timezone.utc)
        )


# ==============================================================================
# Endpoint API: GET /api/archivio, POST /api/archivio/gruppi, POST /api/archivio/foto, DELETE
# ==============================================================================


def test_api_get_archivio_successo_e_isolamento(
    client: TestClient, utente_di_prova, db: Session
):
    """GET /api/archivio elenca i soli gruppi senza campagna dell'artigiano (plan §3)."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)

    # Gruppo d'archivio dell'artigiano
    g_arc = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=2)

    # Gruppo legato a una campagna (non deve comparire in GET /api/archivio)
    camp = campagna_in_bozza(db, profilo_id=bottega.id)
    gruppo(db, camp)

    # Gruppo d'archivio di un altro artigiano
    altro_art = profilo(db)
    gruppo_di_archivio(db, profilo_id=altro_art.id, n_foto=1)

    r = client.get("/api/archivio")
    assert r.status_code == 200
    dati = r.json()
    assert len(dati) == 1
    assert dati[0]["id"] == g_arc.id
    assert dati[0]["origine"] == "caricate"
    assert len(dati[0]["foto"]) == 2


def test_api_get_archivio_senza_gruppi_restituisce_lista_vuota(
    client: TestClient, utente_di_prova, db: Session
):
    """GET /api/archivio restituisce [] se l'artigiano non ha ancora gruppi d'archivio."""
    artigiano = utente_di_prova("artigiano")
    profilo(db, utente_id=artigiano.id)

    r = client.get("/api/archivio")
    assert r.status_code == 200
    assert r.json() == []


def test_api_get_archivio_senza_profilo_da_404(
    client: TestClient, utente_di_prova, db: Session
):
    """GET /api/archivio risponde 404 se l'artigiano non ha ancora salvato il profilo (plan §3)."""
    utente_di_prova("artigiano")
    r = client.get("/api/archivio")
    assert r.status_code == 404


def test_api_get_archivio_richiede_ruolo_artigiano(
    client: TestClient, utente_di_prova, db: Session
):
    """GET /api/archivio è riservato agli artigiani (403 per operatori)."""
    utente_di_prova("operatore")
    r = client.get("/api/archivio")
    assert r.status_code == 403


def test_api_post_archivio_gruppi_successo(
    client: TestClient, utente_di_prova, db: Session
):
    """POST /api/archivio/gruppi crea un gruppo caricate senza campagna (plan §3)."""
    artigiano = utente_di_prova("artigiano")
    profilo(db, utente_id=artigiano.id)

    r = client.post(
        "/api/archivio/gruppi", json={"descrizione": "Nuove ceramiche 2030"}
    )
    assert r.status_code == 201
    dati = r.json()
    assert dati["origine"] == "caricate"
    assert dati["descrizione"] == "Nuove ceramiche 2030"
    assert dati["foto"] == []


def test_api_post_archivio_gruppi_validazioni_descrizione_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """POST /api/archivio/gruppi dà 422 senza descrizione o con descrizione vuota."""
    artigiano = utente_di_prova("artigiano")
    profilo(db, utente_id=artigiano.id)

    r1 = client.post("/api/archivio/gruppi", json={})
    assert r1.status_code == 422

    r2 = client.post("/api/archivio/gruppi", json={"descrizione": "   "})
    assert r2.status_code == 422


def test_api_post_archivio_foto_successo_e_controlli_r13(
    client: TestClient, utente_di_prova, db: Session
):
    """POST /api/archivio/foto carica l'immagine convalidandola secondo R-13 (plan §3)."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)

    png_valido = _crea_png(1080, 1080)
    r = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("foto.png", BytesIO(png_valido), "image/png")},
    )
    assert r.status_code == 201
    dati = r.json()
    assert dati["gruppo_id"] == mazzo.id
    assert dati["larghezza"] == 1080
    assert dati["altezza"] == 1080
    assert dati["mime"] == "image/png"


def test_api_post_archivio_foto_lato_corto_sotto_1080_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """POST /api/archivio/foto rifiuta immagini con lato corto < 1080 px (R-13)."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)

    png_piccolo = _crea_png(800, 1200)
    r = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("piccola.png", BytesIO(png_piccolo), "image/png")},
    )
    assert r.status_code == 422


def test_api_post_archivio_foto_gruppo_altrui_o_con_campagna_da_404(
    client: TestClient, utente_di_prova, db: Session
):
    """POST /api/archivio/foto risponde 404 se il gruppo è di un altro o appartiene a una campagna."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)

    # Gruppo di altro artigiano
    altro = profilo(db)
    g_altro = gruppo_di_archivio(db, profilo_id=altro.id, n_foto=0)

    # Gruppo di una campagna della stessa bottega
    camp = campagna_in_bozza(db, profilo_id=bottega.id)
    g_camp = gruppo(db, camp)

    png = _crea_png(1080, 1080)

    r1 = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(g_altro.id)},
        files={"file": ("foto.png", BytesIO(png), "image/png")},
    )
    assert r1.status_code == 404

    r2 = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(g_camp.id)},
        files={"file": ("foto.png", BytesIO(png), "image/png")},
    )
    assert r2.status_code == 404


def test_api_post_archivio_foto_limite_20_foto_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """POST /api/archivio/foto rifiuta il caricamento se il gruppo contiene già 20 foto (R-13)."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=20)

    png = _crea_png(1080, 1080)
    r = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("foto21.png", BytesIO(png), "image/png")},
    )
    assert r.status_code == 422


def test_api_get_foto_file_per_foto_di_archivio(
    client: TestClient, utente_di_prova, db: Session
):
    """GET /api/foto/{id}/file funziona anche per le foto d'archivio (plan §3)."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)

    png_bytes = _crea_png(1080, 1080)
    r_up = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("foto.png", BytesIO(png_bytes), "image/png")},
    )
    foto_id = r_up.json()["id"]

    # 1. L'artigiano proprietario la scarica con successo
    r_down = client.get(f"/api/foto/{foto_id}/file")
    assert r_down.status_code == 200
    assert r_down.content == png_bytes
    assert r_down.headers["content-type"] == "image/png"
    assert r_down.headers["X-Content-Type-Options"] == "nosniff"

    # 2. Un operatore la può scaricare
    utente_di_prova("operatore")
    r_op = client.get(f"/api/foto/{foto_id}/file")
    assert r_op.status_code == 200
    assert r_op.content == png_bytes

    # 3. Un altro artigiano riceve 404
    utente_di_prova("artigiano")
    r_altrui = client.get(f"/api/foto/{foto_id}/file")
    assert r_altrui.status_code == 404


def test_api_delete_archivio_foto_successo(
    client: TestClient, utente_di_prova, db: Session
):
    """DELETE /api/archivio/foto/{id} elimina la foto (204) e rimuove il file fisico su commit."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)

    png_bytes = _crea_png(1080, 1080)
    r_up = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("foto.png", BytesIO(png_bytes), "image/png")},
    )
    foto_id = r_up.json()["id"]

    foto_db = db.get(Foto, foto_id)
    nome_disco = foto_db.file

    archivio = ottieni_archivio()
    assert archivio.esiste(nome_disco)

    r_ok = client.delete(f"/api/archivio/foto/{foto_id}")
    assert r_ok.status_code == 204
    assert db.get(Foto, foto_id) is None

    # L'hook di rimozione fisica scatta su commit
    db.commit()
    assert not archivio.esiste(nome_disco)


def test_api_delete_archivio_foto_vincoli(
    client: TestClient, utente_di_prova, db: Session
):
    """DELETE /api/archivio/foto/{id} dà 409 se usata in un post, 404 se altrui."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)

    png_bytes = _crea_png(1080, 1080)
    r_up = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("foto.png", BytesIO(png_bytes), "image/png")},
    )
    foto_id = r_up.json()["id"]

    # 1. Se n_utilizzi > 0 -> 409
    foto_db = db.get(Foto, foto_id)
    foto_db.n_utilizzi = 1
    db.flush()

    r_409 = client.delete(f"/api/archivio/foto/{foto_id}")
    assert r_409.status_code == 409

    # 2. Altro artigiano -> 404
    altro = utente_di_prova("artigiano")
    profilo(db, utente_id=altro.id)
    r_altro = client.delete(f"/api/archivio/foto/{foto_id}")
    assert r_altro.status_code == 404


def test_api_delete_archivio_gruppi_successo(
    client: TestClient, utente_di_prova, db: Session
):
    """DELETE /api/archivio/gruppi/{id} elimina il gruppo e le sue foto (204) con pulizia disco su commit."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)

    png_bytes = _crea_png(1080, 1080)
    r_up = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("foto.png", BytesIO(png_bytes), "image/png")},
    )
    foto_id = r_up.json()["id"]

    foto_db = db.get(Foto, foto_id)
    nome_disco = foto_db.file

    archivio = ottieni_archivio()
    assert archivio.esiste(nome_disco)

    r_ok = client.delete(f"/api/archivio/gruppi/{mazzo.id}")
    assert r_ok.status_code == 204
    assert db.get(GruppoFoto, mazzo.id) is None
    assert db.get(Foto, foto_id) is None

    # L'hook di rimozione fisica scatta su commit
    db.commit()
    assert not archivio.esiste(nome_disco)


def test_api_delete_archivio_gruppi_vincoli(
    client: TestClient, utente_di_prova, db: Session
):
    """DELETE /api/archivio/gruppi/{id} dà 409 se una foto è usata, 404 se altrui."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)

    png_bytes = _crea_png(1080, 1080)
    r_up = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("foto.png", BytesIO(png_bytes), "image/png")},
    )
    foto_id = r_up.json()["id"]

    # 1. Se una foto ha n_utilizzi > 0 -> 409
    foto_db = db.get(Foto, foto_id)
    foto_db.n_utilizzi = 2
    db.flush()

    r_409 = client.delete(f"/api/archivio/gruppi/{mazzo.id}")
    assert r_409.status_code == 409

    # 2. Altro artigiano -> 404
    altro = utente_di_prova("artigiano")
    profilo(db, utente_id=altro.id)
    r_altro = client.delete(f"/api/archivio/gruppi/{mazzo.id}")
    assert r_altro.status_code == 404


# ==============================================================================
# Test di Sicurezza (Defense in Depth), Robustezza e Concorrenza
# ==============================================================================


def test_ca76_foto_di_archivio_case_insensitive_e_spazi(db: Session):
    """Verifica resilienza a maiuscole e spazi sui canali in foto_di_archivio e segna_pubblicata."""
    bottega = profilo(db)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=1)
    img = mazzo.foto[0]

    # Segna pubblicata con spazi e maiuscole
    campagne_service.segna_pubblicata(
        db, img.id, "  InStAgRaM  ", ORA_BASE - timedelta(days=95)
    )
    db.expire(img)
    assert "instagram" in img.pubblicata_su

    # Ricerca con casing misto
    risultati = campagne_service.foto_di_archivio(
        db, profilo_id=bottega.id, canale="INSTAGRAM", adesso=ORA_BASE
    )
    assert len(risultati) == 1
    assert risultati[0].foto.id == img.id
    assert risultati[0].mai_uscita is False


def test_api_post_archivio_foto_gruppo_id_invalido_o_assente(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che gruppo_id alfanumerico, vuoto o omesso risponda sempre 422."""
    artigiano = utente_di_prova("artigiano")
    profilo(db, utente_id=artigiano.id)
    png_valido = _crea_png(1080, 1080)

    # 1. gruppo_id non numerico
    r1 = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": "non-un-numero"},
        files={"file": ("foto.png", BytesIO(png_valido), "image/png")},
    )
    assert r1.status_code == 422

    # 2. gruppo_id vuoto
    r2 = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": "   "},
        files={"file": ("foto.png", BytesIO(png_valido), "image/png")},
    )
    assert r2.status_code == 422

    # 3. gruppo_id omesso
    r3 = client.post(
        "/api/archivio/foto",
        data={},
        files={"file": ("foto.png", BytesIO(png_valido), "image/png")},
    )
    assert r3.status_code == 422


def test_api_post_archivio_foto_file_vuoto_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che un file di 0 byte venga rifiutato con 422."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)

    r = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("vuoto.png", BytesIO(b""), "image/png")},
    )
    assert r.status_code == 422


def test_api_post_archivio_foto_non_immagine_o_decompression_bomb(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica controlli di sicurezza (Defense in Depth): anti-spoofing e anti-decompression bomb."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)

    # File testo mascherato da png
    r_spoof = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("falso.png", BytesIO(b"Questo non e un png"), "image/png")},
    )
    assert r_spoof.status_code == 422

    # Dimensione pixel eccessiva (bomb > 36M px: 7000x6000 = 42M px)
    png_bomb = _crea_png(7000, 6000)
    r_bomb = client.post(
        "/api/archivio/foto",
        data={"gruppo_id": str(mazzo.id)},
        files={"file": ("bomb.png", BytesIO(png_bomb), "image/png")},
    )
    assert r_bomb.status_code == 422


def test_api_delete_foto_o_gruppo_con_campagna_da_404(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che foto o gruppi con campagna non siano manipolabili tramite gli endpoint /archivio (404)."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    camp = campagna_in_bozza(db, profilo_id=bottega.id)
    g_camp = gruppo(db, camp)
    f_camp = foto(db, gruppo=g_camp)

    # 1. Cancellazione foto di campagna tramite /archivio/foto/{id} -> 404
    r_foto = client.delete(f"/api/archivio/foto/{f_camp.id}")
    assert r_foto.status_code == 404

    # 2. Cancellazione gruppo di campagna tramite /archivio/gruppi/{id} -> 404
    r_gruppo = client.delete(f"/api/archivio/gruppi/{g_camp.id}")
    assert r_gruppo.status_code == 404


def test_api_risorse_inesistenti_da_404(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che id inesistenti su download e delete restituiscano coerentemente 404."""
    artigiano = utente_di_prova("artigiano")
    profilo(db, utente_id=artigiano.id)

    assert client.delete("/api/archivio/foto/999999").status_code == 404
    assert client.delete("/api/archivio/gruppi/999999").status_code == 404
    assert client.get("/api/foto/999999/file").status_code == 404


def test_concorrenza_upload_archivio_limite_20_foto(motore_test, tmp_path: Path):
    """Verifica che il row-lock su GruppoFoto e l'advisory lock prevengano race condition: con 19 foto d'archivio, solo 1 su 2 thread concorrenti entra."""
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy import text
    from sqlalchemy.orm import Session as SessionClass
    from app.adapters.archivio import ArchivioDisco, usa_archivio
    from app.core.errori import DatiNonValidi
    from app.moduli.campagne import archivio as archivio_modulo

    with usa_archivio(ArchivioDisco(tmp_path)):
        with SessionClass(motore_test) as s, s.begin():
            p = profilo(s, canali=["instagram"])
            u_id = p.utente_id
            prof_id = p.id
            g = GruppoFoto(
                profilo_id=prof_id,
                campagna_id=None,
                origine="caricate",
                descrizione="Archivio concorrente",
            )
            s.add(g)
            s.flush()
            g_id = g.id

            # Inseriamo 19 foto
            for i in range(19):
                s.add(
                    Foto(
                        profilo_id=prof_id,
                        campagna_id=None,
                        gruppo_id=g_id,
                        origine="caricata",
                        file=f"arc_concurr_{i}.png",
                        mime="image/png",
                        larghezza=1080,
                        altezza=1080,
                        da_usare=False,
                        pubblicata_su={},
                    )
                )

        try:
            file_bytes = _crea_png(1080, 1080)

            def tenta_upload(indice: int) -> str:
                with SessionClass(motore_test) as sess:
                    try:
                        with sess.begin():
                            archivio_modulo.carica_foto_archivio(
                                sess,
                                u_id,
                                g_id,
                                file_bytes,
                            )
                        return "ok"
                    except DatiNonValidi:
                        return "422"

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(tenta_upload, i) for i in range(2)]
                esiti = [f.result() for f in futures]

            # Esattamente 1 thread entra (raggiungendo la 20-esima foto) e 1 viene respinto con 422
            assert esiti.count("ok") == 1
            assert esiti.count("422") == 1

            with SessionClass(motore_test) as s:
                totale = (
                    s.query(Foto)
                    .filter(Foto.campagna_id.is_(None), Foto.gruppo_id == g_id)
                    .count()
                )
                assert totale == 20
        finally:
            with SessionClass(motore_test) as s, s.begin():
                s.execute(
                    text("DELETE FROM foto WHERE gruppo_id = :gid"),
                    {"gid": g_id},
                )
                s.execute(
                    text("DELETE FROM gruppo_foto WHERE id = :gid"),
                    {"gid": g_id},
                )
                s.execute(
                    text("DELETE FROM account_social WHERE profilo_id = :pid"),
                    {"pid": prof_id},
                )
                s.execute(
                    text("DELETE FROM profilo_bottega WHERE id = :pid"),
                    {"pid": prof_id},
                )


def test_segna_pubblicata_normalizza_in_utc_se_fuso_diverso(db: Session):
    """Verifica che segna_pubblicata converta in UTC qualsiasi datetime aware con offset non UTC (es. +02:00)."""
    f = foto(db)
    tz_piu_due = timezone(timedelta(hours=2))
    ora_piu_due = datetime(2030, 5, 10, 14, 0, tzinfo=tz_piu_due)
    campagne_service.segna_pubblicata(db, f.id, "instagram", ora_piu_due)
    db.expire(f)
    assert f.pubblicata_su["instagram"] == "2030-05-10T12:00:00+00:00"
    assert datetime.fromisoformat(f.pubblicata_su["instagram"]).tzinfo == timezone.utc
