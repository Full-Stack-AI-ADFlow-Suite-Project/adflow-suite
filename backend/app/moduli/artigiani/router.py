"""Endpoint del modulo artigiani: chiamano service.py, senza logica di business."""

from datetime import datetime
from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.orologio import adesso
from app.moduli.accesso.service import richiede_ruolo

from . import logo, service
from .schemas import CanaleCollegato
from .profilo_schemas import ProfiloScrittura, ProfiloPubblico

router = APIRouter(tags=["artigiani"])


@router.get("/canali", response_model=list[CanaleCollegato])
def canali(
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> list[CanaleCollegato]:
    return service.stato_canali(db, utente.id)


class RottaProfilo(APIRoute):
    """Errori italiani: indica i campi, senza riflettere dati personali."""

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        originale = super().get_route_handler()

        async def valida(request: Request) -> Response:
            try:
                return await originale(request)
            except RequestValidationError as errore:
                campi = sorted(
                    {
                        str(e["loc"][1])
                        for e in errore.errors()
                        if len(e["loc"]) > 1
                        and e["loc"][1] in ProfiloScrittura.model_fields
                    }
                )
                dettaglio = "Dati del profilo non validi."
                if campi:
                    dettaglio += " Controllare: " + ", ".join(campi) + "."
                return JSONResponse(status_code=422, content={"detail": dettaglio})

        return valida


profili = APIRouter(route_class=RottaProfilo)


@profili.get("/profilo", response_model=ProfiloPubblico)
def leggi_profilo(
    db: Annotated[Session, Depends(get_db, scope="function")],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    response: Response,
) -> Any:
    response.headers["Cache-Control"] = "no-store"
    return service.leggi_profilo_personale(db, utente.id)


@profili.put("/profilo", response_model=ProfiloPubblico)
def salva_profilo(
    dati: ProfiloScrittura,
    db: Annotated[Session, Depends(get_db, scope="function")],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    ora: Annotated[datetime, Depends(adesso)],
    response: Response,
) -> Any:
    response.headers["Cache-Control"] = "no-store"
    return service.salva_profilo_personale(db, utente.id, dati, ora)


@profili.put("/profilo/logo", response_model=ProfiloPubblico)
async def salva_logo(
    db: Annotated[Session, Depends(get_db, scope="function")],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    ora: Annotated[datetime, Depends(adesso)],
    file: Annotated[UploadFile, File()],
    response: Response,
) -> Any:
    dati = await file.read(logo.MAX_BYTE + 1)
    response.headers["Cache-Control"] = "no-store"
    return logo.salva(db, utente.id, dati, ora)


@profili.get("/profilo/logo")
def leggi_logo(
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
) -> Response:
    dati, mime = logo.leggi(db, utente.id)
    return Response(dati, media_type=mime, headers={"Cache-Control": "no-store"})


@profili.delete("/profilo/logo", status_code=204)
def elimina_logo(
    db: Annotated[Session, Depends(get_db, scope="function")],
    utente: Annotated[Any, Depends(richiede_ruolo("artigiano"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> Response:
    logo.elimina(db, utente.id, ora)
    return Response(status_code=204)


router.include_router(profili)
