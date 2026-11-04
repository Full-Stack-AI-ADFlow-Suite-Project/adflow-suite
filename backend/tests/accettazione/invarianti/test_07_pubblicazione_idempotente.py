"""§1.7 — Pubblicazione idempotente: il tentativo si registra prima del social.

Attacchi di §4.3: riprogramma dopo un `ok`; processo ucciso dopo la risposta di
Meta e prima del commit (D-07); due worker sullo stesso database (coperto in
`tests/accettazione/concorrenza/test_pubblicazione.py`).
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

from PIL import Image
from sqlalchemy import select

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.adapters.social import SocialFinto, usa_social
from app.adapters.social.base import EsitoPubblicazione, SocialAdapter
from app.moduli.campagne.models import Foto
from app.moduli.contenuti.models import Post
from app.moduli.notifiche.models import Notifica
from app.moduli.pubblicazione.models import Pubblicazione
from app.moduli.pubblicazione import service as pubblicazione
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva
from tests.moduli.contenuti.fabbrica import post_approvato


def _post_dovuto(db, utente, archivio: ArchivioDisco, adesso) -> dict:
    bottega = profilo(db, utente_id=utente.id)
    campagna = campagna_attiva(db, profilo_id=bottega.id)
    post = post_approvato(
        db,
        campagna_id=campagna.id,
        data_ora=adesso - timedelta(minutes=1),
    )
    buffer = io.BytesIO()
    Image.new("RGB", (1080, 1350), (20, 70, 40)).save(buffer, format="JPEG")
    for legame in post.versione_corrente.legami_foto:
        immagine = db.get(Foto, legame.foto_id)
        immagine.file = archivio.salva(buffer.getvalue(), "jpg")
    db.flush()
    return {"campagna": campagna.id, "post": post.id}


def test_dopo_un_ok_il_tick_non_ripubblica(db, utente_di_prova, tmp_path):
    """Un post con una riga `ok` non torna al social al tick successivo."""
    archivio = ArchivioDisco(tmp_path)
    social = SocialFinto()
    adesso = datetime.now(timezone.utc)
    with usa_archivio(archivio):
        _post_dovuto(db, utente_di_prova("artigiano"), archivio, adesso)
    with usa_archivio(archivio), usa_social(social):
        pubblicazione.pubblica_dovuti(db, adesso)
        assert len(social.pubblicazioni) == 1
        pubblicazione.pubblica_dovuti(db, adesso)
    assert len(social.pubblicazioni) == 1, "il post è uscito due volte dopo un ok"


def _tentativo(db, post_id: int) -> Pubblicazione:
    return db.scalar(select(Pubblicazione).where(Pubblicazione.post_id == post_id))


def test_il_tentativo_si_registra_prima_della_chiamata_al_social(
    db, utente_di_prova, tmp_path
):
    """RL-025 (D-07): il processo muore dopo la risposta di Meta, prima dell'esito.

    Il worker conferma il tentativo e `chiamata_il` (commit) *prima* di chiamare
    il social; qui il commit è un `flush` e la morte è «non chiamare
    `registra_esito`». Il tick dopo non richiama il social: segna il post
    `fallito` e avvisa.
    """
    archivio = ArchivioDisco(tmp_path)
    social = SocialFinto()
    adesso = datetime.now(timezone.utc)
    utente_di_prova("operatore")  # destinatario della notifica
    with usa_archivio(archivio):
        mondo = _post_dovuto(db, utente_di_prova("artigiano"), archivio, adesso)

    with usa_archivio(archivio), usa_social(social):
        (tentativo_id,) = pubblicazione.prepara_tentativi(db, adesso)
        richiesta = pubblicazione.avvia_chiamata(db, tentativo_id, adesso)
        pubblicazione.chiama_social(richiesta)
        # il processo muore qui: `registra_esito` non arriva mai

        # il worker riparte: stessa situazione del database, tick nuovo
        pubblicazione.pubblica_dovuti(db, adesso)

    assert len(social.pubblicazioni) == 1, "il social è stato richiamato: doppio post"
    assert db.get(Post, mondo["post"]).stato == "fallito"
    tentativo = _tentativo(db, mondo["post"])
    assert tentativo.stato == "errore"
    assert tentativo.errore == pubblicazione.ERRORE_ESITO_SCONOSCIUTO
    assert "controlla la pagina" in tentativo.errore
    notifica = db.scalar(
        select(Notifica).where(
            Notifica.tipo == "post_fallito", Notifica.post_id == mondo["post"]
        )
    )
    assert notifica is not None


def test_morte_tra_il_commit_di_chiamata_il_e_la_chiamata_al_social(
    db, utente_di_prova, tmp_path
):
    """Il social non è nemmeno partito: nel dubbio non si pubblica, si segnala."""
    archivio = ArchivioDisco(tmp_path)
    social = SocialFinto()
    adesso = datetime.now(timezone.utc)
    with usa_archivio(archivio):
        mondo = _post_dovuto(db, utente_di_prova("artigiano"), archivio, adesso)

    with usa_archivio(archivio), usa_social(social):
        (tentativo_id,) = pubblicazione.prepara_tentativi(db, adesso)
        assert pubblicazione.avvia_chiamata(db, tentativo_id, adesso) is not None
        assert _tentativo(db, mondo["post"]).chiamata_il is not None
        # morte: né `chiama_social` né `registra_esito`
        pubblicazione.pubblica_dovuti(db, adesso)

    assert social.pubblicazioni == []
    assert db.get(Post, mondo["post"]).stato == "fallito"
    assert (
        _tentativo(db, mondo["post"]).errore == pubblicazione.ERRORE_ESITO_SCONOSCIUTO
    )


def test_morte_prima_di_chiamata_il_il_tick_dopo_pubblica(
    db, utente_di_prova, tmp_path
):
    """Morte dopo la prima fase e prima di `chiamata_il`: nulla è partito, si pubblica."""
    archivio = ArchivioDisco(tmp_path)
    social = SocialFinto()
    adesso = datetime.now(timezone.utc)
    with usa_archivio(archivio):
        mondo = _post_dovuto(db, utente_di_prova("artigiano"), archivio, adesso)

    with usa_archivio(archivio), usa_social(social):
        pubblicazione.prepara_tentativi(db, adesso)  # poi il processo muore
        pubblicazione.pubblica_dovuti(db, adesso)

    assert len(social.pubblicazioni) == 1
    assert db.get(Post, mondo["post"]).stato == "pubblicato"


class SocialTemporaneoPoiOk(SocialAdapter):
    """Risponde «temporaneo» `errori` volte, poi pubblica."""

    def __init__(self, errori: int) -> None:
        self.errori = errori
        self.chiamate = 0

    def pubblica(self, canale, testo, hashtag, foto, url_foto):
        self.chiamate += 1
        if self.chiamate <= self.errori:
            return EsitoPubblicazione(
                ok=False, errore="Meta occupato", tipo_errore="temporaneo"
            )
        return EsitoPubblicazione(ok=True, id_esterno="post-1")


def test_un_errore_temporaneo_riprova_ancora(db, utente_di_prova, tmp_path):
    """Un esito ricevuto, anche temporaneo, azzera `chiamata_il`: il tick dopo riprova."""
    archivio = ArchivioDisco(tmp_path)
    social = SocialTemporaneoPoiOk(errori=1)
    adesso = datetime.now(timezone.utc)
    with usa_archivio(archivio):
        mondo = _post_dovuto(db, utente_di_prova("artigiano"), archivio, adesso)

    with usa_archivio(archivio), usa_social(social):
        pubblicazione.pubblica_dovuti(db, adesso)
        tentativo = _tentativo(db, mondo["post"])
        assert tentativo.stato == "in_corso"
        assert tentativo.chiamata_il is None
        assert db.get(Post, mondo["post"]).stato == "approvato"

        pubblicazione.pubblica_dovuti(db, adesso)

    assert social.chiamate == 2
    assert db.get(Post, mondo["post"]).stato == "pubblicato"
    assert _tentativo(db, mondo["post"]).chiamata_il is None
