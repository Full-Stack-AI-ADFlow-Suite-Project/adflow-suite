"""Endpoint del modulo campagne: chiamano service.py, senza logica di business."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.adapters.archivio import DIMENSIONE_MAX_BYTE
from app.core.db import get_db
from app.core.errori import DatiNonValidi, NonTrovato
from app.core.orologio import adesso
from app.moduli.accesso.service import richiede_ruolo, utente_corrente

from . import archivio, bozza, service, viste
from .schemas import (
    CampagnaCrea,
    CampagnaDettaglio,
    CampagnaElencoItem,
    CampagnaInvia,
    CampagnaModifica,
    FotoDettaglio,
    GruppoAggiorna,
    GruppoArchivioCrea,
    GruppoCrea,
    GruppoDettaglio,
    GruppoSintetico,
    RichiestaArtigiano,
    RichiestaCrea,
    RichiestaInvia,
)

router = APIRouter(tags=["campagne"])


def _leggi_file(file: UploadFile) -> bytes:
    """Legge il file caricato a blocchi, con il limite di 10 MB (R-13)."""
    letti = 0
    blocchi = []
    while True:
        chunk = file.file.read(64 * 1024)
        if not chunk:
            break
        letti += len(chunk)
        if letti > DIMENSIONE_MAX_BYTE:
            raise DatiNonValidi(
                "La dimensione del file supera il limite massimo di 10 MB."
            )
        blocchi.append(chunk)

    contenuto = b"".join(blocchi)
    if not contenuto:
        raise DatiNonValidi("Il file caricato è vuoto.")
    return contenuto


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
    if utente.ruolo == "artigiano":
        return viste.campagne_artigiano(db, utente.id, stato)
    return service.elenca_campagne(db, utente.id, utente.ruolo, stato)


@router.get("/campagne/{id}", response_model=CampagnaDettaglio)
def dettaglio_campagna(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(utente_corrente)],
) -> CampagnaDettaglio:
    """Restituisce il dettaglio della campagna (CA-04: 404 se l'artigiano accede a un'altra)."""
    if utente.ruolo == "artigiano":
        return viste.dettaglio_artigiano(db, utente.id, id)
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

    contenuto = _leggi_file(file)

    foto = service.carica_foto(
        db=db,
        utente_id=utente.id,
        ruolo=utente.ruolo,
        campagna_id=id,
        contenuto=contenuto,
        gruppo_id=gruppo,
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


@router.get("/foto/{id}/pubblica")
def scarica_foto_pubblica(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    ora: Annotated[datetime, Depends(adesso)],
    canale: Annotated[str | None, Query()] = None,
    firma: Annotated[str | None, Query()] = None,
    scadenza: Annotated[str | None, Query()] = None,
) -> Response:
    """Restituisce la foto sistemata per il canale con firma a tempo (spec R-42, CA-81).

    Accessibile senza autenticazione o sessione (utilizzato da Meta/Instagram per scaricare la foto).
    Se la firma è alterata, scaduta, mancante o la foto non esiste, risponde con 404
    senza esporre alcun dato interno (constitution §3).
    """
    if id <= 0 or not canale or not firma:
        raise NonTrovato("Foto non trovata.")

    scadenza_ts: int | None = None
    if scadenza is not None:
        try:
            scadenza_ts = int(scadenza.strip())
        except (ValueError, TypeError):
            raise NonTrovato("Foto non trovata.")

    if not service.verifica_firma_foto(
        foto_id=id,
        canale=canale,
        firma=firma,
        scadenza_ts=scadenza_ts,
        ora=ora,
    ):
        raise NonTrovato("Foto non trovata.")

    try:
        dati_jpeg, mime = service.foto_sistemata(db, foto_id=id, canale=canale)
    except (DatiNonValidi, NonTrovato, ValueError):
        raise NonTrovato("Foto non trovata.")

    return Response(
        content=dati_jpeg,
        media_type=mime,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "public, max-age=3600",
        },
    )


@router.post("/campagne/{id}/invia", response_model=CampagnaDettaglio)
def invia_campagna(
    id: int,
    db: Annotated[Session, Depends(get_db, scope="function")],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    ora: Annotated[datetime, Depends(adesso)],
    dati: CampagnaInvia | None = None,
) -> CampagnaDettaglio:
    service.invia_campagna(
        db, utente.id, id, ora, dichiarazione=dati.dichiarazione if dati else False
    )
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


# Congelato per l'MVP, ADR-114: non estendere. Vale per tutti gli endpoint
# `/archivio` qui sotto.
@router.get("/archivio", response_model=list[GruppoSintetico])
def elenca_archivio(
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> list[GruppoSintetico]:
    """Elenca i gruppi e le foto senza campagna dell'archivio della bottega (T2a-22, R-27, plan §3)."""
    return archivio.elenca_archivio(db, utente.id)


@router.post("/archivio/gruppi", response_model=GruppoSintetico, status_code=201)
def crea_gruppo_archivio(
    dati: GruppoArchivioCrea,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> GruppoSintetico:
    """Crea un gruppo di foto senza campagna nell'archivio della bottega (T2a-22, plan §3)."""
    return archivio.crea_gruppo_archivio(db, utente.id, dati)


@router.post("/archivio/foto", response_model=FotoDettaglio, status_code=201)
def carica_foto_archivio(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    gruppo_id: Annotated[str | None, Form()] = None,
) -> FotoDettaglio:
    """Carica una foto nell'archivio della bottega associandola a un gruppo (T2a-22, R-13, CA-13)."""
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

    return archivio.carica_foto_archivio(
        db=db, utente_id=utente.id, gruppo_id=gruppo, contenuto=contenuto
    )


@router.delete("/archivio/foto/{id}", status_code=204)
def elimina_foto_archivio(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> Response:
    """Elimina una foto dall'archivio della bottega (T2a-22, plan §3)."""
    archivio.elimina_foto_archivio(db=db, utente_id=utente.id, foto_id=id)
    return Response(status_code=204)


@router.delete("/archivio/gruppi/{id}", status_code=204)
def elimina_gruppo_archivio(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> Response:
    """Elimina un gruppo dell'archivio con le sue foto (T2a-22, plan §3)."""
    archivio.elimina_gruppo_archivio(db=db, utente_id=utente.id, gruppo_id=id)
    return Response(status_code=204)


# Corsia 6 (ADR-116): richiesta all'artigiano (spec R-46).
@router.post(
    "/campagne/{id}/richiesta", response_model=RichiestaArtigiano, status_code=201
)
def chiedi_all_artigiano(
    id: int,
    dati: RichiestaCrea,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("operatore"))],
) -> RichiestaArtigiano:
    """L'operatore chiede una risposta e fino a 3 foto da sostituire (R-46, CA-86)."""
    return service.apri_richiesta(db, id, utente.id, dati.domanda, dati.foto)


@router.post(
    "/campagne/{id}/richiesta/foto", response_model=FotoDettaglio, status_code=201
)
def carica_foto_richiesta(
    id: int,
    file: Annotated[UploadFile, File(...)],
    foto_id: Annotated[int, Form()],
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    dichiarazione: Annotated[bool, Form()] = False,
) -> FotoDettaglio:
    """L'artigiano carica la foto nuova al posto di una segnata (R-46, R-41, CA-87)."""
    contenuto = _leggi_file(file)
    nuova = service.carica_foto_richiesta(
        db, utente.id, id, foto_id, contenuto, dichiarazione
    )
    return FotoDettaglio.model_validate(nuova)


@router.post("/campagne/{id}/richiesta/invia", response_model=RichiestaArtigiano)
def invia_risposta(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    dati: RichiestaInvia | None = None,
) -> RichiestaArtigiano:
    """L'artigiano invia la risposta alla richiesta del consorzio (R-46, CA-88)."""
    return service.invia_risposta(db, utente.id, id, dati.risposta if dati else None)
