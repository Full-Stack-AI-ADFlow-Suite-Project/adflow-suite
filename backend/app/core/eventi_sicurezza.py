"""Eventi JSON con soli campi ammessi; nessun dato ricevuto dal client."""
from datetime import datetime, timezone
import json
import logging
from uuid import uuid4

logger = logging.getLogger("adflow.sicurezza")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def id_richiesta(request) -> str:
    valore = getattr(request.state, "request_id", None)
    if valore is None:
        valore = uuid4().hex
        request.state.request_id = valore
    return valore


def registra(event_type: str, request_id: str) -> None:
    try:
        logger.info(
            json.dumps(
                {
                    "security_event": True,
                    "event_type": event_type,
                    "esito": "negato",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": request_id,
                },
                separators=(",", ":"),
            )
        )
    except Exception:
        # Un guasto del sink non cambia l'autorizzazione né la risposta HTTP.
        pass


class CorrelazioneRichieste:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id

        async def risposta(message):
            if message["type"] == "http.response.start":
                message["headers"] = [
                    (k, v)
                    for k, v in message["headers"]
                    if k.lower() != b"x-request-id"
                ] + [(b"x-request-id", request_id.encode())]
            await send(message)

        await self.app(scope, receive, risposta)
