"""Rifiuta richieste browser state-changing provenienti da un'altra origine."""

import json
from urllib.parse import urlsplit

METODI_CON_STATO = frozenset({"POST", "PUT", "PATCH", "DELETE"})
MESSAGGIO = "Origine della richiesta non consentita."


def _origine(valore: str) -> tuple[str, str, int] | None:
    """Normalizza un Origin valido senza accettare path, credenziali o query."""
    try:
        parti = urlsplit(valore)
        schema = parti.scheme.lower()
        host = parti.hostname
        porta = parti.port
    except ValueError:
        return None

    if (
        schema not in {"http", "https"}
        or not host
        or parti.username is not None
        or parti.password is not None
        or parti.path not in {"", "/"}
        or parti.query
        or parti.fragment
    ):
        return None

    porta_effettiva = porta if porta is not None else (443 if schema == "https" else 80)
    return schema, host.rstrip(".").lower(), porta_effettiva


class ProtezioneCSRF:
    """In produzione richiede Origin uguale allo schema e host della richiesta.

    Le richieste senza Origin sono rifiutate per i metodi che possono cambiare
    stato; i client non-browser devono inviare esplicitamente la propria origine.
    """

    def __init__(self, app, *, abilitata: bool = True):
        self.app = app
        self.abilitata = abilitata

    async def __call__(self, scope, receive, send):
        if (
            not self.abilitata
            or scope["type"] != "http"
            or scope["method"].upper() not in METODI_CON_STATO
        ):
            return await self.app(scope, receive, send)

        intestazioni = dict(scope["headers"])
        origin = intestazioni.get(b"origin")
        host = intestazioni.get(b"host")
        if origin is None or host is None:
            return await self._rifiuta(send)

        origine_richiesta = _origine(origin.decode("latin-1"))
        origine_attesa = _origine(f"{scope['scheme']}://{host.decode('latin-1')}")
        if origine_richiesta is None or origine_richiesta != origine_attesa:
            return await self._rifiuta(send)

        return await self.app(scope, receive, send)

    @staticmethod
    async def _rifiuta(send) -> None:
        corpo = json.dumps({"detail": MESSAGGIO}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(corpo)).encode()),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": corpo})
