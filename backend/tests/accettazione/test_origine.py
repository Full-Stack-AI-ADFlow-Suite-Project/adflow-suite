"""Il controllo di Origin sulle operazioni che cambiano stato (T4-102, R-02).

L'ipotesi R-01 di §3 («nessun controllo di Origin o Sec-Fetch-Site») va provata
**in produzione**, perché `ProtezioneCSRF` (T3-09) è attiva solo con
`AMBIENTE=produzione`: si avvia quindi un server Uvicorn vero, su un porto
libero, con l'ambiente di produzione, e si mandano richieste TCP con `Origin`
esterna, senza `Origin` e della stessa origine.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from sqlalchemy import make_url, text
from sqlalchemy.orm import Session

from app.core.config import leggi_impostazioni
from app.moduli.accesso.models import Utente
from tests.moduli.accesso.fabbrica import utente

MESSAGGIO = "Origine della richiesta non consentita."


def _aspetta_il_server(controllore, url: str, secondi: int = 30) -> None:
    for _ in range(secondi * 10):
        try:
            with controllore.open(Request(url), timeout=1):
                return
        except HTTPError:
            return
        except URLError:
            time.sleep(0.1)
    raise RuntimeError("il server di prova non è partito")


def test_in_produzione_l_origine_esterna_e_rifiutata(motore_test):
    """Server in produzione: Origin esterna o mancante → 403; stessa origine passa (T4-102)."""
    url_test = leggi_impostazioni().database_url_test
    url = make_url(url_test)
    assert (url.database, url.port) == ("adflow_test", 5432)
    assert url.host in {"127.0.0.1", "localhost"}

    with socket.socket() as porto_libero:
        porto_libero.bind(("127.0.0.1", 0))
        porta = porto_libero.getsockname()[1]

    ambiente = os.environ.copy()
    ambiente.update(
        DATABASE_URL=url_test,
        DATABASE_URL_TEST=url_test,
        AI_PROVIDER="finto",
        SOCIAL_PROVIDER="finto",
        AMBIENTE="produzione",
        LOGIN_LIMITE_SEGRETO="segreto-di-prova-della-corsia-10-accettazione",
        OROLOGIO_GIORNI_AVANTI="0",
        EMAIL_TEST_ENVIRONMENT="false",
    )
    codice = """
import asyncio, sys, uvicorn
from sqlalchemy import make_url, text
from app.core.config import leggi_impostazioni
from app.core.db import motore
i = leggi_impostazioni()
assert i.ambiente == 'produzione', 'il server non è in produzione'
u = make_url(i.database_url)
assert (u.database, u.port) == ('adflow_test', 5432)
with motore().connect() as c:
    assert c.scalar(text('SELECT current_database()')) == 'adflow_test'
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
uvicorn.run('app.main:app', host='127.0.0.1', port=int(sys.argv[1]),
            loop='asyncio', access_log=False, log_level='critical')
"""
    processo = None
    client = build_opener(ProxyHandler({}))
    base = f"http://127.0.0.1:{porta}"

    def richiesta(percorso, dati=None, intestazioni=None, metodo=None):
        corpo = json.dumps(dati).encode() if dati is not None else b""
        intestarie = {"Content-Type": "application/json"}
        intestarie.update(intestazioni or {})
        req = Request(
            base + percorso, data=corpo or None, headers=intestarie, method=metodo
        )
        try:
            risposta = client.open(req, timeout=5)
        except HTTPError as errore:
            risposta = errore
        with risposta:
            corpo_risposta = risposta.read()
            return risposta.code, json.loads(corpo_risposta) if corpo_risposta else None

    try:
        processo = subprocess.Popen(
            [sys.executable, "-c", codice, str(porta)],
            env=ambiente,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        _aspetta_il_server(client, f"{base}/api/health")

        # Origin di un altro dominio su un'operazione che cambia stato
        codice_r, corpo = richiesta(
            "/api/campagne",
            dati={},
            intestazioni={"Origin": "https://attaccante.example.test"},
            metodo="POST",
        )
        assert codice_r == 403, f"atteso 403, risposta {codice_r}: {corpo}"
        assert corpo == {"detail": MESSAGGIO}

        # Sottodominio dello stesso sito: SameSite=Lax non lo fermerebbe
        codice_r, corpo = richiesta(
            "/api/campagne",
            dati={},
            intestazioni={"Origin": "https://malevolo.app.example.test"},
            metodo="POST",
        )
        assert codice_r == 403, f"atteso 403, risposta {codice_r}: {corpo}"

        # Nessuna Origin: i client non-browser devono dichiararla
        codice_r, corpo = richiesta("/api/campagne", dati={}, metodo="POST")
        assert codice_r == 403, f"atteso 403, risposta {codice_r}: {corpo}"

        # Stessa origine: il controllo passa, e senza sessione arriva l'401
        codice_r, corpo = richiesta(
            "/api/campagne",
            dati={},
            intestazioni={"Origin": f"http://127.0.0.1:{porta}"},
            metodo="POST",
        )
        assert (
            codice_r == 401
        ), f"atteso 401 (sessione mancante), risposta {codice_r}: {corpo}"

        # Le letture non sono toccate dal controllo
        codice_r, _ = richiesta(
            "/api/health",
            intestazioni={"Origin": "https://attaccante.example.test"},
        )
        assert codice_r == 200
    finally:
        if processo is not None:
            processo.terminate()
            processo.wait(timeout=10)
            processo.stdout and processo.stdout.close()
            if processo.stderr:
                processo.stderr.close()
