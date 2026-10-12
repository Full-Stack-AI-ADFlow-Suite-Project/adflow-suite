"""Endpoint del modulo revisione: chiamano service.py, senza logica di business."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.orologio import adesso
from app.moduli.accesso import service as accesso

from . import interventi, service
from .schemas import (
    PostControllato,
    PostModifica,
    PostRigenera,
    PostRiprogramma,
    VediCampagnaSchema,
)

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


@router.post("/post/{post_id}/modifica")
def modifica_post(
    post_id: int,
    corpo: PostModifica,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Modifica a mano del testo: versione `modifica_operatore` (R-30, CA-64)."""
    interventi.modifica(db, post_id, utente.id, corpo.testo, corpo.hashtag, ora)
    return {"stato": "ok"}


@router.post("/post/{post_id}/controllato")
def controllato_post(
    post_id: int,
    corpo: PostControllato,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Mette o toglie la spunta «va bene» sul post (R-30, CA-65)."""
    interventi.controllato(db, post_id, utente.id, corpo.valore, ora)
    return {"stato": "ok"}


@router.post("/post/{post_id}/rigenera")
def rigenera_post(
    post_id: int,
    corpo: PostRigenera,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Accende l'intervento e accoda il job `rigenera_post` (R-03, R-31)."""
    interventi.rigenera(
        db, post_id, corpo.modalita, corpo.testo_proposto, corpo.nota, ora
    )
    return {"stato": "in_corso"}


@router.post("/post/{post_id}/riprogramma")
def riprogramma_post(
    post_id: int,
    corpo: PostRiprogramma,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Un post fallito torna approvato con una nuova data (R-34, CA-67)."""
    interventi.riprogramma(db, post_id, utente.id, corpo.data_ora, ora)
    return {"stato": "approvato"}
