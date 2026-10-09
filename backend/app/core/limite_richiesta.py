"""Limite sulla dimensione delle richieste HTTP: oltre, 413 prima dei router."""

import json

from fastapi import HTTPException

MESSAGGIO = "La richiesta supera la dimensione massima consentita."


class LimiteRichiesta:
    """Rifiuta con 413 le richieste il cui body supera ``massimo`` byte.

    Con ``Content-Length`` oltre il limite risponde subito, senza leggere il body.
    Senza, conta i byte man mano che l'applicazione li legge e si ferma al limite:
    il parser multipart non arriva a scrivere su disco un file senza fine.
    """

    def __init__(self, app, massimo: int):
        self.app = app
        self.massimo = massimo

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        dichiarati = dict(scope["headers"]).get(b"content-length")
        if dichiarati is not None and dichiarati.isdigit():
            if int(dichiarati) > self.massimo:
                return await self._rifiuta(send)

        letti = 0

        async def ricevi():
            nonlocal letti
            messaggio = await receive()
            if messaggio["type"] == "http.request":
                letti += len(messaggio.get("body", b""))
                if letti > self.massimo:
                    # HTTPException attraversa la lettura del body di FastAPI
                    # e diventa la risposta 413 con {"detail": ...}
                    raise HTTPException(status_code=413, detail=MESSAGGIO)
            return messaggio

        await self.app(scope, ricevi, send)

    async def _rifiuta(self, send) -> None:
        corpo = json.dumps({"detail": MESSAGGIO}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(corpo)).encode()),
                    (b"connection", b"close"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": corpo})
