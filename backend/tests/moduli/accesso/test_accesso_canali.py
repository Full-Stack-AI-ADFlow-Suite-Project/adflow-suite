"""Autenticazione reale di GET /canali dopo il merge di T1-14."""

import pytest

from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente
from tests.moduli.artigiani.fabbrica import profilo


@pytest.mark.parametrize(
    "ruolo,codice", [("artigiano", 200), ("operatore", 403), ("admin", 403)]
)
def test_canali_con_login_reale(db, client, ruolo, codice):
    record = utente(db, ruolo)
    if ruolo == "artigiano":
        profilo(db, utente_id=record.id, canali=["facebook", "instagram"])
    assert (
        client.post(
            "/api/auth/login",
            json={"email": record.email, "password": PASSWORD_DI_PROVA},
        ).status_code
        == 200
    )
    risposta = client.get("/api/canali")
    assert risposta.status_code == codice
    if codice == 200:
        assert risposta.json() == [
            {"canale": "facebook", "collegato": True},
            {"canale": "instagram", "collegato": True},
        ]
        assert "httponly" in risposta.headers["set-cookie"].lower()
    else:
        assert "set-cookie" not in risposta.headers


def test_canali_senza_sessione_401(client):
    assert client.get("/api/canali").status_code == 401
