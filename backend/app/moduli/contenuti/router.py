"""Endpoint del modulo contenuti: chiamano service.py, senza logica di business."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.moduli.accesso.service import richiede_ruolo

from . import service
from .schemas import CalendarioCampagna

router = APIRouter(tags=["contenuti"])


@router.get("/campagne/{id}/calendario", response_model=CalendarioCampagna)
def calendario(
    id: int,
    db: Annotated[Session, Depends(get_db, scope="function")],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano", "operatore"))],
    response: Response,
) -> CalendarioCampagna:
    response.headers["Cache-Control"] = "no-store"
    return service.calendario_campagna(db, id, utente.id, utente.ruolo)
