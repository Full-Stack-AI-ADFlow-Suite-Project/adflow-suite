from fastapi import FastAPI

app = FastAPI(title="AdFlow Suite API")

@app.get("/api/health")
def health_check():
    return {"stato": "ok", "ambiente": "sviluppo"}
