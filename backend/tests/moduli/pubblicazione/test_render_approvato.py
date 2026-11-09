"""Render all'approvazione e pubblicazione dal file (RT-07, ADR-124)."""

from __future__ import annotations

import hashlib
import io
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from PIL import Image
from sqlalchemy import select

from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.adapters.social import SocialFinto, usa_social
from app.moduli.campagne.models import Foto
from app.moduli.contenuti import service as contenuti
from app.moduli.contenuti.models import VersionePostFoto
from app.moduli.pubblicazione import service as pubblicazione
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva
from tests.moduli.contenuti.fabbrica import post_approvato


@pytest.fixture
def archivio():
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


def _jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (1200, 900), (20, 70, 40)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _post_dovuto(db, archivio, utente, adesso):
    campagna = campagna_attiva(db, profilo_id=profilo(db, utente_id=utente.id).id)
    post = post_approvato(
        db, campagna_id=campagna.id, data_ora=adesso - timedelta(minutes=1)
    )
    legame = post.versione_corrente.legami_foto[0]
    db.get(Foto, legame.foto_id).file = archivio.salva(_jpeg(), "jpg")
    db.flush()
    return post, legame


def test_meta_riceve_i_byte_del_render_approvato(db, utente_di_prova, archivio):
    adesso = datetime.now(timezone.utc)
    post, legame = _post_dovuto(db, archivio, utente_di_prova("artigiano"), adesso)
    contenuti.rendi_foto_approvate(db, post.campagna_id)
    assert legame.render is not None
    approvato = archivio.leggi_derivato(legame.foto_id, legame.render)

    social = SocialFinto()
    with usa_social(social):
        pubblicazione.pubblica_dovuti(db, adesso)

    assert len(social.pubblicazioni) == 1
    inviato = social.foto_inviate[0][0]
    assert hashlib.sha256(inviato).hexdigest() == hashlib.sha256(approvato).hexdigest()


def test_l_url_porta_la_chiave_del_render(db, utente_di_prova, archivio):
    adesso = datetime.now(timezone.utc)
    post, legame = _post_dovuto(db, archivio, utente_di_prova("artigiano"), adesso)
    contenuti.rendi_foto_approvate(db, post.campagna_id)
    social = SocialFinto()
    with usa_social(social):
        pubblicazione.pubblica_dovuti(db, adesso)
    query = parse_qs(urlparse(social.pubblicazioni[0]["url_foto"][0]).query)
    assert query["chiave"] == [legame.render]
    assert "firma" in query


def test_post_approvato_prima_della_corsia_si_rende_al_volo(
    db, utente_di_prova, archivio
):
    adesso = datetime.now(timezone.utc)
    post, legame = _post_dovuto(db, archivio, utente_di_prova("artigiano"), adesso)
    assert legame.render is None  # nessun render fissato all'approvazione

    social = SocialFinto()
    with usa_social(social):
        pubblicazione.pubblica_dovuti(db, adesso)

    assert len(social.pubblicazioni) == 1
    db.refresh(legame)
    assert legame.render is not None
    assert (
        archivio.leggi_derivato(legame.foto_id, legame.render)
        == social.foto_inviate[0][0]
    )


def test_il_render_gia_fissato_non_si_rifa_con_un_altro_esecutore(
    db, utente_di_prova, archivio, monkeypatch
):
    adesso = datetime.now(timezone.utc)
    post, legame = _post_dovuto(db, archivio, utente_di_prova("artigiano"), adesso)
    contenuti.rendi_foto_approvate(db, post.campagna_id)
    fissato = legame.render
    monkeypatch.setattr("app.moduli.campagne.service.VERSIONE_ESECUTORE", "ritocco-9")

    social = SocialFinto()
    with usa_social(social):
        pubblicazione.pubblica_dovuti(db, adesso)

    db.refresh(legame)
    assert legame.render == fissato
    assert social.foto_inviate[0][0] == archivio.leggi_derivato(legame.foto_id, fissato)


def test_render_perso_si_rifa_e_la_pubblicazione_riesce(db, utente_di_prova, archivio):
    adesso = datetime.now(timezone.utc)
    post, legame = _post_dovuto(db, archivio, utente_di_prova("artigiano"), adesso)
    contenuti.rendi_foto_approvate(db, post.campagna_id)
    archivio.elimina_derivato(legame.foto_id, legame.render)

    social = SocialFinto()
    with usa_social(social):
        pubblicazione.pubblica_dovuti(db, adesso)

    assert len(social.pubblicazioni) == 1
    assert archivio.esiste_derivato(legame.foto_id, legame.render)


def test_foto_non_leggibile_non_ferma_il_render_e_la_pubblicazione_segnala(
    db, utente_di_prova, archivio
):
    adesso = datetime.now(timezone.utc)
    post, legame = _post_dovuto(db, archivio, utente_di_prova("artigiano"), adesso)
    archivio.elimina(db.get(Foto, legame.foto_id).file)
    contenuti.rendi_foto_approvate(db, post.campagna_id)  # non solleva
    assert legame.render is None

    social = SocialFinto()
    with usa_social(social):
        pubblicazione.pubblica_dovuti(db, adesso)
    assert social.pubblicazioni == []


def test_rendi_foto_approvate_e_idempotente(db, utente_di_prova, archivio):
    adesso = datetime.now(timezone.utc)
    post, legame = _post_dovuto(db, archivio, utente_di_prova("artigiano"), adesso)
    contenuti.rendi_foto_approvate(db, post.campagna_id)
    primo = legame.render
    contenuti.rendi_foto_approvate(db, post.campagna_id)
    assert legame.render == primo
    assert len(archivio.elenca_derivati()) == 1


def test_rendi_foto_approvate_salta_i_post_non_approvati(db, utente_di_prova, archivio):
    adesso = datetime.now(timezone.utc)
    campagna = campagna_attiva(
        db, profilo_id=profilo(db, utente_id=utente_di_prova("artigiano").id).id
    )
    post = post_approvato(db, campagna_id=campagna.id, stato="da_approvare")
    legame = post.versione_corrente.legami_foto[0]
    db.get(Foto, legame.foto_id).file = archivio.salva(_jpeg(), "jpg")
    db.flush()
    contenuti.rendi_foto_approvate(db, campagna.id)
    assert legame.render is None
    assert archivio.elenca_derivati() == []


def test_una_versione_nata_dopo_l_approvazione_ha_il_suo_render(
    db, utente_di_prova, archivio
):
    """R-16: la modifica di un post approvato crea una versione approvata, già resa."""
    from app.moduli.contenuti import interventi

    adesso = datetime.now(timezone.utc)
    utente = utente_di_prova("operatore")
    post, legame = _post_dovuto(db, archivio, utente, adesso + timedelta(hours=3))
    post.data_ora = adesso + timedelta(days=2)
    db.flush()
    contenuti.rendi_foto_approvate(db, post.campagna_id)

    nuova = interventi.modifica(
        db, post.id, utente.id, "Testo nuovo", ["artigianato"], adesso
    )

    legami = db.scalars(
        select(VersionePostFoto).where(VersionePostFoto.versione_id == nuova.id)
    ).all()
    assert len(legami) == 1
    assert legami[0].render == legame.render
