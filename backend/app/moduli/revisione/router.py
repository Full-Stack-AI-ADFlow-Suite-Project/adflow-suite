"""Endpoint del modulo revisione: chiamano service.py, senza logica di business."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.orologio import adesso
from app.moduli.accesso import service as accesso

from . import service, sospensione
from .schemas import CampagnaRiattiva, VediCampagnaSchema

router = APIRouter(tags=["revisione"])


@router.get("/campagne/{campagna_id}/post", response_model=VediCampagnaSchema)
def vedi_campagna(
    campagna_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    stato: str | None = None,
) -> VediCampagnaSchema:
    """Vedi campagna in ogni stato dopo l'invio, per l'operatore (CA-60)."""
    return service.vedi_campagna(db, campagna_id, stato)


@router.post("/campagne/{campagna_id}/approva")
def approva_campagna(
    campagna_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Approva in blocco: post approvati, campagna attiva (R-14, CA-21/22)."""
    service.approva(db, campagna_id, utente, ora)
    return {"stato": "attiva"}


@router.post("/campagne/{campagna_id}/prosegui")
def prosegui_campagna(
    campagna_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
) -> dict[str, str]:
    """Riparte la generazione da un piano debole (R-20, CA-49)."""
    service.prosegui(db, campagna_id, utente)
    return {"stato": "in_generazione"}


@router.post("/campagne/{campagna_id}/sospendi")
def sospendi_campagna(
    campagna_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
) -> dict[str, str]:
    """Sospende la pubblicazione di una campagna attiva (R-33, CA-32)."""
    sospensione.sospendi(db, campagna_id, utente)
    return {"stato": "sospesa"}


@router.post("/campagne/{campagna_id}/riattiva")
def riattiva_campagna(
    campagna_id: int,
    corpo: CampagnaRiattiva,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Riattiva una sospesa: gli arretrati scelti escono subito, gli altri
    diventano ``annullato`` (R-33, CA-32)."""
    sospensione.riattiva(db, campagna_id, utente, corpo.pubblica_ora, ora)
    return {"stato": "attiva"}


@router.post("/campagne/{campagna_id}/annulla")
def annulla_campagna(
    campagna_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Annulla una campagna attiva o sospesa: i post ``approvato`` diventano
    ``annullato`` (R-33, CA-32)."""
    sospensione.annulla(db, campagna_id, utente, ora)
    return {"stato": "annullata"}
