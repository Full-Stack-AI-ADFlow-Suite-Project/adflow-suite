"""§1.7 — Pubblicazione idempotente: il tentativo si registra prima del social.

Attacchi di §4.3: riprogramma dopo un `ok`; processo ucciso dopo la risposta di
Meta e prima del commit (D-07); due worker sullo stesso database (coperto in
`tests/accettazione/concorrenza/test_pubblicazione.py`).
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

import pytest
from PIL import Image
from sqlalchemy import select

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.adapters.social import SocialFinto, usa_social
from app.moduli.campagne.models import Foto
from app.moduli.contenuti import service as contenuti
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


@pytest.mark.xfail(
    strict=True,
    reason="RL-025 (D-07, costituzione §1.7): il tentativo di pubblicazione è "
    "registrato nella stessa transazione del commit; se il processo muore dopo "
    "la risposta del social e prima del commit, il tentativo si perde e il tick "
    "successivo ripubblica: doppia pubblicazione su Meta (blocco assoluto §8). "
    "Correzione proposta: commit del tentativo prima della chiamata al social",
)
def test_il_tentativo_si_registra_prima_della_chiamata_al_social(
    db, utente_di_prova, tmp_path, monkeypatch
):
    """Se il social risponde ma il processo muore prima del commit, che cosa succede?

    Il tentativo è registrato **nella stessa transazione** del commit: una morte
    del processo prima del commit lo cancella, e il tick successivo ripubblica.
    Questo è il caso D-07 di `accettazione-post-mvp.md`: qui il test lo prova.
    """
    archivio = ArchivioDisco(tmp_path)
    social = SocialFinto()
    adesso = datetime.now(timezone.utc)
    with usa_archivio(archivio):
        mondo = _post_dovuto(db, utente_di_prova("artigiano"), archivio, adesso)

    def esplode(*_argomenti, **_campi):
        raise RuntimeError("il processo muore dopo la risposta del social")

    salvataggio = db.begin_nested()
    with usa_archivio(archivio), usa_social(social), monkeypatch.context() as patch:
        patch.setattr(contenuti, "segna_esito", esplode)
        with pytest.raises(RuntimeError):
            pubblicazione.pubblica_dovuti(db, adesso)
    assert len(social.pubblicazioni) == 1
    salvataggio.rollback()  # come un processo morto prima del commit

    # il worker riparte: trova il post ancora dovuto
    with usa_archivio(archivio), usa_social(social):
        pubblicazione.pubblica_dovuti(db, adesso)
    assert len(social.pubblicazioni) == 1, (
        "dopo un processo morto dopo la risposta di Meta il post è uscito di "
        "nuovo: doppia pubblicazione (D-07)"
    )
