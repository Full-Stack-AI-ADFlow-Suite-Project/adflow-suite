"""HTTPS reale → proxy di test → Uvicorn, senza servizi esterni."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import socket
import ssl
import subprocess
import sys
from threading import Thread
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener, HTTPSHandler
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

import pytest
from sqlalchemy import delete, make_url, text
from sqlalchemy.orm import Session

from app.core.config import leggi_impostazioni
from app.moduli.accesso.models import Utente, Sessione
from tests.moduli.accesso.fabbrica import utente, PASSWORD_DI_PROVA


@pytest.mark.parametrize(
    "fidato,via_proxy,secure", [("127.0.0.1", True, True), ("192.0.2.1", False, False)]
)
def test_catena_https_e_proxy_non_fidato(
    motore_test, tmp_path, fidato, via_proxy, secure
):
    url_test = leggi_impostazioni().database_url_test
    u = make_url(url_test)
    assert (u.database, u.port) == ("adflow_test", 5432)
    assert u.host in {"127.0.0.1", "localhost"}
    email = f"{uuid4().hex}@example.test"
    with Session(motore_test) as db, db.begin():
        record_id = utente(db, email=email).id
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    ambiente = os.environ.copy()
    ambiente["DATABASE_URL"] = url_test
    ambiente["DATABASE_URL_TEST"] = url_test
    codice = """
import asyncio, sys, uvicorn
from sqlalchemy import make_url, text
from app.core.config import leggi_impostazioni
from app.core.db import motore
u=make_url(leggi_impostazioni().database_url)
assert (u.database,u.port)==('adflow_test',5432)
assert u.host in {'127.0.0.1','localhost'}
with motore().connect() as c:
    assert c.scalar(text('SELECT current_database()'))=='adflow_test'
if sys.platform=='win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
uvicorn.run('app.main:app',host='127.0.0.1',port=int(sys.argv[1]),
    loop='asyncio',proxy_headers=True,forwarded_allow_ips=sys.argv[2],
    access_log=False,log_level='critical')
"""
    processo = None
    proxy = None
    thread = None
    diretto = build_opener(ProxyHandler({}))

    class Proxy(BaseHTTPRequestHandler):
        def do_POST(self):
            corpo = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            r = Request(
                f"http://127.0.0.1:{porta}" + self.path,
                data=corpo,
                headers={
                    "Content-Type": "application/json",
                    "X-Forwarded-Proto": "https",
                    "X-Forwarded-For": self.client_address[0],
                },
                method="POST",
            )
            try:
                risposta = diretto.open(r, timeout=5)
            except HTTPError as e:
                risposta = e
            with risposta:
                dati = risposta.read()
                self.send_response(risposta.code)
                for nome in ["Set-Cookie", "X-Request-ID", "Content-Type"]:
                    if nome in risposta.headers:
                        self.send_header(nome, risposta.headers[nome])
                self.send_header("Content-Length", str(len(dati)))
                self.end_headers()
                self.wfile.write(dati)

        def log_message(self, *args):
            pass

    try:
        processo = subprocess.Popen(
            [sys.executable, "-c", codice, str(porta), fidato],
            env=ambiente,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        scadenza = time.monotonic() + 25
        while True:
            assert processo.poll() is None, "Server terminato prima dell'avvio"
            try:
                with diretto.open(f"http://127.0.0.1:{porta}/api/health", timeout=1):
                    break
            except (URLError, TimeoutError):
                assert time.monotonic() < scadenza, "Avvio Uvicorn scaduto"
                time.sleep(0.1)
        client = diretto
        base = f"http://127.0.0.1:{porta}"
        if via_proxy:
            cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
            privata = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
            ora = datetime.now(timezone.utc)
            certificato = (
                x509.CertificateBuilder()
                .subject_name(nome)
                .issuer_name(nome)
                .public_key(privata.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(ora - timedelta(minutes=1))
                .not_valid_after(ora + timedelta(days=1))
                .add_extension(
                    x509.SubjectAlternativeName(
                        [x509.IPAddress(ip_address("127.0.0.1"))]
                    ),
                    critical=False,
                )
                .sign(privata, hashes.SHA256())
            )
            key.write_bytes(
                privata.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            cert.write_bytes(certificato.public_bytes(serialization.Encoding.PEM))
            proxy = ThreadingHTTPServer(("127.0.0.1", 0), Proxy)
            tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls.load_cert_chain(cert, key)
            proxy.socket = tls.wrap_socket(proxy.socket, server_side=True)
            thread = Thread(target=proxy.serve_forever, daemon=True)
            thread.start()
            client = build_opener(
                ProxyHandler({}),
                HTTPSHandler(context=ssl.create_default_context(cafile=str(cert))),
            )
            base = f"https://127.0.0.1:{proxy.server_port}"
        for percorso, dati in [
            ("login", {"email": email, "password": PASSWORD_DI_PROVA}),
            ("logout", {}),
        ]:
            req = Request(
                base + "/api/auth/" + percorso,
                data=json.dumps(dati).encode(),
                headers={
                    "Content-Type": "application/json",
                    "X-Forwarded-Proto": "https",
                },
                method="POST",
            )
            with client.open(req, timeout=5) as r:
                assert r.code == (200 if percorso == "login" else 204)
                cookie = r.headers["Set-Cookie"]
                assert ("; Secure" in cookie) is secure
                assert all(
                    flag in cookie for flag in ["HttpOnly", "SameSite=lax", "Path=/"]
                )
                assert len(r.headers["X-Request-ID"]) == 32
    finally:
        if proxy:
            proxy.shutdown()
            proxy.server_close()
        if thread:
            thread.join(timeout=5)
        if processo:
            processo.terminate()
            try:
                processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                processo.kill()
                processo.wait(timeout=5)
        with motore_test.begin() as c:
            # Attende eventuali FK lock di una transazione in chiusura nel figlio.
            c.execute(
                text("SELECT id FROM utente WHERE id=:id FOR UPDATE"), {"id": record_id}
            )
            c.execute(delete(Sessione).where(Sessione.utente_id == record_id))
            c.execute(delete(Utente).where(Utente.id == record_id))
