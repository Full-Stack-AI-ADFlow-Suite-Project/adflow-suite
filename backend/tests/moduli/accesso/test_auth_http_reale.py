"""Un server Uvicorn separato, richieste TCP e cookie gestiti dal client HTTP."""

import json
import os
import socket
import subprocess
import sys
import time
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, ProxyHandler, Request, build_opener
from uuid import uuid4

from sqlalchemy import delete, make_url, select, text
from sqlalchemy.orm import Session

from app.core.config import leggi_impostazioni
from app.moduli.accesso.models import Sessione, Utente
from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente


def test_server_reale_login_rotazione_logout_e_input_invalidi(motore_test):
    url_test = leggi_impostazioni().database_url_test
    url = make_url(url_test)
    assert (url.database, url.host, url.port) == ("adflow_test", "127.0.0.1", 5432)
    with motore_test.connect() as connessione:
        assert connessione.scalar(text("select current_database()")) == "adflow_test"
    email = f"{uuid4().hex}@example.test"
    with Session(motore_test) as db, db.begin():
        record_id = utente(db, email=email).id

    with socket.socket() as socket_libero:
        socket_libero.bind(("127.0.0.1", 0))
        porta = socket_libero.getsockname()[1]

    ambiente = os.environ.copy()
    # URL solo nell'ambiente del processo figlio: nessun file .env modificato.
    ambiente["DATABASE_URL"] = url_test
    ambiente["DATABASE_URL_TEST"] = url_test
    codice = """
import asyncio, sys, uvicorn
from sqlalchemy import make_url, text
from app.core.config import leggi_impostazioni
from app.core.db import motore
i = leggi_impostazioni()
assert i.database_url == i.database_url_test
u = make_url(i.database_url)
assert (u.database, u.host, u.port) == ('adflow_test', '127.0.0.1', 5432)
with motore().connect() as c:
    assert c.scalar(text('select current_database()')) == 'adflow_test'
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
uvicorn.run('app.main:app', host='127.0.0.1', port=int(sys.argv[1]),
            loop='asyncio', access_log=False, log_level='critical')
"""
    processo = None
    cookie = CookieJar()
    client = build_opener(ProxyHandler({}), HTTPCookieProcessor(cookie))
    base = f"http://127.0.0.1:{porta}"

    def richiesta(percorso, dati=None, method=None, headers=None):
        corpo = json.dumps(dati).encode() if dati is not None else None
        intestazioni = {"Content-Type": "application/json"} if corpo else {}
        intestazioni.update(headers or {})
        req = Request(base + percorso, data=corpo, headers=intestazioni, method=method)
        try:
            risposta = client.open(req, timeout=3)
        except HTTPError as errore:
            risposta = errore
        with risposta:
            body = risposta.read()
            return risposta.code, risposta.headers, json.loads(body) if body else None

    try:
        processo = subprocess.Popen(
            [sys.executable, "-c", codice, str(porta)],
            env=ambiente,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        scadenza = time.monotonic() + 25
        while True:
            assert (
                processo.poll() is None
            ), "Il server di test è terminato prima dell'avvio."
            try:
                if richiesta("/api/health")[0] == 200:
                    break
            except (URLError, TimeoutError):
                pass
            assert time.monotonic() < scadenza, "Avvio del server di test scaduto."
            time.sleep(0.1)

        assert richiesta("/api/auth/me")[0] == 401
        status, headers, body = richiesta(
            "/api/auth/login", {"email": email, "password": PASSWORD_DI_PROVA}
        )
        assert status == 200
        assert body["id"] == record_id
        assert "httponly" in headers["Set-Cookie"].lower()
        vecchio_token = next(iter(cookie)).value
        assert richiesta("/api/auth/me")[2]["id"] == record_id
        assert (
            richiesta("/api/auth/login", {"email": email, "password": "Errata"})[0]
            == 401
        )
        assert next(iter(cookie)).value == vecchio_token
        assert (
            richiesta(
                "/api/auth/login", {"email": email, "password": PASSWORD_DI_PROVA}
            )[0]
            == 200
        )
        assert next(iter(cookie)).value != vecchio_token
        assert (
            richiesta(
                "/api/auth/me", headers={"Cookie": f"adflow_sessione={vecchio_token}"}
            )[0]
            == 401
        )
        assert richiesta("/api/auth/logout", method="POST")[0] == 204
        assert list(cookie) == []
        assert richiesta("/api/auth/me")[0] == 401
        status, _, body = richiesta(
            "/api/auth/login", {"password": "SoloCredenzialeFinta"}
        )
        assert status == 422
        assert body == {"detail": "Dati di accesso non validi."}
        assert (
            richiesta(
                "/api/auth/login",
                {"email": "a\x00@example.test", "password": PASSWORD_DI_PROVA},
            )[0]
            == 422
        )
        with Session(motore_test) as db:
            assert (
                db.scalar(select(Sessione.id).where(Sessione.utente_id == record_id))
                is None
            )
    finally:
        if processo is not None:
            processo.terminate()
            try:
                processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                processo.kill()
                processo.wait(timeout=5)
        with motore_test.begin() as connessione:
            connessione.execute(delete(Sessione).where(Sessione.utente_id == record_id))
            connessione.execute(delete(Utente).where(Utente.id == record_id))
