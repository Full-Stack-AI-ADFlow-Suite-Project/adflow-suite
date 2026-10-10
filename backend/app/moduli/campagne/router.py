"""Endpoint del modulo campagne: chiamano service.py, senza logica di business."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.adapters.archivio import DIMENSIONE_MAX_BYTE
from app.core.db import get_db
from app.core.errori import DatiNonValidi
from app.core.orologio import adesso
from app.moduli.accesso.service import richiede_ruolo, utente_corrente

from . import bozza, service
from .schemas import (
    CampagnaCrea,
    CampagnaDettaglio,
    CampagnaElencoItem,
    CampagnaModifica,
    FotoDettaglio,
    FotoStellaModifica,
    GruppoAggiorna,
    GruppoCrea,
    GruppoDettaglio,
)

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


@router.patch("/campagne/{id}", response_model=CampagnaDettaglio)
def modifica_campagna(
    id: int,
    dati: CampagnaModifica,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> CampagnaDettaglio:
    """Modifica una campagna in bozza per l'artigiano proprietario (T2a-21, CA-08, CA-09, CA-10, CA-48)."""
    campagna = bozza.modifica_bozza(db, utente.id, id, dati, ora)
    return service.dettaglio_campagna(db, utente.id, utente.ruolo, campagna.id)


@router.get("/campagne", response_model=list[CampagnaElencoItem])
def elenca_campagne(
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(utente_corrente)],
    stato: Annotated[list[str] | None, Query()] = None,
) -> list[CampagnaElencoItem]:
    """Elenca le campagne accessibili all'utente (l'artigiano vede solo le sue, operatore/admin tutte con bottega e città)."""
    return service.elenca_campagne(db, utente.id, utente.ruolo, stato)


@router.get("/campagne/{id}", response_model=CampagnaDettaglio)
def dettaglio_campagna(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(utente_corrente)],
) -> CampagnaDettaglio:
    """Restituisce il dettaglio della campagna (CA-04: 404 se l'artigiano accede a un'altra)."""
    return service.dettaglio_campagna(db, utente.id, utente.ruolo, id)


@router.post("/campagne/{id}/gruppi", response_model=GruppoDettaglio, status_code=201)
def crea_gruppo(
    id: int,
    payload: GruppoCrea,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> GruppoDettaglio:
    """Crea un gruppo di foto (caricate o create_ai) per la campagna in bozza (CA-46, CA-47)."""
    gruppo = service.crea_gruppo(
        db=db,
        utente_id=utente.id,
        ruolo=utente.ruolo,
        campagna_id=id,
        dati=payload,
    )
    return GruppoDettaglio.model_validate(gruppo)


@router.put(
    "/campagne/{id}/gruppi/{gruppo_id}", response_model=GruppoDettaglio, status_code=200
)
def aggiorna_gruppo(
    id: int,
    gruppo_id: int,
    payload: GruppoAggiorna,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> GruppoDettaglio:
    """Aggiorna metadati e descrizione del gruppo della campagna in bozza."""
    gruppo = service.aggiorna_gruppo(
        db=db,
        utente_id=utente.id,
        ruolo=utente.ruolo,
        campagna_id=id,
        gruppo_id=gruppo_id,
        dati=payload,
    )
    return GruppoDettaglio.model_validate(gruppo)


@router.delete("/campagne/{id}/gruppi/{gruppo_id}", status_code=204)
def elimina_gruppo(
    id: int,
    gruppo_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> Response:
    """Elimina tutte le foto appartenenti a un gruppo e il gruppo stesso dalla campagna in bozza."""
    service.elimina_gruppo(
        db=db,
        utente_id=utente.id,
        ruolo=utente.ruolo,
        campagna_id=id,
        gruppo_id=gruppo_id,
    )
    return Response(status_code=204)


@router.post("/campagne/{id}/foto", response_model=FotoDettaglio, status_code=201)
def carica_foto(
    id: int,
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    gruppo_id: Annotated[str | None, Form()] = None,
) -> FotoDettaglio:
    """Carica una foto in un gruppo `caricate` della campagna in bozza (CA-13, R-13)."""
    if gruppo_id is None or not gruppo_id.strip():
        raise DatiNonValidi("Indica il gruppo in cui caricare la foto.")
    try:
        gruppo = int(gruppo_id)
    except ValueError:
        raise DatiNonValidi("ID gruppo non valido.")

    dimensione_max = DIMENSIONE_MAX_BYTE
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
        gruppo_id=gruppo,
    )
    return FotoDettaglio.model_validate(foto)


@router.put("/foto/{id}", response_model=FotoDettaglio, status_code=200)
def imposta_stella_foto(
    id: int,
    payload: FotoStellaModifica,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> FotoDettaglio:
    """Imposta o toglie la stella ('da_usare') su una foto della campagna in bozza."""
    foto = service.imposta_stella_foto(
        db=db,
        utente_id=utente.id,
        ruolo=utente.ruolo,
        foto_id=id,
        da_usare=payload.da_usare,
    )
    return FotoDettaglio.model_validate(foto)


@router.delete("/foto/{id}", status_code=204)
def elimina_foto(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> Response:
    """Elimina una singola foto dalla campagna in bozza."""
    service.elimina_foto(db=db, utente_id=utente.id, ruolo=utente.ruolo, foto_id=id)
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
    return Response(
        content=contenuto,
        media_type=mime,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.post("/campagne/{id}/invia", response_model=CampagnaDettaglio)
def invia_campagna(
    id: int,
    db: Annotated[Session, Depends(get_db, scope="function")],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> CampagnaDettaglio:
    service.invia_campagna(db, utente.id, id, ora)
    return service.dettaglio_campagna(db, utente.id, utente.ruolo, id)


@router.post("/campagne/{id}/riprova", response_model=CampagnaDettaglio)
def riprova_campagna(
    id: int,
    db: Annotated[Session, Depends(get_db, scope="function")],
    utente: Annotated[Any, Depends(richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> CampagnaDettaglio:
    service.riprova_campagna(db, id, ora)
    return service.dettaglio_campagna(db, utente.id, utente.ruolo, id)
