"""Fixture utente_di_prova: sostituisce utente_corrente nei test delle API."""
from collections.abc import Iterator
from typing import Annotated

import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.main import app
from app.moduli.accesso.models import Utente
from app.moduli.accesso.service import richiede_ruolo, utente_corrente

router = APIRouter(prefix="/api/_prova")


@router.get("/io")
def io(utente: Annotated[Utente, Depends(utente_corrente)]) -> dict[str, str | int]:
    return {"id": utente.id, "ruolo": utente.ruolo}


@router.get("/operatore")
def solo_operatore(
    utente: Annotated[Utente, Depends(richiede_ruolo("operatore", "admin"))]
) -> dict[str, int]:
    return {"id": utente.id}


@pytest.fixture(autouse=True)
def rotte_di_prova() -> Iterator[None]:
    prima = len(app.router.routes)
    app.include_router(router)
    yield
    del app.router.routes[prima:]


def test_api_con_utente_di_prova(client: TestClient, utente_di_prova) -> None:
    artigiano = utente_di_prova("artigiano")

    risposta = client.get("/api/_prova/io")

    assert risposta.status_code == 200
    assert risposta.json() == {"id": artigiano.id, "ruolo": "artigiano"}


def test_utente_di_prova_passa_il_controllo_del_ruolo(
    client: TestClient, utente_di_prova
) -> None:
    operatore = utente_di_prova("operatore")

    risposta = client.get("/api/_prova/operatore")

    assert risposta.status_code == 200
    assert risposta.json() == {"id": operatore.id}


def test_utente_di_prova_con_ruolo_sbagliato_riceve_403(
    client: TestClient, utente_di_prova
) -> None:
    utente_di_prova("artigiano")

    risposta = client.get("/api/_prova/operatore")

    assert risposta.status_code == 403
    assert risposta.json() == {"detail": "Non hai i permessi per questa operazione."}


def test_utente_di_prova_si_puo_cambiare(client: TestClient, utente_di_prova) -> None:
    utente_di_prova("artigiano")
    admin = utente_di_prova("admin", nome="Admin di prova")

    assert client.get("/api/_prova/io").json() == {"id": admin.id, "ruolo": "admin"}
    assert admin.nome == "Admin di prova"


def test_la_sostituzione_non_resta_dopo_il_test() -> None:
    assert utente_corrente not in app.dependency_overrides
