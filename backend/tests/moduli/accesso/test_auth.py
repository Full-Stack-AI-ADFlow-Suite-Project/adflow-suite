"""CA-01, CA-02 e ciclo completo delle sessioni su PostgreSQL reale."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.orologio import adesso
from app.core.security import hash_token
from app.main import app
from app.moduli.accesso.models import Sessione
from app.moduli.accesso.service import COOKIE_SESSIONE, durata_sessione
from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente

ORA = datetime(2026, 10, 7, 10, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def ora_fissa(client):
    app.dependency_overrides[adesso] = lambda: ORA
    yield
    app.dependency_overrides.pop(adesso, None)


def entra(client, record, password=PASSWORD_DI_PROVA):
    return client.post(
        "/api/auth/login", json={"email": record.email, "password": password}
    )


@pytest.mark.parametrize("ruolo", ["artigiano", "operatore", "admin"])
def test_ca01_login_utente_attivo_con_il_suo_ruolo(db, client, ruolo):
    record = utente(db, ruolo)
    risposta = entra(client, record)
    assert risposta.status_code == 200
    assert risposta.json() == {
        "id": record.id,
        "email": record.email,
        "nome": record.nome,
        "ruolo": ruolo,
    }
    assert client.get("/api/auth/me").json() == risposta.json()
    assert risposta.headers["cache-control"] == "no-store"
    assert client.get("/api/auth/me").headers["cache-control"] == "no-store"


def test_ca02_credenziali_errate_non_rivelano_il_dato_sbagliato(db, client):
    record = utente(db)
    inattivo = utente(db, attivo=False)
    risposte = [
        entra(client, record, "PasswordErrata"),
        client.post(
            "/api/auth/login",
            json={"email": "sconosciuto@example.test", "password": PASSWORD_DI_PROVA},
        ),
        entra(client, inattivo),
    ]
    for risposta in risposte:
        assert risposta.status_code == 401
        assert risposta.json() == {"detail": "Email o password non corrette."}
        assert "set-cookie" not in risposta.headers
    assert list(db.scalars(select(Sessione))) == []


def test_login_normalizza_email(db, client):
    record = utente(db)
    risposta = client.post(
        "/api/auth/login",
        json={"email": f"  {record.email.upper()}  ", "password": PASSWORD_DI_PROVA},
    )
    assert risposta.status_code == 200


def test_cookie_e_hash_del_token(db, client):
    record = utente(db)
    risposta = entra(client, record)
    token = client.cookies.get(COOKIE_SESSIONE)
    sessione = db.scalar(select(Sessione))
    assert sessione.token_hash == hash_token(token)
    assert sessione.token_hash != token
    assert sessione.utente_id == record.id
    assert sessione.scade_il == ORA + durata_sessione("artigiano")
    cookie = risposta.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie
    assert "max-age=604800" in cookie
    assert "secure" not in cookie
    assert token not in risposta.text
    assert record.password_hash not in risposta.text


def test_cookie_secure_su_https(db, client):
    record = utente(db)
    with TestClient(app, base_url="https://testserver") as https:
        risposta = entra(https, record)
        assert "secure" in risposta.headers["set-cookie"].lower()
        assert https.get("/api/auth/me").status_code == 200
        logout = https.post("/api/auth/logout")
        assert "secure" in logout.headers["set-cookie"].lower()
        assert https.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize("token", [None, "", "inesistente"])
def test_me_senza_sessione_valida(client, token):
    if token is not None:
        client.cookies.set(COOKIE_SESSIONE, token)
    risposta = client.get("/api/auth/me")
    assert risposta.status_code == 401
    assert risposta.json() == {"detail": "Sessione non valida o scaduta."}


@pytest.mark.parametrize("scarto", [-1, 0, 1])
def test_scadenza_server_precisa(db, client, scarto):
    entra(client, utente(db))
    app.dependency_overrides[adesso] = (
        lambda: ORA + durata_sessione("artigiano") + timedelta(seconds=scarto)
    )
    assert client.get("/api/auth/me").status_code == (200 if scarto < 0 else 401)


def test_utente_disattivato_perde_accesso(db, client):
    record = utente(db)
    entra(client, record)
    record.attivo = False
    db.flush()
    assert client.get("/api/auth/me").status_code == 401


def test_logout_revoca_anche_un_cookie_copiato(db, client):
    entra(client, utente(db))
    token = client.cookies.get(COOKIE_SESSIONE)
    risposta = client.post("/api/auth/logout")
    assert risposta.status_code == 204
    assert risposta.content == b""
    assert client.cookies.get(COOKIE_SESSIONE) is None
    assert list(db.scalars(select(Sessione))) == []
    client.cookies.set(COOKIE_SESSIONE, token)
    assert client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize("token", [None, "inesistente"])
def test_logout_idempotente(client, token):
    if token:
        client.cookies.set(COOKIE_SESSIONE, token)
    for _ in range(2):
        risposta = client.post("/api/auth/logout")
        assert risposta.status_code == 204
        assert "max-age=0" in risposta.headers["set-cookie"].lower()


def test_login_ruota_token_anche_cambiando_account(db, client):
    primo = utente(db)
    secondo = utente(db, "admin")
    entra(client, primo)
    vecchio_token = client.cookies.get(COOKIE_SESSIONE)
    entra(client, secondo)
    nuovo_token = client.cookies.get(COOKIE_SESSIONE)
    assert nuovo_token != vecchio_token
    assert client.get("/api/auth/me").json()["id"] == secondo.id
    assert len(list(db.scalars(select(Sessione)))) == 1
    client.cookies.clear()
    client.cookies.set(COOKIE_SESSIONE, vecchio_token)
    assert client.get("/api/auth/me").status_code == 401


def test_sessioni_di_altri_dispositivi_restano_valide(db, client):
    record = utente(db)
    entra(client, record)
    altro_token = client.cookies.get(COOKIE_SESSIONE)
    client.cookies.clear()
    entra(client, record)
    client.post("/api/auth/logout")
    client.cookies.set(COOKIE_SESSIONE, altro_token)
    assert client.get("/api/auth/me").status_code == 200


def test_login_fallito_non_revoca_sessione_esistente(db, client):
    record = utente(db)
    entra(client, record)
    token = client.cookies.get(COOKIE_SESSIONE)
    assert entra(client, record, "sbagliata").status_code == 401
    assert client.cookies.get(COOKIE_SESSIONE) == token
    assert client.get("/api/auth/me").status_code == 200


@pytest.mark.parametrize(
    "dati",
    [{}, {"email": "x"}, {"email": "x", "password": ""}, {"email": 1, "password": "x"}],
)
def test_login_rifiuta_dati_non_validi(client, dati):
    assert client.post("/api/auth/login", json=dati).status_code == 422
