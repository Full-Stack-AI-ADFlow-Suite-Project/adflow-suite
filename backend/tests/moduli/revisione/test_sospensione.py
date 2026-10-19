"""Test di sospendi, riattiva e annulla (T2b-43, R-33, CA-32)."""

from datetime import datetime, timezone

from sqlalchemy import select

from app.moduli.campagne.models import DecisioneCampagna
from app.moduli.contenuti import service as contenuti
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_inviata,
    campagna_sospesa,
)
from tests.moduli.contenuti.fabbrica import post_approvato, post_fallito

ADESSO = datetime(2026, 1, 10, 12, tzinfo=timezone.utc)
PASSATO = datetime(2026, 1, 5, 12, tzinfo=timezone.utc)
FUTURO = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)


def _decisioni(db, campagna_id):
    return db.scalars(
        select(DecisioneCampagna)
        .where(DecisioneCampagna.campagna_id == campagna_id)
        .order_by(DecisioneCampagna.id)
    ).all()


def test_ca32_sospendi_ferma_la_pubblicazione(db, client, utente_di_prova):
    """attiva → sospesa: i post dovuti non escono più (post_dovuti li esclude)."""
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    operatore = utente_di_prova("operatore")

    assert contenuti.post_dovuti(db, ADESSO) == [post]

    risposta = client.post(f"/api/campagne/{campagna.id}/sospendi")
    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "sospesa"}

    db.refresh(campagna)
    db.refresh(post)
    assert campagna.stato == "sospesa"
    assert post.stato == "approvato"
    assert contenuti.post_dovuti(db, ADESSO) == []

    [decisione] = _decisioni(db, campagna.id)
    assert decisione.esito == "sospesa"
    assert decisione.utente_id == operatore.id


def test_ca32_sospendi_con_la_nota(db, client, utente_di_prova):
    campagna = campagna_attiva(db)
    utente_di_prova("operatore")

    risposta = client.post(
        f"/api/campagne/{campagna.id}/sospendi",
        json={"nota": "  Il laboratorio è chiuso per ferie  "},
    )
    assert risposta.status_code == 200

    [decisione] = _decisioni(db, campagna.id)
    assert decisione.esito == "sospesa"
    assert decisione.nota == "Il laboratorio è chiuso per ferie"


def test_ca32_sospendi_senza_corpo(db, client, utente_di_prova):
    senza_corpo = campagna_attiva(db)
    nota_vuota = campagna_attiva(db)
    utente_di_prova("operatore")

    assert client.post(f"/api/campagne/{senza_corpo.id}/sospendi").status_code == 200
    assert (
        client.post(
            f"/api/campagne/{nota_vuota.id}/sospendi", json={"nota": "   "}
        ).status_code
        == 200
    )

    for campagna in (senza_corpo, nota_vuota):
        [decisione] = _decisioni(db, campagna.id)
        assert (decisione.esito, decisione.nota) == ("sospesa", None)


def test_ca32_riattiva_pubblica_solo_gli_scelti(db, client, utente_di_prova):
    """Gli arretrati scelti tornano pubblicabili, gli altri diventano annullato."""
    campagna = campagna_sospesa(db)
    scelto = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    non_scelto = post_approvato(
        db, campagna_id=campagna.id, canale="facebook", data_ora=PASSATO
    )
    futuro = post_approvato(db, campagna_id=campagna.id, data_ora=FUTURO)
    operatore = utente_di_prova("operatore")

    risposta = client.post(
        f"/api/campagne/{campagna.id}/riattiva",
        json={"pubblica_ora": [scelto.id]},
    )
    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "attiva"}

    db.refresh(campagna)
    db.refresh(scelto)
    db.refresh(non_scelto)
    db.refresh(futuro)
    assert campagna.stato == "attiva"
    assert scelto.stato == "approvato"
    assert contenuti.post_dovuti(db, ADESSO) == [scelto]
    assert non_scelto.stato == "annullato"
    assert futuro.stato == "approvato"

    [decisione] = _decisioni(db, campagna.id)
    assert decisione.esito == "riattivata"
    assert decisione.utente_id == operatore.id


def test_ca32_annulla_annulla_i_post_approvati(db, client, utente_di_prova):
    """Annulla: i post approvato diventano annullato; il fallito resta tale."""
    campagna = campagna_attiva(db)
    approvato = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    fallito = post_fallito(
        db, campagna_id=campagna.id, canale="facebook", data_ora=PASSATO
    )
    operatore = utente_di_prova("operatore")

    risposta = client.post(f"/api/campagne/{campagna.id}/annulla")
    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "annullata"}

    db.refresh(campagna)
    db.refresh(approvato)
    db.refresh(fallito)
    assert campagna.stato == "annullata"
    assert campagna.chiusa_il is not None
    assert approvato.stato == "annullato"
    assert fallito.stato == "fallito"
    assert contenuti.post_dovuti(db, ADESSO) == []

    [decisione] = _decisioni(db, campagna.id)
    assert decisione.esito == "annullata"
    assert decisione.utente_id == operatore.id


def test_annulla_anche_da_sospesa(db, client, utente_di_prova):
    campagna = campagna_sospesa(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=FUTURO)
    utente_di_prova("operatore")

    assert client.post(f"/api/campagne/{campagna.id}/annulla").status_code == 200

    db.refresh(campagna)
    db.refresh(post)
    assert campagna.stato == "annullata"
    assert post.stato == "annullato"


def test_sospendi_fuori_da_attiva_409(db, client, utente_di_prova):
    campagna = campagna_sospesa(db)
    utente_di_prova("operatore")

    risposta = client.post(f"/api/campagne/{campagna.id}/sospendi")
    assert risposta.status_code == 409
    db.refresh(campagna)
    assert campagna.stato == "sospesa"


def test_riattiva_fuori_da_sospesa_409(db, client, utente_di_prova):
    campagna = campagna_attiva(db)
    utente_di_prova("operatore")

    risposta = client.post(
        f"/api/campagne/{campagna.id}/riattiva", json={"pubblica_ora": []}
    )
    assert risposta.status_code == 409
    db.refresh(campagna)
    assert campagna.stato == "attiva"


def test_annulla_fuori_dalle_transizioni_409(db, client, utente_di_prova):
    campagna = campagna_inviata(db)
    utente_di_prova("operatore")

    risposta = client.post(f"/api/campagne/{campagna.id}/annulla")
    assert risposta.status_code == 409
    db.refresh(campagna)
    assert campagna.stato == "inviata"


def test_riattiva_rifiuta_post_non_arretrato_422(db, client, utente_di_prova):
    """pubblica_ora accetta solo post approvati con la data già passata."""
    campagna = campagna_sospesa(db)
    futuro = post_approvato(db, campagna_id=campagna.id, data_ora=FUTURO)
    arretrato = post_approvato(
        db, campagna_id=campagna.id, canale="facebook", data_ora=PASSATO
    )
    utente_di_prova("operatore")

    risposta = client.post(
        f"/api/campagne/{campagna.id}/riattiva",
        json={"pubblica_ora": [futuro.id]},
    )
    assert risposta.status_code == 422
    db.refresh(campagna)
    db.refresh(futuro)
    db.refresh(arretrato)
    assert campagna.stato == "sospesa"
    assert futuro.stato == "approvato"
    assert arretrato.stato == "approvato"


def test_riattiva_rifiuta_post_di_unaltra_campagna_422(db, client, utente_di_prova):
    campagna = campagna_sospesa(db)
    estraneo = post_approvato(db)
    utente_di_prova("operatore")

    risposta = client.post(
        f"/api/campagne/{campagna.id}/riattiva",
        json={"pubblica_ora": [estraneo.id]},
    )
    assert risposta.status_code == 422
    db.refresh(estraneo)
    assert estraneo.stato == "approvato"


def test_permessi_e_campagna_assente(db, client, utente_di_prova):
    campagna = campagna_attiva(db)

    utente_di_prova("artigiano")
    assert client.post(f"/api/campagne/{campagna.id}/sospendi").status_code == 403

    utente_di_prova("operatore")
    assert client.post("/api/campagne/99999/sospendi").status_code == 404
    assert client.post("/api/campagne/99999/annulla").status_code == 404
    assert (
        client.post(
            "/api/campagne/99999/riattiva", json={"pubblica_ora": []}
        ).status_code
        == 404
    )

    # L'admin passa il controllo del ruolo come l'operatore.
    utente_di_prova("admin")
    assert client.post(f"/api/campagne/{campagna.id}/sospendi").status_code == 200
