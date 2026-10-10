"""API: monta i router dei moduli sotto /api."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import leggi_impostazioni
from app.core.errori import (
    ErroreDominio,
    NonAutenticato,
    NonPermesso,
    frase_di_validazione,
)
from app.core.eventi_sicurezza import CorrelazioneRichieste, registra, id_richiesta
from app.core.limite_login import TroppiTentativi, LimiteNonDisponibile
from app.core.limite_richiesta import LimiteRichiesta
from app.moduli.accesso.router import router as accesso
from app.moduli.artigiani.router import router as artigiani
from app.moduli.campagne.router import router as campagne
from app.moduli.contenuti.router import router as contenuti
from app.moduli.notifiche.router import router as notifiche
from app.moduli.pubblicazione.router import router as pubblicazione
from app.moduli.revisione.router import router as revisione

app = FastAPI(title="AdFlow Suite")
# L'ultimo aggiunto è il più esterno: anche un 413 porta X-Request-ID
app.add_middleware(LimiteRichiesta, massimo=leggi_impostazioni().richiesta_max_byte)
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


@app.exception_handler(RequestValidationError)
def dati_non_validi(request: Request, errore: RequestValidationError) -> JSONResponse:
    """Il 422 dello schema: una frase in italiano, come ogni altro errore."""
    return JSONResponse(
        status_code=422,
        content={"detail": frase_di_validazione(errore.errors())},
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"stato": "ok"}


@app.get("/api/consorzio")
def consorzio() -> dict[str, str]:
    """Contatto pubblico dalla configurazione (R-29)."""
    impostazioni = leggi_impostazioni()
    return {
        "nome": impostazioni.consorzio_nome,
        "telefono": impostazioni.consorzio_telefono,
        "email": impostazioni.consorzio_email,
    }
