"""Endpoint del modulo accesso: chiamano service.py, senza logica di business."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.orologio import adesso

from . import service
from .models import Utente
from .schemas import Login, UtentePubblico

router = APIRouter(tags=["accesso"])


@router.post("/auth/login", response_model=UtentePubblico)
def login(
    dati: Login,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    ora: Annotated[datetime, Depends(adesso)],
) -> Utente:
    utente, token = service.login(
        db, dati.email, dati.password, ora, request.cookies.get(service.COOKIE_SESSIONE)
    )
    response.set_cookie(
        service.COOKIE_SESSIONE,
        token,
        max_age=int(service.DURATA_SESSIONE.total_seconds()),
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return utente


@router.post("/auth/logout", status_code=204)
def logout(request: Request, db: Annotated[Session, Depends(get_db)]) -> Response:
    service.logout(db, request.cookies.get(service.COOKIE_SESSIONE))
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(
        service.COOKIE_SESSIONE,
        path="/",
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
    )
    return response


def _utente_sessione(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    ora: Annotated[datetime, Depends(adesso)],
) -> Utente:
    return service.utente_della_sessione(
        db, request.cookies.get(service.COOKIE_SESSIONE), ora
    )


@router.get("/auth/me", response_model=UtentePubblico)
def me(
    response: Response, utente: Annotated[Utente, Depends(_utente_sessione)]
) -> Utente:
    response.headers["Cache-Control"] = "no-store"
    return utente
