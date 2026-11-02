"""Macchina a stati della campagna (T4-104, §6): gli invarianti di §1 reggono.

Le sequenze casuali di `hypothesis` provano le transizioni della campagna con i
suoi invarianti: lo stato resta tra quelli ammessi, una campagna attiva non ha
post da approvare, una respinta ha tutti i post scartati, il numero dei post
non cala mai. Si salta se `hypothesis` non è installato
(requirements-accettazione.txt). Per la corsa lunga:
`pytest --hypothesis-profile=accettazione` (10 000 sequenze).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import settings
from hypothesis.stateful import (
    RuleBasedStateMachine,
    invariant,
    rule,
    run_state_machine_as_test,
)
from sqlalchemy import func, select

from app.core.errori import DatiNonValidi, NonTrovato, StatoNonValido
from app.moduli.campagne.models import Campagna
from app.moduli.contenuti.models import Post
from app.moduli.revisione import decisioni, service, sospensione
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare

STATI_CAMPAGNA = {
    "bozza",
    "inviata",
    "in_generazione",
    "generazione_fallita",
    "in_revisione",
    "respinta",
    "scaduta",
    "attiva",
    "sospesa",
    "conclusa",
    "annullata",
}

# Sequenze della corsa lunga: ACCETTAZIONE_SEQUENZE=10000 pytest ...
SEQUENZE = int(os.environ.get("ACCETTAZIONE_SEQUENZE", "100"))


class MacchinaCampagna(RuleBasedStateMachine):
    """Una campagna in revisione; le regole sono le transizioni della campagna."""

    db = None
    operatore = None

    def __init__(self):
        super().__init__()
        self.campagna_id = None
        self.post_prima = 0

    @rule()
    def crea_campagna(self):
        bottega = profilo(self.db)
        campagna = campagna_in_revisione(self.db, profilo_id=bottega.id)
        post_da_approvare(self.db, campagna_id=campagna.id)
        self.db.flush()
        self.campagna_id = campagna.id
        self.post_prima = self._conta_post()

    @rule()
    def approva(self):
        if self.campagna_id is None:
            return
        self._tenta(
            lambda: service.approva(
                self.db, self.campagna_id, self.operatore, datetime.now(timezone.utc)
            )
        )

    @rule()
    def respingi(self):
        if self.campagna_id is None:
            return
        self._tenta(
            lambda: decisioni.respingi(
                self.db,
                self.campagna_id,
                self.operatore,
                "altro",
                "Nota della respinta",
                [],
                datetime.now(timezone.utc),
            )
        )

    @rule()
    def sospendi(self):
        if self.campagna_id is None:
            return
        self._tenta(
            lambda: sospensione.sospendi(
                self.db, self.campagna_id, self.operatore, None
            )
        )

    @rule()
    def riattiva(self):
        if self.campagna_id is None:
            return
        self._tenta(
            lambda: sospensione.riattiva(
                self.db,
                self.campagna_id,
                self.operatore,
                [],
                datetime.now(timezone.utc),
            )
        )

    def _tenta(self, azione):
        """Un'azione rifiutata (409/422/404) è un esito ammesso: non fa fallire la sequenza."""
        try:
            with self.db.begin_nested():
                azione()
        except (StatoNonValido, DatiNonValidi, NonTrovato):
            pass

    def _campagna(self) -> Campagna | None:
        return self.db.get(Campagna, self.campagna_id)

    def _conta_post(self) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(Post)
            .where(Post.campagna_id == self.campagna_id)
        )

    @invariant()
    def stato_ammesso(self):
        if self.campagna_id is None:
            return
        assert self._campagna().stato in STATI_CAMPAGNA

    @invariant()
    def attiva_senza_post_da_approvare(self):
        if self.campagna_id is None:
            return
        if self._campagna().stato == "attiva":
            da_approvare = self.db.scalar(
                select(func.count())
                .select_from(Post)
                .where(
                    Post.campagna_id == self.campagna_id, Post.stato == "da_approvare"
                )
            )
            assert da_approvare == 0, "campagna attiva con un post da approvare"

    @invariant()
    def respinta_tutti_scartati(self):
        if self.campagna_id is None:
            return
        if self._campagna().stato == "respinta":
            altri = self.db.scalar(
                select(func.count())
                .select_from(Post)
                .where(Post.campagna_id == self.campagna_id, Post.stato != "scartato")
            )
            assert altri == 0, "campagna respinta con un post non scartato"

    @invariant()
    def i_post_non_calano(self):
        if self.campagna_id is None or self.post_prima == 0:
            return
        assert self._conta_post() == self.post_prima, "il numero dei post è calato"


def test_macchina_campagna(db, utente_di_prova):
    """Sequenze casuali di transizioni della campagna, con gli invarianti (T4-104)."""
    MacchinaCampagna.db = db
    MacchinaCampagna.operatore = utente_di_prova("operatore")
    run_state_machine_as_test(
        MacchinaCampagna, settings=settings(max_examples=SEQUENZE, deadline=None)
    )
