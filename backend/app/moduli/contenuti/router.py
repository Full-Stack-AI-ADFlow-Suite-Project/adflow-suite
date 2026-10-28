"""Endpoint del modulo contenuti: chiamano service.py, senza logica di business."""
from datetime import date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.orologio import adesso
from app.moduli.accesso.service import richiede_ruolo

from . import service, settimana
from .schemas import (
    CalendarioCampagna,
    CalendarioSettimana,
    ChiamataAIDettaglio,
    NumeriAI,
    PaginaChiamateAI,
)

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


# --- Storico dell'AI (R-50): solo operatore, l'admin passa ---------------------


@router.get("/storico-ai", response_model=PaginaChiamateAI)
def storico_ai(
    db: Annotated[Session, Depends(get_db, scope="function")],
    _: Annotated[Any, Depends(richiede_ruolo("operatore"))],
    response: Response,
    campagna_id: Annotated[int | None, Query()] = None,
    tipo: Annotated[str | None, Query()] = None,
    modello: Annotated[str | None, Query()] = None,
    versione_prompt: Annotated[str | None, Query()] = None,
    esito: Annotated[str | None, Query()] = None,
    dal: Annotated[date | None, Query()] = None,
    al: Annotated[date | None, Query()] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
) -> PaginaChiamateAI:
    """Le chiamate all'AI, dalla più recente, 50 per pagina; `dal` e `al` (Roma) compresi."""
    response.headers["Cache-Control"] = "no-store"
    return service.storico_ai(
        db,
        campagna_id=campagna_id,
        tipo=tipo,
        modello=modello,
        versione_prompt=versione_prompt,
        esito=esito,
        dal=dal,
        al=al,
        pagina=pagina,
    )


# `/storico-ai/numeri` prima di `/storico-ai/{id}`: il percorso fisso vince.
@router.get("/storico-ai/numeri", response_model=NumeriAI)
def numeri_ai(
    db: Annotated[Session, Depends(get_db, scope="function")],
    _: Annotated[Any, Depends(richiede_ruolo("operatore"))],
    response: Response,
    campagna_id: Annotated[int | None, Query()] = None,
    tipo: Annotated[str | None, Query()] = None,
    modello: Annotated[str | None, Query()] = None,
    versione_prompt: Annotated[str | None, Query()] = None,
    esito: Annotated[str | None, Query()] = None,
    dal: Annotated[date | None, Query()] = None,
    al: Annotated[date | None, Query()] = None,
) -> NumeriAI:
    response.headers["Cache-Control"] = "no-store"
    return service.numeri_ai(
        db,
        campagna_id=campagna_id,
        tipo=tipo,
        modello=modello,
        versione_prompt=versione_prompt,
        esito=esito,
        dal=dal,
        al=al,
    )


@router.get("/storico-ai/{id}", response_model=ChiamataAIDettaglio)
def chiamata_ai(
    id: int,
    db: Annotated[Session, Depends(get_db, scope="function")],
    _: Annotated[Any, Depends(richiede_ruolo("operatore"))],
    response: Response,
) -> ChiamataAIDettaglio:
    """Richiesta, risposta, errore e valutazioni; 404 se la chiamata non c'è."""
    response.headers["Cache-Control"] = "no-store"
    return service.chiamata_ai(db, id)
