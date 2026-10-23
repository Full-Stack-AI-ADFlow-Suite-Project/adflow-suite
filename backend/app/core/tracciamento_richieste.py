"""Tracciamento HTTP strutturato senza registrare dati o credenziali del client."""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import time
from uuid import uuid4

from app.core.config import leggi_impostazioni
from app.core.log_jsonl import JSONLFileHandler, id_test_redatto

logger = logging.getLogger("adflow.http")
logger.setLevel(logging.INFO)
logger.propagate = True

_formattatore = logging.Formatter("%(message)s")
if not logger.handlers:
    terminale = logging.StreamHandler()
    terminale.setFormatter(_formattatore)
    logger.addHandler(terminale)

_percorso_log = leggi_impostazioni().registro_richieste_file.strip()
if _percorso_log:
    percorso = Path(_percorso_log)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    gia_configurato = any(
        isinstance(handler, JSONLFileHandler)
        and handler.percorso.resolve() == percorso.resolve()
        for handler in logger.handlers
    )
    if not gia_configurato:
        file_log = JSONLFileHandler(percorso)
        file_log.setFormatter(_formattatore)
        logger.addHandler(file_log)

    logger_sicurezza = logging.getLogger("adflow.sicurezza")
    sicurezza_gia_configurato = any(
        isinstance(handler, JSONLFileHandler)
        and handler.percorso.resolve() == percorso.resolve()
        for handler in logger_sicurezza.handlers
    )
    if not sicurezza_gia_configurato:
        file_sicurezza = JSONLFileHandler(percorso)
        file_sicurezza.setFormatter(_formattatore)
        logger_sicurezza.addHandler(file_sicurezza)


class TracciamentoRichieste:
    """Registra inizio/esito/durata senza body, query string, header o cookie."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        stato = scope.setdefault("state", {})
        request_id = stato.get("request_id") or uuid4().hex
        test_id = id_test_redatto(os.environ.get("PYTEST_CURRENT_TEST"))
        metodo = scope.get("method", "UNKNOWN")
        percorso = scope.get("path", "")
        iniziata = time.perf_counter()
        status_code = 500
        errore = None

        _registra(
            "http_request_started",
            request_id=request_id,
            test_id=test_id,
            method=metodo,
            path=percorso,
        )

        async def invia(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, invia)
        except Exception as exc:
            errore = type(exc).__name__
            raise
        finally:
            _registra(
                "http_request_finished",
                request_id=request_id,
                test_id=test_id,
                method=metodo,
                path=percorso,
                status_code=status_code,
                duration_ms=round((time.perf_counter() - iniziata) * 1000, 2),
                exception_type=errore,
            )


def _registra(event_type: str, **campi) -> None:
    logger.info(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                **campi,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
    )
