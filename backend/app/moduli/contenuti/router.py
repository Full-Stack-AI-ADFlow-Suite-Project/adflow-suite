"""Endpoint del modulo contenuti: chiamano service.py, senza logica di business."""
from datetime import date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.orologio import adesso
from app.moduli.accesso.service import richiede_ruolo

from . import service, settimana
from .schemas import CalendarioCampagna, CalendarioSettimana

router = APIRouter(tags=["contenuti"])


@router.get("/calendario", response_model=CalendarioSettimana)
def calendario_settimanale(
    db: Annotated[Session, Depends(get_db, scope="function")],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano", "operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
    response: Response,
    dal: Annotated[date | None, Query()] = None,
) -> CalendarioSettimana:
    """La settimana da lunedì a domenica: i post dell'artigiano, o di tutti (R-48)."""
    response.headers["Cache-Control"] = "no-store"
    return settimana.leggi(db, utente.id, utente.ruolo, dal, ora)


@router.get("/campagne/{id}/calendario", response_model=CalendarioCampagna)
def calendario(
    id: int,
    db: Annotated[Session, Depends(get_db, scope="function")],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano", "operatore"))],
    response: Response,
) -> CalendarioCampagna:
    response.headers["Cache-Control"] = "no-store"
    return service.calendario_campagna(db, id, utente.id, utente.ruolo)
