from collections.abc import Iterator
from datetime import timedelta

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Impostazioni, leggi_impostazioni
from app.core.db import get_db
from app.core.errori import NonTrovato, StatoNonValido, frase_di_validazione
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


# --- Il 422 dello schema (issue #63, constitution §4) ---------------------------


class _DatiDiProva(BaseModel):
    titolo: str
    giorni: int

    @field_validator("titolo")
    @classmethod
    def titolo_non_vuoto(cls, valore: str) -> str:
        if not valore.strip():
            raise ValueError("Il titolo non può essere vuoto.")
        return valore


@pytest.fixture
def prova_schema() -> Iterator[str]:
    """Un endpoint con uno schema e un parametro nel percorso, solo per il test."""

    @app.post("/api/_prova_schema/{numero}")
    def prova(numero: int, dati: _DatiDiProva) -> dict[str, bool]:
        return {"ok": True}

    try:
        yield "/api/_prova_schema/1"
    finally:
        app.router.routes.pop()


def test_422_dello_schema_e_una_frase_con_i_campi(
    client: TestClient, prova_schema: str
) -> None:
    risposta = client.post(prova_schema, json={})

    assert risposta.status_code == 422
    assert risposta.json() == {
        "detail": "Dati non validi. Controllare: titolo, giorni."
    }


def test_422_dello_schema_non_riporta_i_valori_ricevuti(
    client: TestClient, prova_schema: str
) -> None:
    dati = {"titolo": "Titolo", "giorni": "marta@example.com"}

    risposta = client.post(prova_schema, json=dati)

    assert risposta.status_code == 422
    assert risposta.json() == {"detail": "Dati non validi. Controllare: giorni."}
    assert "marta" not in risposta.text


def test_422_di_un_validatore_porta_il_suo_messaggio(
    client: TestClient, prova_schema: str
) -> None:
    """Il messaggio in italiano del validatore vince sugli altri errori."""
    risposta = client.post(prova_schema, json={"titolo": "  ", "giorni": "x"})

    assert risposta.status_code == 422
    assert risposta.json() == {"detail": "Il titolo non può essere vuoto."}


def test_422_per_un_corpo_che_non_e_json(client: TestClient, prova_schema: str) -> None:
    risposta = client.post(
        prova_schema, content=b"{", headers={"Content-Type": "application/json"}
    )

    assert risposta.status_code == 422
    assert risposta.json() == {"detail": "Dati non validi."}


def test_422_per_un_parametro_del_percorso(
    client: TestClient, prova_schema: str
) -> None:
    risposta = client.post(
        "/api/_prova_schema/abc", json={"titolo": "Titolo", "giorni": 3}
    )

    assert risposta.status_code == 422
    assert risposta.json() == {"detail": "Dati non validi. Controllare: numero."}


def test_422_dello_schema_su_un_endpoint_vero(client, utente_di_prova) -> None:
    """Come lo vede il frontend: `detail` è una frase, non un elenco."""
    utente_di_prova("artigiano")

    risposta = client.post("/api/campagne", json={})

    assert risposta.status_code == 422
    dettaglio = risposta.json()["detail"]
    assert isinstance(dettaglio, str)
    assert dettaglio.startswith("Dati non validi. Controllare: titolo")


def test_frase_di_validazione_senza_errori_e_senza_campi() -> None:
    assert frase_di_validazione([]) == "Dati non validi."
    assert frase_di_validazione([{"type": "missing", "loc": ("body",)}]) == (
        "Dati non validi."
    )
    # un campo ripetuto si nomina una volta sola
    doppio = [{"type": "missing", "loc": ("body", "foto", n)} for n in (0, 1)]
    assert frase_di_validazione(doppio) == "Dati non validi. Controllare: foto."
