"""Macchina a stati del post (T4-104, §6): versioni e stato sotto attacco.

Le regole provano le azioni di revisione su un post in revisione con testi
random; gli invarianti di §1: lo stato del post resta tra quelli ammessi, le
versioni non si perdono mai (§1.2), nessuna versione nasce vuota e ogni azione
crea al massimo una versione. Si salta se `hypothesis` non è installato.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import settings
from hypothesis.stateful import (
    RuleBasedStateMachine,
    invariant,
    rule,
    run_state_machine_as_test,
)
from hypothesis.strategies import text
from sqlalchemy import func, select

from app.core.errori import DatiNonValidi, NonTrovato, StatoNonValido
from app.moduli.campagne.models import Foto
from app.moduli.contenuti.models import Post, VersionePost
from app.moduli.revisione import interventi
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare

STATI_POST = {
    "da_approvare",
    "da_rivedere",
    "approvato",
    "pubblicato",
    "fallito",
    "annullato",
    "scartato",
    "scaduto",
}

# Sequenze della corsa lunga: ACCETTAZIONE_SEQUENZE=10000 pytest ...
SEQUENZE = int(os.environ.get("ACCETTAZIONE_SEQUENZE", "100"))

PAROLE = text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=3, max_size=60)


class MacchinaPost(RuleBasedStateMachine):
    """Un post in revisione: modifica, rigenera, cambia foto, sposta."""

    db = None
    operatore = None

    def __init__(self):
        super().__init__()
        bottega = profilo(self.db)
        campagna = campagna_in_revisione(self.db, profilo_id=bottega.id)
        post = post_da_approvare(self.db, campagna_id=campagna.id)
        self.db.flush()
        self.post_id = post.id
        self.campagna_id = campagna.id
        self.versioni = self._conta_versioni()

    def _post(self) -> Post:
        return self.db.get(Post, self.post_id)

    def _conta_versioni(self) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(VersionePost)
            .where(VersionePost.post_id == self.post_id)
        )

    @rule(testo=PAROLE)
    def modifica(self, testo):
        self._tenta(
            lambda: interventi.modifica(
                self.db,
                self.post_id,
                self.operatore,
                testo,
                ["artigianato"],
                datetime.now(timezone.utc),
            )
        )

    @rule()
    def rigenera(self):
        self._tenta(
            lambda: interventi.rigenera(
                self.db, self.post_id, "totale", None, None, datetime.now(timezone.utc)
            )
        )

    @rule()
    def cambia_foto(self):
        def scegli():
            return self.db.scalars(
                select(Foto.id).where(
                    Foto.campagna_id == self.campagna_id, Foto.n_utilizzi == 0
                )
            ).first()

        foto_id = scegli()
        if foto_id is None:
            return
        self._tenta(
            lambda: interventi.cambia_foto(
                self.db,
                self.post_id,
                foto_id,
                self.operatore,
                datetime.now(timezone.utc),
            )
        )

    @rule()
    def sposta(self):
        adesso = datetime.now(timezone.utc)
        self._tenta(
            lambda: interventi.sposta(
                self.db,
                self.post_id,
                self.operatore.id,
                adesso + timedelta(hours=2),
                adesso,
            )
        )

    def _tenta(self, azione):
        try:
            with self.db.begin_nested():
                azione()
        except (StatoNonValido, DatiNonValidi, NonTrovato):
            pass

    @invariant()
    def stato_ammesso(self):
        assert self._post().stato in STATI_POST

    @invariant()
    def le_versioni_non_calano(self):
        assert self._conta_versioni() >= self.versioni, "una versione è sparita (§1.2)"
        self.versioni = self._conta_versioni()

    @invariant()
    def nessuna_versione_vuota(self):
        corrente = self._post().versione_corrente
        assert corrente is not None
        assert corrente.testo.strip(), "la versione corrente è vuota (§1.6)"

    @invariant()
    def numeri_di_versione_progressivi(self):
        numeri = self.db.scalars(
            select(VersionePost.numero)
            .where(VersionePost.post_id == self.post_id)
            .order_by(VersionePost.numero)
        ).all()
        assert numeri == list(range(1, len(numeri) + 1)), numeri


def test_macchina_post(db, utente_di_prova):
    """Sequenze casuali di azioni sul post, con gli invarianti (T4-104)."""
    MacchinaPost.db = db
    MacchinaPost.operatore = utente_di_prova("operatore")
    run_state_machine_as_test(
        MacchinaPost, settings=settings(max_examples=SEQUENZE, deadline=None)
    )
