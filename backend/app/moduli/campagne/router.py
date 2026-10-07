"""Endpoint del modulo campagne: chiamano service.py, senza logica di business."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errori import DatiNonValidi
from app.core.orologio import adesso
from app.moduli.accesso.service import richiede_ruolo, utente_corrente

from . import service
from .schemas import (
    CampagnaCrea,
    CampagnaDettaglio,
    CampagnaElencoItem,
    FotoDettaglio,
    GruppoDescrizioneAggiorna,
)

router = APIRouter(tags=["campagne"])


@router.post("/campagne", response_model=CampagnaDettaglio, status_code=201)
def crea_campagna(
    dati: CampagnaCrea,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> CampagnaDettaglio:
    """Crea una nuova campagna in bozza per l'artigiano autenticato (CA-09, CA-10, CA-11, CA-12, CA-46)."""
    campagna = service.crea_bozza(db, utente.id, dati, ora)
    return service.dettaglio_campagna(db, utente.id, utente.ruolo, campagna.id)


@router.get("/campagne", response_model=list[CampagnaElencoItem])
def elenca_campagne(
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(utente_corrente)],
    stato: Annotated[str | None, Query()] = None,
) -> list[CampagnaElencoItem]:
    """Elenca le campagne accessibili all'utente (l'artigiano vede solo le sue)."""
    campagne = service.elenca_campagne(db, utente.id, utente.ruolo, stato)
    return [CampagnaElencoItem.model_validate(c) for c in campagne]


@router.get("/campagne/{id}", response_model=CampagnaDettaglio)
def dettaglio_campagna(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(utente_corrente)],
) -> CampagnaDettaglio:
    """Restituisce il dettaglio della campagna (CA-04: 404 se l'artigiano accede a un'altra)."""
    return service.dettaglio_campagna(db, utente.id, utente.ruolo, id)


@router.post("/campagne/{id}/foto", response_model=FotoDettaglio, status_code=201)
def carica_foto(
    id: int,
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    gruppo_id: Annotated[UUID | None, Form()] = None,
) -> FotoDettaglio:
    """Carica una nuova foto nella campagna in bozza con streaming e limiti anti-DoS (CA-13, R-13)."""
    dimensione_max = 10 * 1024 * 1024
    letti = 0
    blocchi = []
    while True:
        chunk = file.file.read(64 * 1024)
        if not chunk:
            break
        letti += len(chunk)
        if letti > dimensione_max:
            raise DatiNonValidi(
                "La dimensione del file supera il limite massimo di 10 MB."
            )
        blocchi.append(chunk)

    contenuto = b"".join(blocchi)
    if not contenuto:
        raise DatiNonValidi("Il file caricato è vuoto.")

    foto = service.carica_foto(
        db=db,
        utente_id=utente.id,
        ruolo=utente.ruolo,
        campagna_id=id,
        contenuto=contenuto,
        gruppo_id=gruppo_id,
    )
    return FotoDettaglio.model_validate(foto)


@router.put("/campagne/{id}/gruppi/{gruppo_id}", status_code=200)
def aggiorna_descrizione_gruppo(
    id: int,
    gruppo_id: UUID,
    payload: GruppoDescrizioneAggiorna,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> dict[str, Any]:
    """Aggiorna la descrizione associata al gruppo di foto indicato."""
    service.aggiorna_descrizione_gruppo(
        db=db,
        utente_id=utente.id,
        ruolo=utente.ruolo,
        campagna_id=id,
        gruppo_id=gruppo_id,
        descrizione=payload.descrizione,
    )
    return {"ok": True, "descrizione": payload.descrizione}


@router.delete("/foto/{id}", status_code=204)
def elimina_foto(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> Response:
    """Elimina una singola foto dalla campagna in bozza."""
    service.elimina_foto(db=db, utente_id=utente.id, ruolo=utente.ruolo, foto_id=id)
    return Response(status_code=204)


@router.delete("/campagne/{id}/gruppi/{gruppo_id}", status_code=204)
def elimina_gruppo(
    id: int,
    gruppo_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> Response:
    """Elimina tutte le foto appartenenti a un gruppo della campagna in bozza."""
    service.elimina_gruppo(
        db=db,
        utente_id=utente.id,
        ruolo=utente.ruolo,
        campagna_id=id,
        gruppo_id=gruppo_id,
    )
    return Response(status_code=204)


@router.get("/foto/{id}/file")
def scarica_file_foto(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(utente_corrente)],
) -> Response:
    """Restituisce il file originale della foto dall'archivio con il proprio mime-type."""
    contenuto, mime = service.leggi_file_foto(
        db=db, utente_id=utente.id, ruolo=utente.ruolo, foto_id=id
    )
    return Response(content=contenuto, media_type=mime)
