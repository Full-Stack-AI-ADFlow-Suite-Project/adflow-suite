from datetime import timedelta

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Impostazioni, leggi_impostazioni
from app.core.db import get_db
from app.core.errori import NonTrovato, StatoNonValido
from app.core.orologio import adesso
from app.core.transizioni import verifica_transizione
from app.main import app

TRANSIZIONI = {"bozza": {"inviata"}, "inviata": {"in_revisione", "scaduta"}}


def test_health(client: TestClient) -> None:
    risposta = client.get("/api/health")
    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "ok"}


def test_la_sessione_dei_test_usa_adflow_test(db: Session) -> None:
    assert db.execute(text("SELECT current_database()")).scalar_one().endswith("_test")


def test_il_router_riceve_la_sessione_del_test(client: TestClient, db: Session) -> None:
    viste = []

    @app.get("/api/_prova_db")
    def prova_db(sessione: Session = Depends(get_db)) -> dict[str, bool]:
        viste.append(sessione)
        return {"ok": True}

    try:
        assert client.get("/api/_prova_db").status_code == 200
        assert viste == [db]
    finally:
        app.router.routes.pop()


def test_errore_di_dominio_diventa_detail(client: TestClient) -> None:
    @app.get("/api/_prova_errore")
    def prova_errore() -> None:
        raise NonTrovato("Campagna non trovata.")

    try:
        risposta = client.get("/api/_prova_errore")
        assert risposta.status_code == 404
        assert risposta.json() == {"detail": "Campagna non trovata."}
    finally:
        app.router.routes.pop()


def test_transizione_ammessa() -> None:
    verifica_transizione(TRANSIZIONI, "bozza", "inviata")


@pytest.mark.parametrize(
    ("da", "a"),
    [("bozza", "scaduta"), ("inviata", "bozza"), ("scaduta", "bozza")],
)
def test_transizione_vietata(da: str, a: str) -> None:
    with pytest.raises(StatoNonValido):
        verifica_transizione(TRANSIZIONI, da, a)


def test_adesso_e_in_utc() -> None:
    assert adesso().utcoffset().total_seconds() == 0


def test_adesso_va_avanti_dei_giorni_chiesti_per_le_prove_a_mano(monkeypatch) -> None:
    monkeypatch.setattr(leggi_impostazioni(), "orologio_giorni_avanti", 0)
    vera = adesso()
    monkeypatch.setattr(leggi_impostazioni(), "orologio_giorni_avanti", 12)
    avanti = adesso() - vera
    assert timedelta(days=12) <= avanti < timedelta(days=12, minutes=1)


def test_in_produzione_l_orologio_non_si_sposta() -> None:
    valori = dict(
        _env_file=None,
        database_url="postgresql://finto",
        database_url_test="postgresql://finto",
        login_limite_segreto="s" * 32,
        cookie_secure=True,
    )
    assert Impostazioni(**valori, ambiente="sviluppo", orologio_giorni_avanti=12)
    assert Impostazioni(**valori, ambiente="produzione").orologio_giorni_avanti == 0
    with pytest.raises(ValidationError):
        Impostazioni(**valori, ambiente="produzione", orologio_giorni_avanti=12)
