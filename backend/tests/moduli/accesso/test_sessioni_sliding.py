"""CA-03, CA-61 e CA-62: autenticazione reale e rinnovo R-29."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import get_db
from app.core.orologio import adesso
from app.main import app
from app.moduli.accesso import service
from app.moduli.accesso.models import Sessione, Utente
from app.moduli.accesso.router import router
from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente

ORA = datetime(2026, 10, 8, 10, tzinfo=timezone.utc)


@pytest.fixture
def protetta(db):
    prova = FastAPI()
    prova.exception_handlers.update(app.exception_handlers)
    prova.include_router(router, prefix="/api")
    prova.dependency_overrides[get_db] = lambda: db
    prova.dependency_overrides[adesso] = lambda: ORA

    @prova.get("/operatore")
    def operatore(
        record: Annotated[Utente, Depends(service.richiede_ruolo("operatore"))]
    ):
        return {"id": record.id}

    @prova.get("/artigiano")
    def artigiano(
        record: Annotated[Utente, Depends(service.richiede_ruolo("artigiano"))]
    ):
        return {"id": record.id}

    with TestClient(prova, base_url="https://testserver") as client:
        yield prova, client


def login(client, record):
    risposta = client.post(
        "/api/auth/login", json={"email": record.email, "password": PASSWORD_DI_PROVA}
    )
    assert risposta.status_code == 200
    return client.cookies.get(service.COOKIE_SESSIONE)


@pytest.mark.parametrize("ruolo", ["artigiano", "operatore", "admin"])
def test_ca62_richiesta_rinnova_database_e_cookie(db, protetta, ruolo):
    prova, client = protetta
    record = utente(db, ruolo)
    token = login(client, record)
    durata = service.durata_sessione(ruolo)
    quasi_scadenza = ORA + durata - timedelta(seconds=1)
    prova.dependency_overrides[adesso] = lambda: quasi_scadenza
    risposta = client.get("/api/auth/me")
    assert risposta.status_code == 200
    assert db.scalar(select(Sessione.scade_il)) == quasi_scadenza + durata
    assert client.cookies.get(service.COOKIE_SESSIONE) == token
    cookie = risposta.headers["set-cookie"].lower()
    assert f"max-age={int(durata.total_seconds())}" in cookie
    assert "secure" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    # Superata la scadenza iniziale, l'attività precedente tiene valida la sessione.
    prova.dependency_overrides[adesso] = lambda: ORA + durata + timedelta(minutes=1)
    assert client.get("/api/auth/me").status_code == 200


@pytest.mark.parametrize("ruolo", ["artigiano", "operatore", "admin"])
@pytest.mark.parametrize("oltre", [0, 1])
def test_ca62_sessione_non_usata_scade_senza_rinnovo(db, protetta, ruolo, oltre):
    prova, client = protetta
    record = utente(db, ruolo)
    login(client, record)
    scadenza = ORA + service.durata_sessione(ruolo)
    prova.dependency_overrides[adesso] = lambda: scadenza + timedelta(seconds=oltre)
    risposta = client.get("/api/auth/me")
    assert risposta.status_code == 401
    assert "set-cookie" not in risposta.headers
    assert db.scalar(select(Sessione.scade_il)) == scadenza


def test_ca03_artigiano_non_accede_operatore(db, protetta):
    _, client = protetta
    login(client, utente(db))
    assert client.get("/operatore").status_code == 403


def test_ca61_admin_accede_operatore_non_artigiano(db, protetta):
    _, client = protetta
    login(client, utente(db, "admin"))
    assert client.get("/operatore").status_code == 200
    assert client.get("/artigiano").status_code == 403


@pytest.mark.parametrize("token", [None, "inesistente", ""])
def test_endpoint_protetto_senza_sessione_401(protetta, token):
    _, client = protetta
    if token is not None:
        client.cookies.set(service.COOKIE_SESSIONE, token)
    assert client.get("/operatore").status_code == 401


def test_cambio_ruolo_riletto_e_durata_adattata(db, protetta):
    prova, client = protetta
    record = utente(db)
    login(client, record)
    record.ruolo = "operatore"
    db.flush()
    dopo = ORA + timedelta(hours=1)
    prova.dependency_overrides[adesso] = lambda: dopo
    assert client.get("/operatore").status_code == 200
    assert db.scalar(select(Sessione.scade_il)) == dopo + timedelta(hours=12)
    record.ruolo = "artigiano"
    db.flush()
    assert client.get("/operatore").status_code == 403


def test_sessione_rinnovata_anche_fuori_auth_me(db, protetta):
    prova, client = protetta
    login(client, utente(db, "operatore"))
    dopo = ORA + timedelta(hours=5)
    prova.dependency_overrides[adesso] = lambda: dopo
    risposta = client.get("/operatore")
    assert risposta.status_code == 200
    assert "set-cookie" in risposta.headers
    assert risposta.headers["cache-control"] == "no-store"
    assert db.scalar(select(Sessione.scade_il)) == dopo + timedelta(hours=12)


def test_rinnovo_non_fa_commit(db):
    record = utente(db)
    _, token = service.login(db, record.email, PASSWORD_DI_PROVA, ORA)
    iniziale = db.scalar(select(Sessione.scade_il))
    with db.begin_nested() as savepoint:
        service.utente_della_sessione(db, token, ORA + timedelta(days=1))
        assert db.scalar(select(Sessione.scade_il)) > iniziale
        savepoint.rollback()
    assert db.scalar(select(Sessione.scade_il)) == iniziale
