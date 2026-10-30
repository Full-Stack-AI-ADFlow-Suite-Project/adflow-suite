"""Timeout dopo che Meta ha pubblicato (T4-105, D-07): il caso insidioso.

L'adattatore che risponde «temporaneo» dopo aver pubblicato davvero: il tick
non può sapere che il post è uscito e riprova. Il test documenta **com'è oggi**
(come chiede il brief di T4-105): ogni riprova è un post pubbblicato sulla
pagina, fino a `TENTATIVI_MAX`; poi il post è `fallito`, riprogrammabile.
La protezione vera (chiave di idempotenza lato Meta) non c'è: è il rilievo
RL-025 (D-07) del registro.
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

from PIL import Image

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.adapters.social.base import EsitoPubblicazione, SocialAdapter
from app.adapters.social import usa_social
from app.moduli.campagne.models import Foto
from app.moduli.contenuti.models import Post
from app.moduli.pubblicazione import service as pubblicazione
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva
from tests.moduli.contenuti.fabbrica import post_approvato


class SocialChePubblicaPoiVaInTimeout(SocialAdapter):
    """Pubblica (registra la chiamata) e poi risponde «temporaneo»."""

    def __init__(self) -> None:
        self.pubblicazioni: list[dict] = []

    def pubblica(self, canale, testo, hashtag, foto, url_foto):
        self.pubblicazioni.append({"canale": canale, "testo": testo})
        return EsitoPubblicazione(
            ok=False,
            errore="Timeout dopo la pubblicazione",
            tipo_errore="temporaneo",
        )


def test_il_timeout_dopo_la_pubblicazione_ripete_il_post(db, utente_di_prova, tmp_path):
    """Documenta D-07: tre chiamate al social, tutte «uscite», poi `fallito`."""
    utente = utente_di_prova("artigiano")
    archivio = ArchivioDisco(tmp_path)
    adesso = datetime.now(timezone.utc)
    with usa_archivio(archivio):
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
        Image.new("RGB", (1080, 1350), (10, 40, 90)).save(buffer, format="JPEG")
        for legame in post.versione_corrente.legami_foto:
            immagine = db.get(Foto, legame.foto_id)
            immagine.file = archivio.salva(buffer.getvalue(), "jpg")
        db.flush()

    social = SocialChePubblicaPoiVaInTimeout()
    with usa_archivio(archivio), usa_social(social):
        for _ in range(pubblicazione.TENTATIVI_MAX):
            pubblicazione.pubblica_dovuti(db, adesso)

    assert db.get(Post, post.id).stato == "fallito"
    assert len(social.pubblicazioni) == pubblicazione.TENTATIVI_MAX, (
        "il numero di pubblicazioni vere dipende dai riprova: qui sono "
        f"{len(social.pubblicazioni)} (D-07, RL-025)"
    )
