from fastapi import FastAPI

app = FastAPI(title="AdFlow API")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AdFlow API is running"}
