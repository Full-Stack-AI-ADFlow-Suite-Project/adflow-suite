"""RT-05: i campi della corsia del ritocco sono vuoti sulle righe di prima."""
from sqlalchemy import select

from app.moduli.contenuti.models import VersionePostFoto
from tests.moduli.contenuti.fabbrica import chiamata_ai, post_approvato


def test_legame_senza_ritocco_ne_render(db):
    post_approvato(db)
    legame = db.scalars(select(VersionePostFoto)).first()
    assert legame is not None
    assert legame.ritocco is None
    assert legame.render is None


def test_legame_salva_ritocco_e_render(db):
    post_approvato(db)
    legame = db.scalars(select(VersionePostFoto)).first()
    legame.ritocco = {"variante": "standard", "privacy": []}
    legame.render = "a" * 64
    db.flush()
    db.expire(legame)
    assert legame.ritocco == {"variante": "standard", "privacy": []}
    assert legame.render == "a" * 64


def test_chiamata_ai_senza_token_in_cache(db):
    assert chiamata_ai(db).token_in_cache is None
    assert chiamata_ai(db, token_in_cache=900).token_in_cache == 900
