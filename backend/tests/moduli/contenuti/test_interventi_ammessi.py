"""T3-61: gli interventi che l'operatore può fare adesso su un post (spec R-16)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.errori import StatoNonValido
from app.moduli.contenuti.interventi import verifica_intervento
from app.moduli.contenuti.models import VersionePost, VersionePostFoto
from app.moduli.contenuti.service import interventi_ammessi
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_sospesa
from tests.moduli.contenuti.fabbrica import (
    post_approvato,
    post_da_approvare,
    post_fallito,
)

# I post della fabbrica escono il 5/1/2030 alle 12:00 UTC.
ADESSO = datetime(2030, 1, 5, 9, tzinfo=timezone.utc)


def test_in_revisione_cinque_interventi(db):
    uno = post_da_approvare(db)
    assert interventi_ammessi(uno, "in_revisione", ADESSO) == [
        "modifica",
        "rigenera",
        "rigenera_immagine",
        "cambia_foto",
        "sposta",
    ]


def test_approvato_oltre_il_margine(db):
    attivo = post_approvato(db)
    sospeso = post_approvato(db, campagna_id=campagna_sospesa(db).id)
    giusto = post_approvato(db, data_ora=ADESSO + timedelta(minutes=15))
    for uno, stato in ((attivo, "attiva"), (sospeso, "sospesa"), (giusto, "attiva")):
        assert interventi_ammessi(uno, stato, ADESSO) == [
            "modifica",
            "cambia_foto",
            "sposta",
            "annulla",
        ]


def test_approvato_entro_il_margine_nessuno(db):
    uno = post_approvato(db, data_ora=ADESSO + timedelta(minutes=14))
    assert interventi_ammessi(uno, "attiva", ADESSO) == []
    with pytest.raises(StatoNonValido, match="esce tra meno di 15 minuti"):
        verifica_intervento(db, uno, "modifica", ADESSO)


def test_con_un_intervento_in_corso_nessuno(db):
    uno = post_da_approvare(
        db,
        intervento_in_corso="rigenera_totale",
        intervento_dal=ADESSO - timedelta(minutes=2),
    )
    assert interventi_ammessi(uno, "in_revisione", ADESSO) == []
    with pytest.raises(StatoNonValido, match="intervento in corso"):
        verifica_intervento(db, uno, "sposta", ADESSO)
    # Dopo 10 minuti vale come fallito (R-31).
    uno.intervento_dal = ADESSO - timedelta(minutes=11)
    assert len(interventi_ammessi(uno, "in_revisione", ADESSO)) == 5


def test_fallito_solo_riprogramma(db):
    uno = post_fallito(db)
    sospeso = post_fallito(db, campagna_id=campagna_sospesa(db).id)
    assert interventi_ammessi(uno, "attiva", ADESSO) == ["riprogramma"]
    assert interventi_ammessi(sospeso, "sospesa", ADESSO) == ["riprogramma"]


def test_immagine_ai_ammette_cambia_foto(db):
    """ADR-119: anche un post con un'immagine AI cambia immagine."""
    uno = post_da_approvare(db, riempitivo="immagine_ai")
    assert interventi_ammessi(uno, "in_revisione", ADESSO) == [
        "modifica",
        "rigenera",
        "rigenera_immagine",
        "cambia_foto",
        "sposta",
    ]


def test_rigenerazioni_finite_senza_rigenera(db):
    uno = post_da_approvare(db, n_rigenerazioni_testo=3)
    assert interventi_ammessi(uno, "in_revisione", ADESSO) == [
        "modifica",
        "rigenera_immagine",
        "cambia_foto",
        "sposta",
    ]
    with pytest.raises(StatoNonValido, match="Le 3 rigenerazioni"):
        verifica_intervento(db, uno, "rigenera", ADESSO)


def test_tre_rigenerazioni_dell_immagine_senza_rigenera_immagine(db):
    """R-49: alla quarta rigenerazione dell'immagine l'intervento non c'è più."""
    uno = post_da_approvare(db)
    for numero in range(2, 5):
        db.add(
            VersionePost(
                post_id=uno.id,
                numero=numero,
                testo="Testo di prova",
                hashtag=["artigianato"],
                tipo_intervento="rigenera_immagine",
            )
        )
    db.flush()
    db.expire(uno, ["versioni"])

    assert "rigenera_immagine" not in interventi_ammessi(uno, "in_revisione", ADESSO)
    with pytest.raises(StatoNonValido, match="già stata rigenerata 3 volte"):
        verifica_intervento(db, uno, "rigenera_immagine", ADESSO)


def test_senza_versione_solo_sposta(db):
    uno = post_da_approvare(db)
    db.query(VersionePostFoto).delete()
    db.delete(uno.versioni[0])
    db.flush()
    db.expire(uno, ["versioni"])
    assert interventi_ammessi(uno, "in_revisione", ADESSO) == ["sposta"]
    with pytest.raises(StatoNonValido, match="non ha ancora un testo"):
        verifica_intervento(db, uno, "modifica", ADESSO)


@pytest.mark.parametrize("stato", ["pubblicato", "annullato", "scaduto", "scartato"])
def test_stati_chiusi_nessuno(db, stato):
    campagna = campagna_attiva(db)
    uno = post_da_approvare(db, campagna_id=campagna.id, stato=stato)
    assert interventi_ammessi(uno, "attiva", ADESSO) == []
    with pytest.raises(StatoNonValido, match="Questo intervento non è ammesso"):
        verifica_intervento(db, uno, "modifica", ADESSO)


def test_verifica_restituisce_la_campagna(db):
    uno = post_da_approvare(db)
    assert verifica_intervento(db, uno, "sposta", ADESSO).id == uno.campagna_id
