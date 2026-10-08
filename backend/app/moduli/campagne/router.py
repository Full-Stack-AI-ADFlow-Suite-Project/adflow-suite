"""Endpoint del modulo campagne: chiamano service.py, senza logica di business."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.orologio import adesso
from app.moduli.accesso.service import richiede_ruolo, utente_corrente

from . import service
from .schemas import CampagnaCrea, CampagnaDettaglio, CampagnaElencoItem

router = APIRouter(tags=["campagne"])


@router.post("/campagne", response_model=CampagnaDettaglio, status_code=201)
def crea_campagna(
    dati: CampagnaCrea,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> CampagnaDettaglio:
    """Crea una nuova campagna in bozza per l'artigiano autenticato (CA-09, CA-10, CA-11, CA-12, CA-48)."""
    campagna = service.crea_bozza(db, utente.id, dati, ora)
    return service.dettaglio_campagna(db, utente.id, utente.ruolo, campagna.id)


@router.get("/campagne", response_model=list[CampagnaElencoItem])
def elenca_campagne(
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(utente_corrente)],
    stato: Annotated[list[str] | None, Query()] = None,
) -> list[CampagnaElencoItem]:
    """Elenca le campagne accessibili all'utente (supporta stati multipli e include bottega/città per l'operatore)."""
    return service.elenca_campagne(db, utente.id, utente.ruolo, stato)


@router.get("/campagne/{id}", response_model=CampagnaDettaglio)
def dettaglio_campagna(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(utente_corrente)],
) -> CampagnaDettaglio:
    """Restituisce il dettaglio della campagna (CA-04: 404 se l'artigiano accede a un'altra)."""
    return service.dettaglio_campagna(db, utente.id, utente.ruolo, id)
