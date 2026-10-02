from fastapi import FastAPI

app = FastAPI(title="AdFlow Suite API")

# Router dei moduli (vuoti per ora, verranno implementati nei task delle corsie)
# from app.moduli.accesso.router import router as accesso_router
# from app.moduli.artigiani.router import router as artigiani_router
# from app.moduli.campagne.router import router as campagne_router
# from app.moduli.contenuti.router import router as contenuti_router
# from app.moduli.revisione.router import router as revisione_router
# from app.moduli.pubblicazione.router import router as pubblicazione_router
# from app.moduli.notifiche.router import router as notifiche_router

# app.include_router(accesso_router, prefix="/auth", tags=["auth"])
# app.include_router(artigiani_router, prefix="/artigiani", tags=["artigiani"])
# app.include_router(campagne_router, prefix="/campagne", tags=["campagne"])
# app.include_router(contenuti_router, prefix="/contenuti", tags=["contenuti"])
# app.include_router(revisione_router, prefix="/revisione", tags=["revisione"])
# app.include_router(pubblicazione_router, prefix="/pubblicazione", tags=["pubblicazione"])
# app.include_router(notifiche_router, prefix="/notifiche", tags=["notifiche"])

@app.get("/api/health")
def health_check():
    return {"stato": "ok", "ambiente": "sviluppo"}
