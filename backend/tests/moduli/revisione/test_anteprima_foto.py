"""L'anteprima reale della foto del post (RT-08, ADR-124, D1)."""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import delete

from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.main import app
from app.moduli.accesso.service import utente_corrente
from app.moduli.campagne.models import Foto
from app.moduli.contenuti.models import VersionePostFoto
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_approvato, post_da_approvare


@pytest.fixture
def archivio():
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


def _jpeg(dimensioni=(2400, 1600)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", dimensioni, (120, 80, 40)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _con_file(db, archivio, post) -> None:
    for legame in post.versione_corrente.legami_foto:
        db.get(Foto, legame.foto_id).file = archivio.salva(_jpeg(), "jpg")
    db.flush()


def _entra(record) -> None:
    app.dependency_overrides[utente_corrente] = lambda: record


@pytest.fixture
def mondo(db, archivio):
    a = utente(db, "artigiano")
    b = utente(db, "artigiano")
    operatore = utente(db, "operatore")
    bottega_a = profilo(db, utente_id=a.id)
    profilo(db, utente_id=b.id)
    revisione = campagna_in_revisione(db, profilo_id=bottega_a.id)
    da_approvare = post_da_approvare(db, campagna_id=revisione.id)
    attiva = campagna_attiva(db, profilo_id=bottega_a.id)
    approvato = post_approvato(
        db,
        campagna_id=attiva.id,
        data_ora=datetime.now(timezone.utc) + timedelta(days=3),
    )
    _con_file(db, archivio, da_approvare)
    _con_file(db, archivio, approvato)
    return dict(
        a=a, b=b, operatore=operatore, da_approvare=da_approvare, approvato=approvato
    )


def _url(post, variante: str | None = None) -> str:
    base = f"/api/post/{post.id}/foto/anteprima"
    return base + (f"?variante={variante}" if variante else "")


def _dimensioni(risposta) -> tuple[int, int]:
    return Image.open(io.BytesIO(risposta.content)).size


def test_operatore_vede_un_jpeg_con_lato_corto_1080(mondo, client):
    _entra(mondo["operatore"])
    risposta = client.get(_url(mondo["da_approvare"]))
    assert risposta.status_code == 200
    assert risposta.headers["content-type"] == "image/jpeg"
    assert risposta.headers["x-content-type-options"] == "nosniff"
    assert risposta.content.startswith(b"\xff\xd8\xff")
    assert min(_dimensioni(risposta)) == 1080


@pytest.mark.parametrize("variante", ["originale", "standard"])
def test_operatore_chiede_le_varianti_disponibili(mondo, client, variante):
    _entra(mondo["operatore"])
    assert client.get(_url(mondo["da_approvare"], variante)).status_code == 200


def test_la_spinta_e_spenta_fino_a_RT_25(mondo, client):
    _entra(mondo["operatore"])
    assert client.get(_url(mondo["da_approvare"], "spinta")).status_code == 422


def test_variante_sconosciuta_422(mondo, client):
    _entra(mondo["operatore"])
    assert client.get(_url(mondo["da_approvare"], "ottima")).status_code == 422


def test_post_senza_foto_o_inesistente_404(mondo, client, db):
    _entra(mondo["operatore"])
    assert client.get("/api/post/999999/foto/anteprima").status_code == 404
    versione = mondo["da_approvare"].versione_corrente
    db.execute(
        delete(VersionePostFoto).where(VersionePostFoto.versione_id == versione.id)
    )
    db.expire(versione, ["legami_foto"])
    assert client.get(_url(mondo["da_approvare"])).status_code == 404


def test_senza_sessione_401(mondo, client):
    app.dependency_overrides.pop(utente_corrente, None)
    assert client.get(_url(mondo["approvato"])).status_code == 401


def test_artigiano_vede_il_render_dei_post_approvati(mondo, client):
    _entra(mondo["a"])
    risposta = client.get(_url(mondo["approvato"]))
    assert risposta.status_code == 200
    assert min(_dimensioni(risposta)) == 1080


def test_artigiano_non_vede_i_post_non_approvati(mondo, client):
    """D1: solo i post approvati. Il proprietario riceve 409, come per il calendario."""
    _entra(mondo["a"])
    assert client.get(_url(mondo["da_approvare"])).status_code == 409


def test_artigiano_vede_la_variante_scelta_e_ignora_il_parametro(mondo, client):
    _entra(mondo["a"])
    scelto = client.get(_url(mondo["approvato"]))
    altro = client.get(_url(mondo["approvato"], "originale"))
    assert altro.status_code == 200
    assert altro.content == scelto.content


def test_un_altro_artigiano_riceve_404(mondo, client):
    _entra(mondo["b"])
    assert client.get(_url(mondo["approvato"])).status_code == 404
    assert client.get(_url(mondo["da_approvare"])).status_code == 404


def test_la_vista_del_post_porta_anteprima_e_varianti(mondo, client):
    _entra(mondo["operatore"])
    corpo = client.get(f"/api/campagne/{mondo['da_approvare'].campagna_id}/post").json()
    post = next(
        p
        for u in corpo["uscite"]
        for p in u["post"]
        if p["post_id"] == mondo["da_approvare"].id
    )
    foto = post["foto"]
    assert (
        foto["anteprima_url"] == f"/api/post/{mondo['da_approvare'].id}/foto/anteprima"
    )
    assert foto["varianti"] == {
        "disponibili": ["originale", "standard"],
        "uguali": ["standard"],
        "scelta": "standard",
    }
    assert foto["zone_privacy"] == {"numero": 0, "decise": 0, "oscurate": False}
    assert foto["avvisi"] == []
