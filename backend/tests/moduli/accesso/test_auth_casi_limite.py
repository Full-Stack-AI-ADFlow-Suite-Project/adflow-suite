"""Input ostili, isolamento dei token e limiti delle credenziali."""

import json

import pytest
from sqlalchemy import func, select

from app.core.errori import DatiNonValidi
from app.main import app
from app.moduli.accesso import service
from app.moduli.accesso.models import Sessione, Utente
from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente


@pytest.mark.parametrize(
    "dati",
    [
        {"password": "CredenzialeSoloTest"},
        {"email": "x@example.test", "password": ["CredenzialeSoloTest"]},
        {"email": "x@example.test", "password": "CredenzialeSoloTest" * 100},
    ],
)
def test_errori_di_validazione_non_riflettono_password(client, dati):
    risposta = client.post("/api/auth/login", json=dati)
    assert risposta.status_code == 422
    assert "CredenzialeSoloTest" not in risposta.text
    assert risposta.json() == {"detail": "Dati di accesso non validi."}


@pytest.mark.parametrize("email", ["a\x00@example.test", "a\ud800@example.test"])
def test_login_email_non_rappresentabile_rifiutata(client, email):
    # JSON escaped: anche i surrogati isolati possono arrivare attraverso HTTP.
    risposta = client.post(
        "/api/auth/login",
        content=json.dumps({"email": email, "password": PASSWORD_DI_PROVA}),
        headers={"Content-Type": "application/json"},
    )
    assert risposta.status_code == 422


@pytest.mark.parametrize("campo", ["email", "nome", "password"])
def test_creazione_rifiuta_unicode_non_rappresentabile(db, campo):
    dati = dict(
        email="persona@example.test", nome="Persona", password="Password", ruolo="admin"
    )
    dati[campo] = "a\ud800@example.test"
    with pytest.raises(DatiNonValidi):
        service.crea_utente(db, **dati)
    assert db.scalar(select(func.count()).select_from(Utente)) == 0


@pytest.mark.parametrize("campo", ["email", "nome"])
def test_creazione_rifiuta_nul_nei_campi_postgres(db, campo):
    dati = dict(
        email="persona@example.test", nome="Persona", password="Password", ruolo="admin"
    )
    dati[campo] = "a\x00@example.test"
    with pytest.raises(DatiNonValidi):
        service.crea_utente(db, **dati)
    assert db.scalar(select(func.count()).select_from(Utente)) == 0


@pytest.mark.parametrize("password", ["x", "x" * 1024, "  à😊\x00  "])
def test_password_limite_e_unicode_roundtrip(db, client, password):
    record = service.crea_utente(
        db, "persona@example.test", password, "Persona", "admin"
    )
    risposta = client.post(
        "/api/auth/login", json={"email": record.email, "password": password}
    )
    assert risposta.status_code == 200
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204


def test_password_non_viene_tagliata_o_normalizzata(db, client):
    record = service.crea_utente(
        db, "persona@example.test", " Password ", "Persona", "admin"
    )
    risposta = client.post(
        "/api/auth/login", json={"email": record.email, "password": "Password"}
    )
    assert risposta.status_code == 401


@pytest.mark.parametrize(
    "hash_corrotto", ["", "scrypt$-1$8$1$00$00", "argon2$non-valido"]
)
def test_hash_password_corrotto_non_causa_500(db, client, hash_corrotto):
    record = utente(db, password_hash=hash_corrotto)
    risposta = client.post(
        "/api/auth/login", json={"email": record.email, "password": PASSWORD_DI_PROVA}
    )
    assert risposta.status_code == 401
    assert list(db.scalars(select(Sessione))) == []


@pytest.mark.parametrize(
    "email", ["' OR 1=1 --", "persona@example.test' UNION SELECT 1 --"]
)
def test_email_sql_ostile_non_autentica(db, client, email):
    utente(db)
    risposta = client.post(
        "/api/auth/login", json={"email": email, "password": PASSWORD_DI_PROVA}
    )
    assert risposta.status_code == 401
    assert list(db.scalars(select(Sessione))) == []


def test_ruolo_e_id_del_body_non_alzano_privilegi(db, client):
    record = utente(db, "artigiano")
    risposta = client.post(
        "/api/auth/login",
        json={
            "email": record.email,
            "password": PASSWORD_DI_PROVA,
            "ruolo": "admin",
            "id": 999,
        },
    )
    assert risposta.status_code == 200
    assert risposta.json()["ruolo"] == "artigiano"
    assert risposta.json()["id"] == record.id


def test_hash_database_non_utilizzabile_come_token(db, client):
    record = utente(db)
    assert (
        client.post(
            "/api/auth/login",
            json={"email": record.email, "password": PASSWORD_DI_PROVA},
        ).status_code
        == 200
    )
    sessione = db.scalar(select(Sessione))
    client.cookies.clear()
    client.cookies.set(service.COOKIE_SESSIONE, sessione.token_hash)
    assert client.get("/api/auth/me").status_code == 401


def test_header_bearer_non_sostituisce_cookie(db, client):
    record = utente(db)
    client.post(
        "/api/auth/login", json={"email": record.email, "password": PASSWORD_DI_PROVA}
    )
    token = client.cookies.get(service.COOKIE_SESSIONE)
    client.cookies.clear()
    assert (
        client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


def test_openapi_non_espone_hash_password_o_token():
    schema = app.openapi()["components"]["schemas"]["UtentePubblico"]
    assert set(schema["properties"]) == {"id", "email", "nome", "ruolo"}


@pytest.mark.parametrize(
    "body,content_type",
    [
        ('{"password":"CredenzialeSoloTest",', "application/json"),
        ('["CredenzialeSoloTest"]', "application/json"),
        ('"CredenzialeSoloTest"', "application/json"),
        ("password=CredenzialeSoloTest", "application/x-www-form-urlencoded"),
        ("CredenzialeSoloTest", "text/plain"),
    ],
)
def test_body_malformato_non_riflette_credenziali(client, body, content_type):
    risposta = client.post(
        "/api/auth/login", content=body, headers={"Content-Type": content_type}
    )
    assert risposta.status_code == 422
    assert risposta.json() == {"detail": "Dati di accesso non validi."}
    assert "CredenzialeSoloTest" not in risposta.text
    assert risposta.headers["cache-control"] == "no-store"
