"""Pubblicazione concorrente (T4-103, costituzione §1.7, guasto D-07).

Scenari di §7.3:
- due worker (tick) sullo stesso database, con lo stesso post dovuto: il post
  **non** deve uscire due volte (blocco assoluto della §8);
- annulla di un post mentre il tick lo pubblica: al massimo uno dei due passa,
  e lo stato finale resta coerente.

Il social è il finto, che registra in ``pubblicazioni`` ogni chiamata: è la
prova che conta, perché su Meta una seconda chiamata sarebbe un secondo post.
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

import pytest
from PIL import Image
from sqlalchemy import func, select

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.adapters.social import SocialFinto, usa_social
from app.moduli.campagne.models import Campagna, Foto
from app.moduli.contenuti.models import Post
from app.moduli.pubblicazione import service as pubblicazione
from app.moduli.pubblicazione.models import Pubblicazione
from app.moduli.revisione import interventi
from tests.accettazione.concorrenza.conftest import crea_con_commit, esegui_in_parallelo
from tests.moduli.campagne.fabbrica import campagna_attiva
from tests.moduli.contenuti.fabbrica import post_approvato

RIPETIZIONI = 50


def _jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (1080, 1350), (40, 90, 60)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _post_dovuto(motore, bottega, adesso, archivio: ArchivioDisco, minuti: int) -> dict:
    """Campagna attiva con un post approvato che esce tra `minuti` minuti."""

    def costruisci(sessione):
        campagna = campagna_attiva(sessione, profilo_id=bottega.id)
        post = post_approvato(
            sessione,
            campagna_id=campagna.id,
            data_ora=adesso + timedelta(minutes=minuti),
        )
        versione = post.versione_corrente
        for legame in versione.legami_foto:
            immagine = sessione.get(Foto, legame.foto_id)
            immagine.file = archivio.salva(_jpeg(), "jpg")
        return {"campagna": campagna.id, "post": post.id}

    return crea_con_commit(motore, costruisci)


def _stato_post(motore, post_id: int) -> str:
    return crea_con_commit(
        motore, lambda s: s.scalar(select(Post.stato).where(Post.id == post_id))
    )


@pytest.fixture
def archivio_e_social(tmp_path):
    archivio = ArchivioDisco(tmp_path)
    social = SocialFinto()
    with usa_archivio(archivio), usa_social(social):
        yield archivio, social


def test_due_worker_pubblicano_lo_stesso_post(
    motore_concorrenza, mondo_concorrenza, archivio_e_social
):
    """50 volte: due tick insieme, il social riceve **una** sola chiamata (§1.7)."""
    archivio, social = archivio_e_social
    doppie = 0
    esiti = {}
    for _ in range(RIPETIZIONI):
        adesso = datetime.now(timezone.utc)
        mondo = _post_dovuto(
            motore_concorrenza,
            mondo_concorrenza["bottega"],
            adesso,
            archivio,
            minuti=-1,
        )
        social.pubblicazioni.clear()
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: pubblicazione.pubblica_dovuti(s, adesso),
                lambda s: pubblicazione.pubblica_dovuti(s, adesso),
            ],
        )
        if len(social.pubblicazioni) > 1:
            doppie += 1
        esiti[tuple(type(e).__name__ if e else "ok" for e in errori)] = (
            esiti.get(tuple(type(e).__name__ if e else "ok" for e in errori), 0) + 1
        )
        # in ogni caso, una sola riga `ok` (indice unico parziale) e post uscito
        ok = crea_con_commit(
            motore_concorrenza,
            lambda s: s.scalar(
                select(func.count())
                .select_from(Pubblicazione)
                .where(
                    Pubblicazione.post_id == mondo["post"],
                    Pubblicazione.stato == "ok",
                )
            ),
        )
        assert ok == 1, f"righe ok per il post: {ok}"
        assert _stato_post(motore_concorrenza, mondo["post"]) == "pubblicato"
    assert doppie == 0, (
        f"il social ha ricevuto più di una chiamata per lo stesso post in "
        f"{doppie}/{RIPETIZIONI} ripetizioni (esiti: {esiti}): doppia pubblicazione"
    )


def test_annulla_un_post_mentre_il_tick_lo_pubblica(
    motore_concorrenza, mondo_concorrenza, archivio_e_social
):
    """Post dovuto adesso: annulla prende 409, il tick pubblica una volta sola."""
    archivio, social = archivio_e_social
    for _ in range(RIPETIZIONI):
        adesso = datetime.now(timezone.utc)
        mondo = _post_dovuto(
            motore_concorrenza,
            mondo_concorrenza["bottega"],
            adesso,
            archivio,
            minuti=-1,
        )
        social.pubblicazioni.clear()
        operatore_id = mondo_concorrenza["operatore"].id
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: pubblicazione.pubblica_dovuti(s, adesso),
                lambda s: interventi.annulla(
                    s, mondo["post"], operatore_id, "Da non pubblicare", adesso
                ),
            ],
        )
        assert errori[0] is None, f"il tick è fallito: {errori[0]}"
        assert (
            errori[1] is not None
        ), "annulla su un post in uscita è passato: R-16 violata"
        assert len(social.pubblicazioni) == 1
        assert _stato_post(motore_concorrenza, mondo["post"]) == "pubblicato"


def test_annulla_un_post_che_esce_tra_venti_minuti(
    motore_concorrenza, mondo_concorrenza, archivio_e_social
):
    """Post non dovuto: annulla passa (esce tra più di 15 minuti), il tick non tocca nulla."""
    archivio, social = archivio_e_social
    for _ in range(RIPETIZIONI):
        adesso = datetime.now(timezone.utc)
        mondo = _post_dovuto(
            motore_concorrenza,
            mondo_concorrenza["bottega"],
            adesso,
            archivio,
            minuti=20,
        )
        social.pubblicazioni.clear()
        operatore_id = mondo_concorrenza["operatore"].id
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: pubblicazione.pubblica_dovuti(s, adesso),
                lambda s: interventi.annulla(
                    s, mondo["post"], operatore_id, "Da non pubblicare", adesso
                ),
            ],
        )
        assert errori[1] is None, f"annulla è fallito: {errori[1]}"
        assert (
            len(social.pubblicazioni) == 0
        ), "il tick ha pubblicato un post non dovuto"
        assert _stato_post(motore_concorrenza, mondo["post"]) == "annullato"
