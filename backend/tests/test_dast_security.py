"""Probe DAST locali sulle rotte HTTP, senza avviare DB o servizi esterni."""

from collections.abc import Iterator
import logging

import pytest
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient as StarletteTestClient

from app.core.config import leggi_impostazioni
from app.core.db import get_db
from app.core.errori import NonAutenticato
from app.core.protezione_csrf import MESSAGGIO, ProtezioneCSRF
from app.main import app
from app.moduli.accesso.service import utente_corrente


@pytest.fixture
def client(monkeypatch) -> Iterator[TestClient]:
    def sessione_non_valida():
        raise NonAutenticato("Sessione non valida o scaduta.")

    monkeypatch.setitem(app.dependency_overrides, get_db, lambda: None)
    monkeypatch.setitem(app.dependency_overrides, utente_corrente, sessione_non_valida)
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    ("metodo", "percorso"),
    [
        ("GET", "/api/auth/me"),
        ("GET", "/api/campagne"),
        ("GET", "/api/profilo"),
        ("GET", "/api/da-approvare"),
        ("GET", "/api/foto/1/file"),
        ("POST", "/api/campagne/1/approva"),
    ],
)
def test_dast_rotte_protette_rifiutano_client_anonimo(
    client: TestClient, metodo: str, percorso: str
) -> None:
    risposta = client.request(metodo, percorso, headers={"Origin": "http://testserver"})

    assert risposta.status_code == 401
    assert risposta.headers.get("cache-control") == "no-store"
    assert risposta.headers.get("x-request-id")
    assert "set-cookie" not in risposta.headers


def test_dast_foto_pubblica_rifiuta_firma_non_valida(client: TestClient) -> None:
    risposta = client.get(
        "/api/foto/1/pubblica?canale=instagram&firma=1_firma-non-valida"
    )

    assert risposta.status_code == 404
    assert risposta.json() == {"detail": "Foto non trovata."}
    assert risposta.headers.get("x-request-id")


def test_dast_solo_endpoint_pubblici_previsti_senza_sessione(
    client: TestClient,
) -> None:
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/consorzio").status_code == 200


def test_dast_log_dettagliato_redige_query_e_registra_esito(
    client: TestClient, caplog
) -> None:
    query_segreta = "token-che-non-deve-finire-nei-log"
    with caplog.at_level(logging.INFO, logger="adflow.http"):
        risposta = client.get(f"/api/campagne?token={query_segreta}")

    assert risposta.status_code == 401
    assert "http_request_started" in caplog.text
    assert "http_request_finished" in caplog.text
    assert "status_code" in caplog.text
    assert "test_dast_log_dettagliato_redige_query_e_registra_esito" in caplog.text
    assert query_segreta not in caplog.text


def test_dast_csrf_middleware_collegato_alla_modalita_produzione() -> None:
    middleware = next(
        voce for voce in app.user_middleware if voce.cls is ProtezioneCSRF
    )

    assert middleware.kwargs["abilitata"] is (
        leggi_impostazioni().ambiente == "produzione"
    )


def _app_csrf() -> Starlette:
    prova = Starlette()
    prova.add_middleware(ProtezioneCSRF, abilitata=True)

    async def cambia_stato(request):
        return JSONResponse({"stato": "modificato"})

    async def lettura(request):
        return JSONResponse({"stato": "letto"})

    prova.routes.extend(
        [
            Route("/modifica", cambia_stato, methods=["POST"]),
            Route("/lettura", lettura, methods=["GET"]),
        ]
    )
    return prova


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Origin": "https://attaccante.example.test"},
        {"Origin": "https://evil.app.example.test"},
        {"Origin": "null"},
        {"Origin": "https://utente:pass@app.example.test"},
        {"Origin": "https://app.example.test/percorso"},
    ],
)
def test_dast_csrf_rifiuta_origini_mancanti_o_non_corrispondenti(
    headers: dict[str, str],
) -> None:
    with StarletteTestClient(
        _app_csrf(), base_url="https://app.example.test"
    ) as client:
        risposta = client.post("/modifica", headers=headers)

    assert risposta.status_code == 403
    assert risposta.json() == {"detail": MESSAGGIO}
    assert risposta.headers["cache-control"] == "no-store"


def test_dast_csrf_accetta_stessa_origine_e_metodi_di_lettura() -> None:
    with StarletteTestClient(
        _app_csrf(), base_url="https://app.example.test"
    ) as client:
        modifica = client.post(
            "/modifica", headers={"Origin": "https://app.example.test"}
        )
        lettura = client.get("/lettura")

    assert modifica.status_code == 200
    assert lettura.status_code == 200
