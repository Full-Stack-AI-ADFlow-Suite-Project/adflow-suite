"""T1-04: stati, transizioni e funzioni comuni del modulo contenuti."""
from datetime import datetime, timedelta, timezone
from itertools import product

import pytest
from sqlalchemy import select

from app.core.errori import DatiNonValidi, StatoNonValido
from app.core.transizioni import verifica_transizione
from app.moduli.campagne.service import cambia_stato, foto_della_campagna
from app.moduli.contenuti import domain
from app.moduli.contenuti.models import VersionePost, VersionePostFoto
from app.moduli.contenuti.service import (
    approva_post,
    ha_blocchi,
    post_della_campagna,
    post_dovuti,
    segna_esito,
    tutti_chiusi,
)
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_approvato, post_da_approvare

# Le transizioni di plan §2, scritte qui una seconda volta apposta.
AMMESSE = {
    ("da_approvare", "approvato"),
    ("approvato", "pubblicato"),
    ("approvato", "fallito"),
    ("approvato", "annullato"),
    ("fallito", "approvato"),
    ("da_approvare", "scaduto"),
    ("da_approvare", "scartato"),
}
STATI = (
    "da_approvare",
    "approvato",
    "pubblicato",
    "fallito",
    "scaduto",
    "scartato",
    "annullato",
)
VIETATE = sorted(set(product(STATI, STATI)) - AMMESSE)
SCADENZA = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)


def test_il_domain_ha_gli_stati_e_le_transizioni_del_piano():
    assert set(domain.STATI) == set(STATI)
    nel_domain = {(da, a) for da, verso in domain.TRANSIZIONI.items() for a in verso}
    assert nel_domain == AMMESSE
    assert "da_rivedere" not in domain.STATI


@pytest.mark.parametrize(("da", "a"), sorted(AMMESSE))
def test_transizione_del_post_ammessa(da, a):
    verifica_transizione(domain.TRANSIZIONI, da, a)


@pytest.mark.parametrize(("da", "a"), VIETATE)
def test_transizione_del_post_vietata(da, a):
    with pytest.raises(StatoNonValido):
        verifica_transizione(domain.TRANSIZIONI, da, a)


def test_post_della_campagna_con_versione_corrente_e_storico(db):
    campagna = campagna_in_revisione(db)
    secondo = post_da_approvare(db, campagna_id=campagna.id, data_ora=SCADENZA)
    primo = post_da_approvare(
        db, campagna_id=campagna.id, data_ora=SCADENZA - timedelta(days=1)
    )
    post_da_approvare(db)  # di un'altra campagna
    db.add(
        VersionePost(
            post_id=primo.id,
            numero=2,
            testo="Testo rigenerato",
            hashtag=[],
            tipo_intervento="rigenera_totale",
        )
    )
    db.flush()

    trovati = post_della_campagna(db, campagna.id)

    assert trovati == [primo, secondo]
    assert [v.numero for v in trovati[0].versioni] == [1, 2]
    assert trovati[0].versione_corrente.testo == "Testo rigenerato"
    assert trovati[1].versione_corrente.numero == 1


def test_post_della_campagna_senza_post(db):
    assert post_della_campagna(db, campagna_in_revisione(db).id) == []


def test_ha_blocchi(db):
    campagna = campagna_in_revisione(db)
    post = post_da_approvare(db, campagna_id=campagna.id)
    post_da_approvare(db, da_rivedere=True)  # di un'altra campagna
    assert ha_blocchi(db, campagna.id, SCADENZA) is False
    post.da_rivedere = True
    assert ha_blocchi(db, campagna.id, SCADENZA) is True


def test_approva_post_in_blocco(db):
    campagna = campagna_in_revisione(db)
    primo = post_da_approvare(db, campagna_id=campagna.id)
    secondo = post_da_approvare(db, campagna_id=campagna.id)
    altro = post_da_approvare(db)

    versioni = approva_post(db, campagna.id, SCADENZA)

    assert primo.stato == secondo.stato == "approvato"
    assert altro.stato == "da_approvare"
    assert sorted(v.post_id for v in versioni) == sorted([primo.id, secondo.id])
    assert all(v.numero == 1 for v in versioni)


def test_approva_post_rifiuta_se_un_post_non_e_da_approvare(db):
    campagna = campagna_in_revisione(db)
    primo = post_da_approvare(db, campagna_id=campagna.id)
    post_da_approvare(db, campagna_id=campagna.id, stato="approvato")
    with pytest.raises(StatoNonValido):
        approva_post(db, campagna.id, SCADENZA)
    assert primo.stato == "da_approvare"


def test_post_dovuti(db):
    attiva = campagna_attiva(db)
    dovuto = post_approvato(db, campagna_id=attiva.id, data_ora=SCADENZA)
    preciso = post_approvato(
        db, campagna_id=attiva.id, data_ora=SCADENZA + timedelta(minutes=5)
    )
    post_approvato(db, campagna_id=attiva.id, data_ora=SCADENZA + timedelta(hours=1))
    post_da_approvare(db, campagna_id=attiva.id, data_ora=SCADENZA)
    post_approvato(db, campagna_id=attiva.id, data_ora=SCADENZA, stato="pubblicato")
    sospesa = campagna_attiva(db)
    cambia_stato(db, sospesa, "sospesa")
    post_approvato(db, campagna_id=sospesa.id, data_ora=SCADENZA)

    adesso = SCADENZA + timedelta(minutes=5)
    assert post_dovuti(db, adesso) == [dovuto, preciso]
    assert post_dovuti(db, SCADENZA - timedelta(seconds=1)) == []


@pytest.mark.parametrize("esito", ["pubblicato", "fallito"])
def test_segna_esito(db, esito):
    post = post_approvato(db)
    segna_esito(db, post, esito)
    db.expire(post)
    assert post.stato == esito


def test_segna_esito_su_post_non_approvato(db):
    post = post_da_approvare(db)
    with pytest.raises(StatoNonValido):
        segna_esito(db, post, "pubblicato")
    assert post.stato == "da_approvare"


def test_segna_esito_con_esito_non_ammesso(db):
    post = post_approvato(db)
    with pytest.raises(DatiNonValidi):
        segna_esito(db, post, "approvato")


def test_tutti_chiusi(db):
    attiva = campagna_attiva(db)
    primo = post_approvato(db, campagna_id=attiva.id)
    secondo = post_approvato(db, campagna_id=attiva.id)
    assert tutti_chiusi(db, attiva.id, SCADENZA + timedelta(days=40)) is False
    segna_esito(db, primo, "pubblicato")
    assert tutti_chiusi(db, attiva.id, SCADENZA + timedelta(days=40)) is False
    segna_esito(db, secondo, "fallito")
    assert tutti_chiusi(db, attiva.id, SCADENZA + timedelta(days=40)) is True


def test_le_fabbriche_dei_post_hanno_sempre_la_foto(db):
    attiva = campagna_attiva(db)
    post_approvato(db, campagna_id=attiva.id)
    post_approvato(db, campagna_id=attiva.id)
    immagini = {f.id: f for f in foto_della_campagna(db, attiva.id)}
    trovati = post_della_campagna(db, attiva.id)
    assert len(trovati) == 2
    for post in trovati:
        legame = db.scalars(
            select(VersionePostFoto).where(
                VersionePostFoto.versione_id == post.versione_corrente.id
            )
        ).all()
        assert [l.posizione for l in legame] == [1]
        assert legame[0].foto_id in immagini
    assert sum(f.n_utilizzi for f in immagini.values()) == 2
