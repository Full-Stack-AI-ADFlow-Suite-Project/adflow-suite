"""Campagne sovrapposte della stessa bottega (T4-103, R-12, R-25, CA-115).

Scenari di §7.3: due campagne sovrapposte della stessa bottega inviate
insieme. `invia_campagna` non genera il piano (lo fa il job con l'AI): qui si
prova che l'invio della bozza e un intervento sull'altra campagna in corso non
si bloccano e che lo stato resta coerente. Il rispetto degli orari occupati
(R-25, CA-115) si gioca nel pianificatore e non è provabile a questo livello:
è dichiarato `non provato` nel report del task.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.moduli.campagne import service
from app.moduli.campagne.models import Campagna
from app.moduli.revisione import interventi
from tests.accettazione.concorrenza.conftest import crea_con_commit, esegui_in_parallelo
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_in_bozza
from tests.moduli.contenuti.fabbrica import post_approvato

RIPETIZIONI = 20


def _due_campagne_sovrapposte(motore, bottega, adesso) -> dict:
    def costruisci(sessione):
        attiva = campagna_attiva(sessione, profilo_id=bottega.id)
        post = post_approvato(
            sessione,
            campagna_id=attiva.id,
            data_ora=adesso + timedelta(minutes=30),
        )
        bozza = campagna_in_bozza(sessione, profilo_id=bottega.id)
        return {"attiva": attiva.id, "post": post.id, "bozza": bozza.id}

    return crea_con_commit(motore, costruisci)


def _stato(motore, campagna_id: int) -> str:
    return crea_con_commit(
        motore,
        lambda s: s.scalar(select(Campagna.stato).where(Campagna.id == campagna_id)),
    )


def test_invio_della_bozza_mentre_si_sposta_un_post_dell_altra(
    motore_concorrenza, mondo_concorrenza
):
    """Invio della bozza e sposta sull'altra campagna insieme: nessuno dei due si blocca."""
    for _ in range(RIPETIZIONI):
        adesso = datetime.now(timezone.utc)
        mondo = _due_campagne_sovrapposte(
            motore_concorrenza, mondo_concorrenza["bottega"], adesso
        )
        utente = mondo_concorrenza["artigiano"].id
        operatore_id = mondo_concorrenza["operatore"].id
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: service.invia_campagna(
                    s, utente, mondo["bozza"], adesso, dichiarazione=True
                ),
                lambda s: interventi.sposta(
                    s,
                    mondo["post"],
                    operatore_id,
                    adesso + timedelta(minutes=45),
                    adesso,
                ),
            ],
        )
        assert errori[0] is None, f"l'invio è stato bloccato: {errori[0]}"
        assert _stato(motore_concorrenza, mondo["bozza"]) == "inviata"
        assert _stato(motore_concorrenza, mondo["attiva"]) == "attiva"


def test_due_botteghe_inviano_insieme(motore_concorrenza, mondo_concorrenza):
    """Due botteghe diverse inviano nello stesso istante: entrambe passano."""
    for _ in range(RIPETIZIONI):
        adesso = datetime.now(timezone.utc)
        bottega_a = crea_con_commit(
            motore_concorrenza,
            lambda s: campagna_in_bozza(
                s, profilo_id=mondo_concorrenza["bottega"].id
            ).id,
        )
        bottega_b = crea_con_commit(
            motore_concorrenza,
            lambda s: campagna_in_bozza(
                s, profilo_id=mondo_concorrenza["bottega2"].id
            ).id,
        )
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: service.invia_campagna(
                    s, mondo_concorrenza["artigiano"].id, bottega_a, adesso, True
                ),
                lambda s: service.invia_campagna(
                    s, mondo_concorrenza["artigiano2"].id, bottega_b, adesso, True
                ),
            ],
        )
        assert errori == [None, None], f"una bottega ha bloccato l'altra: {errori}"
        assert _stato(motore_concorrenza, bottega_a) == "inviata"
        assert _stato(motore_concorrenza, bottega_b) == "inviata"
