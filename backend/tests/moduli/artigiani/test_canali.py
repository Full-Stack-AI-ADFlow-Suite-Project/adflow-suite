"""T1-14: canali MVP, isolamento dell'artigiano e autorizzazione."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app import cli
from app.main import app
from app.moduli.accesso.service import utente_corrente
from app.moduli.accesso import service as accesso
from app.moduli.artigiani.models import AccountSocial
from tests.moduli.artigiani.fabbrica import profilo


def test_canali_seed_facebook_instagram_collegati(db, client):
    cli.esegui_seed(db, "PasswordSoloTest!2026")
    record, _ = accesso.login(
        db,
        "artigiano@example.com",
        "PasswordSoloTest!2026",
        datetime(2026, 10, 8, tzinfo=timezone.utc),
    )
    app.dependency_overrides[utente_corrente] = lambda: record
    risposta = client.get("/api/canali")
    assert risposta.status_code == 200
    assert risposta.json() == [
        {"canale": "facebook", "collegato": True},
        {"canale": "instagram", "collegato": True},
    ]


@pytest.mark.parametrize("stato", ["scaduto", "scollegato"])
def test_account_non_collegato_non_abilita_canale(db, client, utente_di_prova, stato):
    record = utente_di_prova()
    bottega = profilo(db, utente_id=record.id, canali=["facebook", "instagram"])
    account = db.scalar(
        select(AccountSocial).where(
            AccountSocial.profilo_id == bottega.id,
            AccountSocial.piattaforma == "facebook",
        )
    )
    account.stato = stato
    account.permesso = "SegretoNonEsposto"
    db.flush()
    risposta = client.get("/api/canali")
    assert risposta.json() == [
        {"canale": "facebook", "collegato": False},
        {"canale": "instagram", "collegato": True},
    ]
    assert "SegretoNonEsposto" not in risposta.text


def test_senza_profilo_tutti_non_collegati(client, utente_di_prova):
    utente_di_prova()
    assert client.get("/api/canali").json() == [
        {"canale": "facebook", "collegato": False},
        {"canale": "instagram", "collegato": False},
    ]


def test_non_legge_account_di_altri_artigiani(db, client, utente_di_prova):
    record = utente_di_prova()
    profilo(db, canali=["facebook", "instagram"])
    profilo(db, utente_id=record.id, canali=[])
    assert not any(item["collegato"] for item in client.get("/api/canali").json())


@pytest.mark.parametrize("ruolo", ["operatore", "admin"])
def test_canali_riservato_artigiano(client, utente_di_prova, ruolo):
    utente_di_prova(ruolo)
    assert client.get("/api/canali").status_code == 403
