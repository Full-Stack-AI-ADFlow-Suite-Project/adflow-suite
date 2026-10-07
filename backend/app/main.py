"""API: monta i router dei moduli sotto /api."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errori import ErroreDominio, NonAutenticato, NonPermesso
from app.core.eventi_sicurezza import CorrelazioneRichieste, registra, id_richiesta
from app.core.limite_login import TroppiTentativi, LimiteNonDisponibile
from app.moduli.accesso.router import router as accesso
from app.moduli.artigiani.router import router as artigiani
from app.moduli.campagne.router import router as campagne
from app.moduli.contenuti.router import router as contenuti
from app.moduli.notifiche.router import router as notifiche
from app.moduli.pubblicazione.router import router as pubblicazione
from app.moduli.revisione.router import router as revisione

app = FastAPI(title="AdFlow Suite")
app.add_middleware(CorrelazioneRichieste)

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
    evento = None
    if isinstance(errore, NonAutenticato):
        evento = (
            "auth_failure"
            if request.url.path == "/api/auth/login"
            else "invalid_session"
        )
    elif isinstance(errore, NonPermesso):
        evento = "role_denied"
    elif isinstance(errore, TroppiTentativi):
        evento = "login_rate_limited"
    elif isinstance(errore, LimiteNonDisponibile):
        evento = "login_limiter_unavailable"
    if evento:
        registra(evento, id_richiesta(request))
    headers = {"Cache-Control": "no-store"} if evento else {}
    if isinstance(errore, TroppiTentativi):
        headers["Retry-After"] = str(errore.riprova_dopo)
    return JSONResponse(
        status_code=errore.status_code,
        content={"detail": errore.messaggio},
        headers=headers,
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"stato": "ok"}
