"""Issue #40: le richieste oltre RICHIESTA_MAX_BYTE ricevono 413 prima dei router."""

from fastapi import FastAPI, Request, UploadFile
from starlette.testclient import TestClient

from app.core.config import leggi_impostazioni
from app.core.limite_richiesta import MESSAGGIO, LimiteRichiesta

LIMITE = 100


def _app_di_prova() -> FastAPI:
    prova = FastAPI()
    prova.add_middleware(LimiteRichiesta, massimo=LIMITE)

    @prova.post("/eco")
    async def eco(request: Request) -> dict[str, int]:
        return {"byte": len(await request.body())}

    @prova.post("/dati")
    def dati(dati: dict) -> dict:
        return dati

    @prova.post("/file")
    def file(file: UploadFile) -> dict[str, int]:
        return {"byte": len(file.file.read())}

    return prova


def _a_pezzi(totale: int, pezzo: int = 40):
    """Body senza Content-Length: il client lo manda a blocchi."""
    for inizio in range(0, totale, pezzo):
        yield b"x" * min(pezzo, totale - inizio)


def test_richiesta_entro_il_limite_passa():
    with TestClient(_app_di_prova()) as client:
        risposta = client.post("/eco", content=b"x" * LIMITE)
    assert risposta.status_code == 200
    assert risposta.json() == {"byte": LIMITE}


def test_content_length_oltre_il_limite_da_413_senza_leggere_il_body():
    with TestClient(_app_di_prova()) as client:
        risposta = client.post("/eco", content=b"x" * (LIMITE + 1))
    assert risposta.status_code == 413
    assert risposta.json() == {"detail": MESSAGGIO}


def test_body_a_blocchi_oltre_il_limite_da_413():
    with TestClient(_app_di_prova()) as client:
        entro = client.post("/eco", content=_a_pezzi(LIMITE))
        oltre = client.post("/eco", content=_a_pezzi(LIMITE + 1))
    assert entro.status_code == 200
    assert oltre.status_code == 413
    assert oltre.json() == {"detail": MESSAGGIO}


def test_json_a_blocchi_oltre_il_limite_da_413_e_non_400():
    corpo = b'{"chiave": "' + b"x" * (LIMITE * 2) + b'"}'

    def a_blocchi():
        for inizio in range(0, len(corpo), 40):
            yield corpo[inizio : inizio + 40]

    with TestClient(_app_di_prova()) as client:
        risposta = client.post(
            "/dati", content=a_blocchi(), headers={"content-type": "application/json"}
        )
    assert risposta.status_code == 413


def test_file_multipart_oltre_il_limite_da_413():
    with TestClient(_app_di_prova()) as client:
        risposta = client.post(
            "/file", files={"file": ("grande.bin", b"x" * (LIMITE * 3))}
        )
    assert risposta.status_code == 413


def test_api_vera_rifiuta_oltre_il_limite_configurato(client: TestClient):
    limite = leggi_impostazioni().richiesta_max_byte
    assert limite >= 10 * 1024 * 1024  # una foto da 10 MB deve poter passare (R-13)

    risposta = client.post("/api/auth/login", content=b"x" * (limite + 1))

    assert risposta.status_code == 413
    assert risposta.json() == {"detail": MESSAGGIO}
    assert risposta.headers.get("x-request-id")
