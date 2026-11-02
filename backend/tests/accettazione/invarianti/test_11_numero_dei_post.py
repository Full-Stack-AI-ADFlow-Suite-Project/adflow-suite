"""§1.11 — Ogni azione di revisione e ogni intervento: il numero dei post non cala.

Attacco di §4.3: modifica, rigenera, cambia foto, sposta e respingi non
tolgono post; i post calano solo con un canale tolto, con la scadenza o, dopo
l'approvazione, con l'annullamento di un post (spec R-16, R-33).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.moduli.campagne.models import Campagna
from app.moduli.contenuti.models import Post
from app.moduli.revisione import decisioni, interventi
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare


def _conta(db) -> int:
    return db.scalar(select(func.count()).select_from(Post))


def test_le_azioni_di_revisione_non_tolgono_post(db, utente_di_prova):
    """Modifica, rigenera, cambia foto, sposta, respingi: i post restano tutti."""
    artigiano = utente_di_prova("artigiano")
    operatore = utente_di_prova("operatore")
    bottega = profilo(db, utente_id=artigiano.id)
    oggi = datetime.now(timezone.utc).date()
    campagna = campagna_in_revisione(
        db,
        profilo_id=bottega.id,
        inizio=oggi,
        fine=oggi + timedelta(days=30),
    )
    primo = post_da_approvare(db, campagna_id=campagna.id)
    secondo = post_da_approvare(db, campagna_id=campagna.id)
    db.flush()
    adesso = datetime.now(timezone.utc)
    prima = _conta(db)

    interventi.modifica(
        db,
        primo.id,
        operatore,
        "Testo nuovo per il primo post",
        ["artigianato"],
        adesso,
    )
    interventi.rigenera(db, secondo.id, "totale", None, None, adesso)
    interventi.sposta(
        db, primo.id, operatore.id, adesso + timedelta(minutes=30), adesso
    )
    assert _conta(db) == prima, "un'azione di revisione ha tolto un post"

    decisioni.respingi(
        db, campagna.id, operatore, "foto", "Foto non della bottega", [], adesso
    )
    assert _conta(db) == prima, "la respinta ha cancellato post invece di scartarli"
    assert (
        db.scalar(
            select(func.count()).select_from(Post).where(Post.stato == "scartato")
        )
        == 2
    )


def test_togliere_un_canale_toglie_i_suoi_post_e_lascia_gli_altri(db, utente_di_prova):
    """Il caso ammesso: togli un canale → i post di quel canale spariscono (R-18)."""
    artigiano = utente_di_prova("artigiano")
    operatore = utente_di_prova("operatore")
    bottega = profilo(db, utente_id=artigiano.id, canali=["facebook", "instagram"])
    campagna = campagna_in_revisione(
        db, profilo_id=bottega.id, canali=["facebook", "instagram"]
    )
    post_da_approvare(db, campagna_id=campagna.id, canale="facebook")
    post_da_approvare(db, campagna_id=campagna.id, canale="instagram")
    db.flush()
    assert _conta(db) == 2

    decisioni.togli_canale(
        db,
        campagna.id,
        operatore,
        "facebook",
        "Il canale non serve",
        datetime.now(timezone.utc),
    )
    rimasti = db.scalars(
        select(Post.canale).where(Post.campagna_id == campagna.id)
    ).all()
    assert sorted(rimasti) == [
        "facebook",
        "instagram",
    ], "niente si cancella: i post scartati restano in tabella (§1.2)"
    ancora_vivi = db.scalars(
        select(Post.canale).where(
            Post.campagna_id == campagna.id, Post.stato != "scartato"
        )
    ).all()
    assert ancora_vivi == ["instagram"], "il canale tolto ha lasciato post pubblicabili"
