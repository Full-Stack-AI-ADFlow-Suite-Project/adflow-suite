"""Endpoint del modulo accesso: chiamano service.py, senza logica di business."""

from datetime import datetime
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.db import get_db
from app.core.orologio import adesso
from app.core.config import leggi_impostazioni
from app.core.limite_login import prenota
from app.core.eventi_sicurezza import registra, id_richiesta

from . import service
from .models import Utente
from .schemas import Login, UtentePubblico
from .email import identita_login


def cookie_sicuro(request: Request) -> bool:
    return service.cookie_sicuro(request)


class RottaAccesso(APIRoute):
    """Non riflette dati del login nei dettagli degli errori di validazione."""

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        originale = super().get_route_handler()

        async def senza_credenziali(request: Request) -> Response:
            if request.url.path == "/api/auth/login" and request.method == "POST":
                await run_in_threadpool(
                    prenota,
                    "ip",
                    request.client.host if request.client else "assente",
                    adesso(),
                )
            try:
                return await originale(request)
            except RequestValidationError:
                registra("auth_invalid_input", id_richiesta(request))
                return JSONResponse(
                    status_code=422,
                    content={"detail": "Dati di accesso non validi."},
                    headers={"Cache-Control": "no-store"},
                )

        return senza_credenziali


router = APIRouter(tags=["accesso"], route_class=RottaAccesso)


@router.post("/auth/login", response_model=UtentePubblico)
def login(
    dati: Login,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db, scope="function")],
    ora: Annotated[datetime, Depends(adesso)],
) -> Utente:
    prenota("account", identita_login(dati.email), ora)
    utente, token = service.login(
        db, dati.email, dati.password, ora, request.cookies.get(service.COOKIE_SESSIONE)
    )
    response.set_cookie(
        service.COOKIE_SESSIONE,
        token,
        max_age=int(service.durata_sessione(utente.ruolo).total_seconds()),
        httponly=True,
        secure=cookie_sicuro(request),
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return utente


@router.post("/auth/logout", status_code=204)
def logout(
    request: Request, db: Annotated[Session, Depends(get_db, scope="function")]
) -> Response:
    service.logout(db, request.cookies.get(service.COOKIE_SESSIONE))
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(
        service.COOKIE_SESSIONE,
        path="/",
        httponly=True,
        secure=cookie_sicuro(request),
        samesite="lax",
    )
    return response


@router.get("/auth/me", response_model=UtentePubblico)
def me(
    response: Response, utente: Annotated[Utente, Depends(service.utente_corrente)]
) -> Utente:
    response.headers["Cache-Control"] = "no-store"
    return utente
