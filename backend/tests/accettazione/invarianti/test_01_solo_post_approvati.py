"""§1.1 — Si pubblica solo un post approvato; si approva la campagna intera.

Attacchi di §4.3: approvare con un post `da_rivedere`; far uscire un post non
approvato forzando lo stato; approvare due volte in parallelo (R-03). Il terzo
è in `tests/accettazione/concorrenza/test_approvazione.py` (RL-021): qui i
primi due.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.adapters.social import SocialFinto, usa_social
from app.core.errori import StatoNonValido
from app.moduli.contenuti.models import Post
from app.moduli.pubblicazione import service as pubblicazione
from app.moduli.revisione import service
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_approvato, post_da_approvare


def test_approvare_con_un_post_da_rivedere_e_rifiutato(db, utente_di_prova):
    """R-14: un post `da_rivedere` blocca approva (409), nessun post si muove."""
    operatore = utente_di_prova("operatore")
    campagna = campagna_in_revisione(db, profilo_id=profilo(db).id)
    post_da_approvare(db, campagna_id=campagna.id)
    post_da_approvare(db, campagna_id=campagna.id, stato="da_rivedere")
    db.flush()

    with pytest.raises(StatoNonValido):
        service.approva(db, campagna.id, operatore, datetime.now(timezone.utc))

    stati = set(
        db.scalars(select(Post.stato).where(Post.campagna_id == campagna.id)).all()
    )
    assert "approvato" not in stati, "un post è stato approvato lo stesso"


def test_il_tick_non_pubblica_un_post_non_approvato(db):
    """R-01: il tick guarda lo stato; un `da_approvare` dovuto non esce."""
    social = SocialFinto()
    adesso = datetime.now(timezone.utc)
    campagna = campagna_attiva(db, profilo_id=profilo(db).id)
    post = post_da_approvare(
        db,
        campagna_id=campagna.id,
        data_ora=adesso - timedelta(minutes=5),
    )
    db.flush()
    with usa_social(social):
        pubblicazione.pubblica_dovuti(db, adesso)
    assert social.pubblicazioni == []
    assert post.stato == "da_approvare"
