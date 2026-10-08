"""Endpoint del modulo artigiani: chiamano service.py, senza logica di business."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.moduli.accesso.service import richiede_ruolo

from . import service
from .schemas import CanaleCollegato

router = APIRouter(tags=["artigiani"])


@router.get("/canali", response_model=list[CanaleCollegato])
def canali(
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> list[CanaleCollegato]:
    return service.stato_canali(db, utente.id)
