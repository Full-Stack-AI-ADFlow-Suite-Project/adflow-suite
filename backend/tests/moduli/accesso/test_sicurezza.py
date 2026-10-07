"""Follow-up #16–19: database reale, concorrenza, log e proxy fidati."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import logging
import os
import subprocess
import sys
from threading import Barrier

import pytest
from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import Impostazioni, leggi_impostazioni
from app.core.eventi_sicurezza import logger
from app.core.limite_login import prenota, TroppiTentativi, LimiteNonDisponibile
from app.main import app
from app.moduli.accesso import service
from app.moduli.accesso.email import normalizza_email
from app.moduli.accesso.router import cookie_sicuro
from app.core.errori import DatiNonValidi
from tests.moduli.accesso.fabbrica import utente, PASSWORD_DI_PROVA

ORA = datetime.now(timezone.utc)


def test_limite_scadenza_precisa_e_retry_after(motore_test):
    for _ in range(5):
        prenota("account", "utente@example.com", ORA, engine=motore_test)
    with pytest.raises(TroppiTentativi) as e:
        prenota(
            "account",
            "utente@example.com",
            ORA + timedelta(seconds=899),
            engine=motore_test,
        )
    assert e.value.riprova_dopo == 1
    prenota(
        "account",
        "utente@example.com",
        ORA + timedelta(seconds=900),
        engine=motore_test,
    )


@pytest.mark.parametrize("concorrenti", [8, 20])
@pytest.mark.parametrize("scaduto", [False, True])
def test_limite_concorrente_esattamente_cinque(motore_test, concorrenti, scaduto):
    ora = ORA
    if scaduto:
        for _ in range(5):
            prenota("ip", "192.0.2.1", ora, engine=motore_test)
        ora += timedelta(seconds=900)
    barriera = Barrier(concorrenti)

    def tenta(_):
        barriera.wait()
        try:
            prenota("ip", "192.0.2.1", ora, engine=motore_test)
            return True
        except TroppiTentativi:
            return False

    with ThreadPoolExecutor(max_workers=concorrenti) as pool:
        assert sum(pool.map(tenta, range(concorrenti))) == 5
    with motore_test.connect() as c:
        row = c.execute(text("SELECT chiave, tentativi FROM limite_login")).one()
        assert len(row.chiave) == 64 and row.tentativi == 6
        assert "192.0.2.1" not in row.chiave


def test_limite_database_non_disponibile_blocca(monkeypatch):
    from sqlalchemy.exc import OperationalError

    class MotoreGuasto:
        def begin(self):
            raise OperationalError("dato sensibile", {}, Exception("segreto"))

    with pytest.raises(LimiteNonDisponibile) as e:
        prenota("ip", "192.0.2.1", ORA, engine=MotoreGuasto())
    assert str(e.value) == "Accesso temporaneamente non disponibile."


def test_limite_condiviso_tra_processi_indipendenti(motore_test):
    ambiente = os.environ.copy()
    ambiente["DATABASE_URL"] = leggi_impostazioni().database_url_test
    ambiente["DATABASE_URL_TEST"] = ambiente["DATABASE_URL"]
    codice = """
import sys
from datetime import datetime, timezone
from sqlalchemy import make_url, text
from app.core.db import motore
from app.core.config import leggi_impostazioni
from app.core.limite_login import prenota, TroppiTentativi
u = make_url(leggi_impostazioni().database_url)
assert (u.database, u.host, u.port) == ('adflow_test', '127.0.0.1', 5432)
with motore().connect() as c:
    assert c.scalar(text('SELECT current_database()')) == 'adflow_test'
try:
    prenota('account', 'processi@example.com', datetime.now(timezone.utc))
except TroppiTentativi:
    sys.exit(3)
"""

    def processo(_):
        risultato = subprocess.run(
            [sys.executable, "-c", codice],
            env=ambiente,
            capture_output=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        assert risultato.returncode in (0, 3), "Processo di verifica fallito."
        return risultato.returncode

    with ThreadPoolExecutor(max_workers=6) as pool:
        risultati = list(pool.map(processo, range(6)))
    assert risultati.count(0) == 5
    assert risultati.count(3) == 1


def test_ip_blocca_account_diversi_e_payload_malformati(client, motore_test):
    for n in range(5):
        assert (
            client.post(
                "/api/auth/login",
                json={"email": f"u{n}@example.com", "password": "errata"},
            ).status_code
            == 401
        )
    risposta = client.post("/api/auth/login", content="{")
    assert risposta.status_code == 429
    assert 1 <= int(risposta.headers["retry-after"]) <= 900
    assert risposta.headers["cache-control"] == "no-store"
    assert client.get("/api/health").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204


def test_payload_malformati_consumano_limite_ip(client):
    for _ in range(5):
        assert client.post("/api/auth/login", content="{").status_code == 422
    assert client.post("/api/auth/login", content="{").status_code == 429


def test_account_blocca_ip_diversi_e_normalizza_case(db):
    from app.core.db import get_db

    app.dependency_overrides[get_db] = lambda: db
    try:
        for n in range(6):
            with TestClient(app, client=(f"192.0.2.{n+1}", 5000)) as c:
                email = " Persona@EXAMPLE.COM " if n % 2 else "persona@example.com"
                risposta = c.post(
                    "/api/auth/login", json={"email": email, "password": "errata"}
                )
                assert risposta.status_code == (401 if n < 5 else 429)
    finally:
        app.dependency_overrides.clear()


def test_successi_contano_senza_bloccare_sessione_corrente(db, client):
    record = utente(db)
    for _ in range(5):
        assert (
            client.post(
                "/api/auth/login",
                json={"email": record.email, "password": PASSWORD_DI_PROVA},
            ).status_code
            == 200
        )
    assert (
        client.post(
            "/api/auth/login",
            json={"email": record.email, "password": PASSWORD_DI_PROVA},
        ).status_code
        == 429
    )
    assert client.get("/api/auth/me").status_code == 200


def test_commit_fallito_non_restituisce_cookie(db, client, motore_test):
    from app.core.db import get_db
    from app.moduli.accesso.models import Sessione
    from sqlalchemy import select

    record = utente(db)

    def commit_fallito():
        with db.begin_nested() as savepoint:
            yield db
            savepoint.rollback()
            raise RuntimeError("Errore commit simulato")

    app.dependency_overrides[get_db] = commit_fallito
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.post(
                "/api/auth/login",
                json={"email": record.email, "password": PASSWORD_DI_PROVA},
            )
            assert r.status_code == 500
            assert "set-cookie" not in r.headers
        assert (
            db.scalar(select(Sessione.id).where(Sessione.utente_id == record.id))
            is None
        )
        with motore_test.connect() as c:
            assert c.scalar(text("SELECT count(*) FROM limite_login")) == 2
    finally:
        app.dependency_overrides[get_db] = lambda: db


def test_guasto_limite_http_503_senza_dati(client, monkeypatch, eventi):
    from app.core import limite_login
    from sqlalchemy.exc import OperationalError

    class Guasto:
        def begin(self):
            raise OperationalError("email-pii", {}, Exception("password-pii"))

    monkeypatch.setattr(limite_login, "motore", lambda: Guasto())
    r = client.post(
        "/api/auth/login",
        json={"email": "persona@example.com", "password": "password-pii"},
    )
    assert r.status_code == 503
    assert r.json() == {"detail": "Accesso temporaneamente non disponibile."}
    assert eventi[-1]["event_type"] == "login_limiter_unavailable"
    assert "pii" not in json.dumps(eventi)


@pytest.fixture
def eventi():
    messaggi = []

    class Raccolta(logging.Handler):
        def emit(self, record):
            messaggi.append(json.loads(record.getMessage()))

    handler = Raccolta()
    logger.addHandler(handler)
    yield messaggi
    logger.removeHandler(handler)


def test_log_serializzato_senza_pii_e_id_generato(client, eventi):
    r = client.post(
        "/api/auth/login",
        json={"email": "pii@example.com", "password": "SegretoFinto"},
        headers={
            "X-Request-ID": "PII-attaccante",
            "Authorization": "Bearer segreto",
            "Cookie": "adflow_sessione=token",
        },
    )
    assert r.status_code == 401
    assert eventi[-1]["event_type"] == "auth_failure"
    assert eventi[-1]["request_id"] == r.headers["x-request-id"]
    assert len(r.headers["x-request-id"]) == 32
    assert eventi[-1]["security_event"] is True
    assert set(eventi[-1]) == {
        "security_event",
        "event_type",
        "esito",
        "timestamp",
        "request_id",
    }
    serializzato = json.dumps(eventi)
    for valore in [
        "pii@example.com",
        "SegretoFinto",
        "PII-attaccante",
        "Bearer",
        "adflow_sessione",
        "testclient",
    ]:
        assert valore not in serializzato
    assert client.get("/api/auth/me").status_code == 401
    assert eventi[-1]["event_type"] == "invalid_session"
    assert client.post("/api/auth/login", content="{").status_code == 422
    assert eventi[-1]["event_type"] == "auth_invalid_input"


def test_log_rate_limit_e_ruolo(db, client, eventi):
    record = utente(db, "artigiano")
    assert (
        client.post(
            "/api/auth/login",
            json={"email": record.email, "password": PASSWORD_DI_PROVA},
        ).status_code
        == 200
    )
    controllo = service.richiede_ruolo("admin")
    # Una rotta isolata usa lo stesso handler globale e middleware.
    percorso = "/api/test-sicurezza-ruolo"
    app.add_api_route(percorso, lambda u=Depends(controllo): {}, methods=["GET"])
    try:
        assert client.get(percorso).status_code == 403
        assert eventi[-1]["event_type"] == "role_denied"
    finally:
        app.router.routes[:] = [
            r for r in app.router.routes if getattr(r, "path", None) != percorso
        ]
    for _ in range(4):
        client.post(
            "/api/auth/login", json={"email": record.email, "password": "errata"}
        )
    assert client.post("/api/auth/login", content="{").status_code == 429
    assert eventi[-1]["event_type"] == "login_rate_limited"


def test_guasto_logger_preserva_http(client, monkeypatch):
    def guasto(*a, **k):
        raise OSError("sink guasto")

    monkeypatch.setattr(logger, "info", guasto)
    assert client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize("trusted,secure", [("127.0.0.1", True), ("192.0.2.1", False)])
def test_proxy_fidato_cookie_login_logout(db, trusted, secure):
    from app.core.db import get_db

    record = utente(db)
    app.dependency_overrides[get_db] = lambda: db
    wrapper = ProxyHeadersMiddleware(app, trusted_hosts=trusted)
    try:
        with TestClient(wrapper, client=("127.0.0.1", 5000)) as c:
            h = {"X-Forwarded-Proto": "https"}
            r = c.post(
                "/api/auth/login",
                json={"email": record.email, "password": PASSWORD_DI_PROVA},
                headers=h,
            )
            assert r.status_code == 200
            assert ("; Secure" in r.headers["set-cookie"]) is secure
            for flag in ["HttpOnly", "SameSite=lax", "Path=/"]:
                assert flag in r.headers["set-cookie"]
            r = c.post("/api/auth/logout", headers=h)
            assert ("; Secure" in r.headers["set-cookie"]) is secure
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "campo,valore",
    [
        ("cookie_secure", False),
        ("email_test_environment", True),
        ("login_limite_segreto", "corto"),
    ],
)
def test_produzione_rifiuta_configurazione_insicura(campo, valore):
    dati = dict(
        database_url="finto",
        database_url_test="finto",
        ambiente="produzione",
        login_limite_segreto="a" * 40,
    )
    dati[campo] = valore
    with pytest.raises(ValidationError):
        Impostazioni(_env_file=None, **dati)


def test_cookie_produzione_sempre_secure(client, monkeypatch):
    from starlette.requests import Request

    monkeypatch.setattr(leggi_impostazioni(), "ambiente", "produzione")
    assert cookie_sicuro(Request({"type": "http", "scheme": "http"}))


@pytest.mark.parametrize(
    "email",
    [
        "a..b@example.com",
        ".a@example.com",
        "a@example..com",
        "a@localhost",
        "a@[127.0.0.1]",
        "a@-example.com",
    ],
)
def test_email_casi_edge_rifiutati(email):
    with pytest.raises(DatiNonValidi, match="Indirizzo email non valido"):
        normalizza_email(email)


def test_email_unicode_senza_dns_e_login_legacy(db, client, monkeypatch):
    import dns.resolver

    def vietato(*a, **k):
        pytest.fail("Nessuna richiesta DNS ammessa")

    monkeypatch.setattr(dns.resolver.Resolver, "resolve", vietato)
    assert normalizza_email("  E\u0301@example.com ") == "é@example.com"
    monkeypatch.setattr(leggi_impostazioni(), "email_test_environment", False)
    with pytest.raises(DatiNonValidi):
        normalizza_email("nuovo@example.test")
    record = utente(db, email="legacy@example.test")
    assert (
        client.post(
            "/api/auth/login",
            json={"email": record.email, "password": PASSWORD_DI_PROVA},
        ).status_code
        == 200
    )
    nuovo = service.crea_utente(db, "É@example.com", "password", "Nome", "artigiano")
    with pytest.raises(DatiNonValidi, match="Email già registrata"):
        service.crea_utente(db, "E\u0301@example.com", "password", "Nome", "artigiano")
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "E\u0301@example.com", "password": "password"},
        ).json()["id"]
        == nuovo.id
    )


def test_creazione_non_rende_ambiguo_account_unicode_storico(db, client):
    storico = utente(db, email="e\u0301@example.com")
    with pytest.raises(DatiNonValidi, match="Email già registrata"):
        service.crea_utente(db, "é@example.com", "password", "Nome", "admin")
    assert (
        client.post(
            "/api/auth/login",
            json={"email": storico.email, "password": PASSWORD_DI_PROVA},
        ).json()["id"]
        == storico.id
    )


def test_migrazione_downgrade_upgrade_solo_test(motore_test):
    cfg = Config("alembic.ini")
    cfg.attributes["url"] = leggi_impostazioni().database_url_test
    assert cfg.attributes["url"].endswith("/adflow_test")
    command.downgrade(cfg, "007")
    with motore_test.connect() as c:
        assert c.scalar(text("SELECT to_regclass('limite_login')")) is None
    command.upgrade(cfg, "head")
    with motore_test.connect() as c:
        assert c.scalar(text("SELECT to_regclass('limite_login')")) == "limite_login"
