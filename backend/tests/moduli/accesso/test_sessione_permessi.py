"""CA-03 con sessioni reali e compatibilità della fixture utente_di_prova."""

from datetime import datetime, timezone
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.core.orologio import adesso
from app.main import app
from app.moduli.accesso.models import Utente
from app.moduli.accesso.service import COOKIE_SESSIONE, richiede_ruolo, durata_sessione
from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente


@pytest.fixture
def riservato(db, client):
    # App isolata: nessuna rotta di prova aggiunta alla composizione del progetto.
    prova = FastAPI()
    prova.exception_handlers.update(app.exception_handlers)
    prova.dependency_overrides[get_db] = lambda: db

    @prova.get("/operatore")
    def operatore(
        record: Annotated[Utente, Depends(richiede_ruolo("operatore", "admin"))],
    ):
        return {"id": record.id}

    with TestClient(prova) as accesso:
        yield accesso, prova


def login(client, record):
    risposta = client.post(
        "/api/auth/login", json={"email": record.email, "password": PASSWORD_DI_PROVA}
    )
    assert risposta.status_code == 200
    return client.cookies.get(COOKIE_SESSIONE)


def test_ca03_artigiano_non_accede_a_funzione_operatore(db, client, riservato):
    record = utente(db)
    accesso, _ = riservato
    accesso.cookies.set(COOKIE_SESSIONE, login(client, record))
    risposta = accesso.get("/operatore")
    assert risposta.status_code == 403
    assert risposta.json() == {"detail": "Non hai i permessi per questa operazione."}


@pytest.mark.parametrize("ruolo", ["operatore", "admin"])
def test_ruoli_ammessi_con_cookie_reale(db, client, riservato, ruolo):
    record = utente(db, ruolo)
    accesso, _ = riservato
    accesso.cookies.set(COOKIE_SESSIONE, login(client, record))
    risposta = accesso.get("/operatore")
    assert risposta.status_code == 200
    assert risposta.json() == {"id": record.id}


@pytest.mark.parametrize("token", [None, "inesistente"])
def test_funzione_riservata_senza_sessione_restituisce_401(riservato, token):
    accesso, _ = riservato
    if token:
        accesso.cookies.set(COOKIE_SESSIONE, token)
    assert accesso.get("/operatore").status_code == 401


def test_scadenza_precede_controllo_del_ruolo(db, client, riservato):
    accesso, prova = riservato
    ora = datetime(2026, 10, 7, tzinfo=timezone.utc)
    app.dependency_overrides[adesso] = lambda: ora
    accesso.cookies.set(COOKIE_SESSIONE, login(client, utente(db)))
    prova.dependency_overrides[adesso] = lambda: ora + durata_sessione("artigiano")
    assert accesso.get("/operatore").status_code == 401


def test_utente_di_prova_funzione_me(client, utente_di_prova):
    record = utente_di_prova("operatore")
    risposta = client.get("/api/auth/me")
    assert risposta.status_code == 200
    assert risposta.json()["id"] == record.id
