"""Guasti di Meta: errori temporanei e definitivi (T4-105, §7.4).

L'adattatore vero (5xx, 190, 368, 4/17/32/613) è coperto dai suoi test
(`tests/adapters/social/test_meta.py`): qui si prova il comportamento del
tick con il social finto — un errore temporaneo lascia il tentativo `in_corso`
e riprova fino a `TENTATIVI_MAX`, poi il post è `fallito` e riprogrammabile.
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

from PIL import Image
from sqlalchemy import select

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.adapters.social.finto import (
    MARCA_ERRORE_DEFINITIVO,
    MARCA_ERRORE_TEMPORANEO,
    SocialFinto,
)
from app.adapters.social import usa_social
from app.moduli.campagne.models import Foto
from app.moduli.contenuti.models import Post
from app.moduli.pubblicazione import service as pubblicazione
from app.moduli.pubblicazione.models import Pubblicazione
from app.moduli.revisione import interventi
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva
from tests.moduli.contenuti.fabbrica import (
    post_approvato,
    post_da_approvare,
    uscita,
)


def _post_dovuto(
    db, utente, archivio: ArchivioDisco, adesso, marcatore: str = ""
) -> int:
    bottega = profilo(db, utente_id=utente.id)
    campagna = campagna_attiva(
        db,
        profilo_id=bottega.id,
        inizio=adesso.date() - timedelta(days=1),
        fine=adesso.date() + timedelta(days=30),
    )
    post = post_approvato(
        db, campagna_id=campagna.id, data_ora=adesso - timedelta(minutes=1)
    )
    buffer = io.BytesIO()
    Image.new("RGB", (1080, 1350), (60, 30, 90)).save(buffer, format="JPEG")
    for legame in post.versione_corrente.legami_foto:
        immagine = db.get(Foto, legame.foto_id)
        immagine.file = archivio.salva(buffer.getvalue(), "jpg")
    if marcatore:
        post.versione_corrente.testo = f"Testo {marcatore}"
    db.flush()
    return post.id


def test_un_errore_temporaneo_riprova_fino_al_massimo_poi_fallisce(
    db, utente_di_prova, tmp_path
):
    """Tre tentativi temporanei → `fallito`; il tentativo resta e non raddoppia."""
    utente = utente_di_prova("artigiano")
    archivio = ArchivioDisco(tmp_path)
    adesso = datetime.now(timezone.utc)
    with usa_archivio(archivio):
        post_id = _post_dovuto(db, utente, archivio, adesso, MARCA_ERRORE_TEMPORANEO)
    social = SocialFinto()
    with usa_archivio(archivio), usa_social(social):
        for _ in range(pubblicazione.TENTATIVI_MAX):
            pubblicazione.pubblica_dovuti(db, adesso)
    post = db.get(Post, post_id)
    assert post.stato == "fallito"
    tentativi = db.scalars(
        select(Pubblicazione).where(Pubblicazione.post_id == post_id)
    ).all()
    assert len(tentativi) == 1, "un tentativo per tick doveva essere riusato"
    assert len(social.pubblicazioni) == pubblicazione.TENTATIVI_MAX


def test_un_errore_definitivo_fallisce_al_primo_colpo(db, utente_di_prova, tmp_path):
    """Errore definitivo (marca FAIL_DEF) → `fallito` subito."""
    utente = utente_di_prova("artigiano")
    archivio = ArchivioDisco(tmp_path)
    adesso = datetime.now(timezone.utc)
    with usa_archivio(archivio):
        post_id = _post_dovuto(db, utente, archivio, adesso, MARCA_ERRORE_DEFINITIVO)
    with usa_archivio(archivio), usa_social(SocialFinto()):
        pubblicazione.pubblica_dovuti(db, adesso)
    assert db.get(Post, post_id).stato == "fallito"


def test_un_post_fallito_si_riprogramma_e_esce(db, utente_di_prova, tmp_path):
    """R-34: riprogramma un post fallito e il tick lo pubblica al nuovo orario."""
    utente = utente_di_prova("artigiano")
    operatore = utente_di_prova("operatore")
    archivio = ArchivioDisco(tmp_path)
    adesso = datetime.now(timezone.utc)
    with usa_archivio(archivio):
        post_id = _post_dovuto(db, utente, archivio, adesso, MARCA_ERRORE_DEFINITIVO)
    with usa_archivio(archivio), usa_social(SocialFinto()):
        pubblicazione.pubblica_dovuti(db, adesso)
    assert db.get(Post, post_id).stato == "fallito"

    # si riprogramma senza la marca d'errore e si pubblica
    post = db.get(Post, post_id)
    post.versione_corrente.testo = "Testo senza marcatori"
    interventi.riprogramma(
        db, post_id, operatore.id, adesso + timedelta(minutes=30), adesso
    )
    dopo = adesso + timedelta(minutes=31)
    social = SocialFinto()
    with usa_archivio(archivio), usa_social(social):
        pubblicazione.pubblica_dovuti(db, dopo)
    assert db.get(Post, post_id).stato == "pubblicato"
    assert len(social.pubblicazioni) == 1
