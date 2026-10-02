"""API: monta i router dei moduli sotto /api."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errori import ErroreDominio
from app.moduli.accesso.router import router as accesso
from app.moduli.artigiani.router import router as artigiani
from app.moduli.campagne.router import router as campagne
from app.moduli.contenuti.router import router as contenuti
from app.moduli.notifiche.router import router as notifiche
from app.moduli.pubblicazione.router import router as pubblicazione
from app.moduli.revisione.router import router as revisione

app = FastAPI(title="AdFlow Suite")

for _router in (
    accesso,
    notifiche,
    artigiani,
    campagne,
    contenuti,
    revisione,
    pubblicazione,
):
    app.include_router(_router, prefix="/api")


@app.exception_handler(ErroreDominio)
def errore_dominio(request: Request, errore: ErroreDominio) -> JSONResponse:
    return JSONResponse(
        status_code=errore.status_code, content={"detail": errore.messaggio}
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"stato": "ok"}
