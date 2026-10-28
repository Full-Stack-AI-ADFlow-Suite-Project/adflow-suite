"""CA-100: l'avviso `campagne_sovrapposte` nel dettaglio della campagna (R-12, R-25).

Due campagne della stessa bottega possono avere periodi sovrapposti (ADR-119):
il dettaglio lo segnala quando l'altra campagna non è in bozza e non è chiusa.
"""

from datetime import timedelta

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.core.orologio import adesso
from app.moduli.campagne import domain
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza


def _avvisi(client: TestClient, campagna_id: int) -> list[str]:
    risposta = client.get(f"/api/campagne/{campagna_id}")
    assert risposta.status_code == 200
    return risposta.json()["avvisi"]


def test_ca100_avviso_con_campagna_attiva_sovrapposta(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-100: campagna attiva con lo stesso periodo -> avviso `campagne_sovrapposte`."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["instagram"])

    inizio = adesso().date() + timedelta(days=10)
    fine = inizio + timedelta(days=20)
    campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        titolo="Campagna attiva",
        inizio=inizio,
        fine=fine,
        stato=domain.ATTIVA,
    )
    bozza = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        titolo="Bozza sovrapposta",
        inizio=inizio + timedelta(days=5),
        fine=fine,
    )

    assert "campagne_sovrapposte" in _avvisi(client, bozza.id)


@pytest.mark.parametrize(
    "stato",
    [domain.BOZZA, domain.RESPINTA, domain.SCADUTA, domain.ANNULLATA, domain.CONCLUSA],
)
def test_ca100_nessun_avviso_con_campagna_in_bozza_o_chiusa(
    client: TestClient, utente_di_prova, db: Session, stato: str
):
    """CA-100: in bozza o chiusa (respinta, scaduta, annullata, conclusa) -> nessun avviso."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["instagram"])

    inizio = adesso().date() + timedelta(days=10)
    fine = inizio + timedelta(days=20)
    campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        titolo="Campagna non in corso",
        inizio=inizio,
        fine=fine,
        stato=stato,
    )
    # La campagna che si legge non è quella creata sopra: una seconda bozza
    # non è ammessa dall'API, ma la fabbrica può scriverla.
    bozza = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        titolo="Bozza sovrapposta",
        inizio=inizio + timedelta(days=5),
        fine=fine,
    )

    assert "campagne_sovrapposte" not in _avvisi(client, bozza.id)


def test_ca100_nessun_avviso_con_campagna_di_un_altra_bottega(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-100: la campagna sovrapposta di un'altra bottega non produce l'avviso."""
    artigiano = utente_di_prova("artigiano")
    altra_bottega = profilo(db, utente_id=utente(db).id, canali=["instagram"])

    inizio = adesso().date() + timedelta(days=10)
    fine = inizio + timedelta(days=20)
    campagna_in_bozza(
        db,
        profilo_id=altra_bottega.id,
        titolo="Campagna di un'altra bottega",
        inizio=inizio,
        fine=fine,
        stato=domain.ATTIVA,
    )
    bozza = campagna_in_bozza(
        db,
        profilo_id=profilo(db, utente_id=artigiano.id, canali=["instagram"]).id,
        titolo="Bozza della bottega",
        inizio=inizio + timedelta(days=5),
        fine=fine,
    )

    assert "campagne_sovrapposte" not in _avvisi(client, bozza.id)
