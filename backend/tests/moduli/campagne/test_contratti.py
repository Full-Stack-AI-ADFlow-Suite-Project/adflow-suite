"""T1-04: stati, transizioni e funzioni comuni del modulo campagne."""
from itertools import product

import pytest
from sqlalchemy import select

from app.core.errori import DatiNonValidi, NonTrovato, StatoNonValido
from app.moduli.campagne import domain
from app.moduli.campagne.models import DecisioneCampagna, GruppoFoto
from app.moduli.campagne.service import (
    aggiorna_foto,
    cambia_stato,
    campagna,
    campagne_in_stato,
    foto_della_campagna,
    registra_decisione,
)
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_in_bozza,
    campagna_in_revisione,
    campagna_inviata,
    foto,
)

# Le transizioni di plan §2, scritte qui una seconda volta apposta:
# il test fallisce se il domain.py si allontana dal piano.
AMMESSE = {
    ("bozza", "inviata"),
    ("inviata", "in_generazione"),
    ("in_generazione", "in_revisione"),
    ("in_revisione", "attiva"),
    ("attiva", "conclusa"),
    ("in_generazione", "generazione_fallita"),
    ("generazione_fallita", "inviata"),
    ("in_revisione", "respinta"),
    ("inviata", "scaduta"),
    ("in_generazione", "scaduta"),
    ("generazione_fallita", "scaduta"),
    ("in_revisione", "scaduta"),
    ("attiva", "sospesa"),
    ("sospesa", "attiva"),
    ("attiva", "annullata"),
    ("sospesa", "annullata"),
}
STATI = (
    "bozza",
    "inviata",
    "in_generazione",
    "generazione_fallita",
    "in_revisione",
    "respinta",
    "scaduta",
    "attiva",
    "sospesa",
    "annullata",
    "conclusa",
)
VIETATE = sorted(set(product(STATI, STATI)) - AMMESSE)


def test_il_domain_ha_gli_stati_e_le_transizioni_del_piano():
    assert set(domain.STATI) == set(STATI)
    nel_domain = {(da, a) for da, verso in domain.TRANSIZIONI.items() for a in verso}
    assert nel_domain == AMMESSE


@pytest.mark.parametrize(("da", "a"), sorted(AMMESSE))
def test_cambia_stato_transizione_ammessa(db, da, a):
    record = campagna_in_bozza(db, stato=da)
    cambia_stato(db, record, a)
    db.expire(record)
    assert record.stato == a


@pytest.mark.parametrize(("da", "a"), VIETATE)
def test_cambia_stato_transizione_vietata(db, da, a):
    record = campagna_in_bozza(db, stato=da)
    with pytest.raises(StatoNonValido):
        cambia_stato(db, record, a)
    assert record.stato == da


def test_cambia_stato_rifiuta_uno_stato_sconosciuto(db):
    record = campagna_in_bozza(db)
    with pytest.raises(StatoNonValido):
        cambia_stato(db, record, "inesistente")


def test_campagna_per_id(db):
    record = campagna_in_bozza(db)
    assert campagna(db, record.id) is record


def test_campagna_inesistente(db):
    with pytest.raises(NonTrovato):
        campagna(db, -1)


def test_foto_della_campagna(db):
    record = campagna_in_bozza(db)
    assert foto_della_campagna(db, record.id) == []
    prima = foto(db, campagna=record)
    seconda = foto(db, campagna=record)
    foto(db)  # di un'altra campagna
    assert foto_della_campagna(db, record.id) == [prima, seconda]


def test_campagne_in_stato(db):
    bozza = campagna_in_bozza(db)
    inviata = campagna_inviata(db)
    attiva = campagna_attiva(db)
    assert campagne_in_stato(db, ["attiva"]) == [attiva]
    assert campagne_in_stato(db, ["bozza", "inviata"]) == [bozza, inviata]
    assert campagne_in_stato(db, ["conclusa"]) == []
    assert campagne_in_stato(db, []) == []


def test_registra_decisione_approvata(db):
    record = campagna_in_revisione(db)
    operatore = utente(db, "operatore")
    registra_decisione(db, record, operatore.id, "approvata", None, None, [])
    decisione = db.scalar(
        select(DecisioneCampagna).where(DecisioneCampagna.campagna_id == record.id)
    )
    assert decisione.esito == "approvata"
    assert decisione.utente_id == operatore.id
    assert decisione.motivo is None
    assert decisione.foto_segnate == []
    assert decisione.creata_il is not None


def test_registra_decisione_non_sostituisce_le_precedenti(db):
    record = campagna_in_revisione(db)
    operatore = utente(db, "operatore")
    immagine = foto_della_campagna(db, record.id)[0]
    registra_decisione(db, record, operatore.id, "rimandata", None, "Ci torno", [])
    registra_decisione(
        db, record, operatore.id, "respinta", "foto", "Foto sfocate", [immagine.id]
    )
    decisioni = db.scalars(
        select(DecisioneCampagna)
        .where(DecisioneCampagna.campagna_id == record.id)
        .order_by(DecisioneCampagna.id)
    ).all()
    assert [d.esito for d in decisioni] == ["rimandata", "respinta"]
    assert decisioni[1].foto_segnate == [immagine.id]


@pytest.mark.parametrize(
    ("esito", "motivo", "nota"),
    [
        ("forse", None, None),
        ("approvata", "antipatia", None),
        ("respinta", None, "Nota senza motivo"),
        ("respinta", "foto", None),
        ("respinta", "altro", "   "),
    ],
)
def test_registra_decisione_dati_non_validi(db, esito, motivo, nota):
    record = campagna_in_revisione(db)
    operatore = utente(db, "operatore")
    with pytest.raises(DatiNonValidi):
        registra_decisione(db, record, operatore.id, esito, motivo, nota, [])


def test_aggiorna_foto(db):
    immagine = foto(db)
    aggiorna_foto(db, immagine.id, {"soggetto": "vaso", "colori": ["blu"]}, 2)
    db.expire(immagine)
    assert immagine.analisi_ai == {"soggetto": "vaso", "colori": ["blu"]}
    assert immagine.n_utilizzi == 2


def test_aggiorna_foto_inesistente(db):
    with pytest.raises(NonTrovato):
        aggiorna_foto(db, -1, None, 0)


def test_le_fabbriche_dall_invio_in_poi_sono_complete(db):
    record = campagna_inviata(db)
    assert set(record.canali) <= {"facebook", "instagram"}
    assert record.frequenza == record.profilo_snapshot["frequenza"]
    assert record.obiettivo == record.profilo_snapshot["obiettivo"]
    assert record.profilo_snapshot["nome"] == "Bottega di prova"
    mazzo = db.scalar(select(GruppoFoto).where(GruppoFoto.campagna_id == record.id))
    assert mazzo.descrizione
    immagini = foto_della_campagna(db, record.id)
    assert len(immagini) == 4
    assert all(i.gruppo_id == mazzo.id for i in immagini)
    assert all(min(i.larghezza, i.altezza) >= 1080 for i in immagini)
