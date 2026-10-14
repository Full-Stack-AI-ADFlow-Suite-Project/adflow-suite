"""``campagne_di()``, ``togli_canale()`` (congelato) e ``ultima_nota()`` di campagne (plan §6)."""

from datetime import date

import pytest

from app.core.errori import DatiNonValidi, StatoNonValido
from app.moduli.campagne.service import (
    campagne_di,
    registra_decisione,
    togli_canale,
    ultima_nota,
)
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza, campagna_inviata


def test_campagne_di_tutte_o_per_stato_dalla_piu_recente(db):
    bottega = profilo(db)
    vecchia = campagna_in_bozza(db, profilo_id=bottega.id, inizio=date(2030, 1, 1))
    recente = campagna_inviata(db, profilo_id=bottega.id, inizio=date(2030, 3, 1))
    altrui = campagna_inviata(db)

    tutte = campagne_di(db, bottega.id)
    assert [c.id for c in tutte] == [recente.id, vecchia.id]
    assert altrui.id not in {c.id for c in tutte}

    assert [c.id for c in campagne_di(db, bottega.id, stati=["inviata"])] == [
        recente.id
    ]
    assert campagne_di(db, bottega.id, stati=["attiva"]) == []
    assert campagne_di(db, 99999) == []


def test_togli_canale_va_in_canali_tolti_e_non_torna(db):
    bottega = profilo(db, canali=["instagram", "facebook"])
    campagna = campagna_inviata(db, profilo_id=bottega.id)

    togli_canale(db, campagna, "instagram")
    assert campagna.canali_tolti == ["instagram"]
    # Toglierlo una seconda volta non cambia niente.
    togli_canale(db, campagna, "instagram")
    assert campagna.canali_tolti == ["instagram"]


def test_togli_canale_fuori_dalla_campagna_422(db):
    campagna = campagna_inviata(db)

    with pytest.raises(DatiNonValidi):
        togli_canale(db, campagna, "tiktok")


def test_togli_lultimo_canale_409_ca53(db):
    bottega = profilo(db, canali=["instagram", "facebook"])
    campagna = campagna_inviata(db, profilo_id=bottega.id)

    togli_canale(db, campagna, "instagram")
    with pytest.raises(StatoNonValido):
        togli_canale(db, campagna, "facebook")
    assert campagna.canali_tolti == ["instagram"]


def test_ultima_nota_la_piu_recente_o_nessuna(db):
    campagna = campagna_inviata(db)
    operatore = utente(db, "operatore")

    assert ultima_nota(db, campagna.id) is None

    registra_decisione(db, campagna, operatore.id, "approvata", None, None, [])
    assert ultima_nota(db, campagna.id) is None

    registra_decisione(db, campagna, operatore.id, "nota", None, "Prima nota", [])
    registra_decisione(db, campagna, operatore.id, "nota", None, "Seconda nota", [])
    assert ultima_nota(db, campagna.id).nota == "Seconda nota"
