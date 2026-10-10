"""CA-78 e conservazione del logo degli snapshot (parte profilo di CA-77)."""
from datetime import datetime, timezone
from io import BytesIO

from PIL import Image
import pytest

from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.orologio import adesso
from app.main import app
from app.moduli.artigiani import logo
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_inviata

ORA = datetime(2030, 1, 1, tzinfo=timezone.utc)


def immagine(formato="PNG", size=(300, 300), colore="red"):
    out = BytesIO()
    Image.new("RGB", size, colore).save(out, format=formato)
    return out.getvalue()


@pytest.fixture
def archivio():
    with usa_archivio(ArchivioFinto()) as adattatore:
        yield adattatore


@pytest.fixture
def bottega(db, client, utente_di_prova):
    u = utente_di_prova("artigiano")
    app.dependency_overrides[adesso] = lambda: ORA
    return u, profilo(db, utente_id=u.id)


def carica(client, dati=None, filename="../../nome.exe", mime="application/pdf"):
    return client.put(
        "/api/profilo/logo",
        files={"file": (filename, immagine() if dati is None else dati, mime)},
    )


@pytest.mark.parametrize(
    "formato,mime,ext",
    [
        ("PNG", "image/png", ".png"),
        ("JPEG", "image/jpeg", ".jpg"),
        ("WEBP", "image/webp", ".webp"),
    ],
)
def test_ca78_formati_reali_nome_server_e_lettura(
    db, client, bottega, archivio, formato, mime, ext
):
    _, p = bottega
    dati = immagine(formato)
    risposta = carica(client, dati)
    assert risposta.status_code == 200
    nome = risposta.json()["logo"]
    assert nome.endswith(ext) and "/" not in nome and ".." not in nome
    assert archivio.leggi(nome) == dati
    db.refresh(p)
    assert p.logo == nome and p.aggiornato_il == ORA
    lettura = client.get("/api/profilo/logo")
    assert lettura.status_code == 200 and lettura.content == dati
    assert lettura.headers["content-type"] == mime
    assert lettura.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "dati",
    [
        b"",
        b"%PDF-1.7",
        b"<svg></svg>",
        immagine("GIF"),
        immagine()[:30],
        immagine("JPEG")[:50],
    ],
)
def test_ca78_file_non_valido_422(client, bottega, archivio, dati):
    risposta = carica(client, dati, "logo.png", "image/png")
    assert risposta.status_code == 422
    assert isinstance(risposta.json()["detail"], str)
    assert not archivio.file_salvati


@pytest.mark.parametrize(
    "size,esito",
    [((299, 800), 422), ((800, 299), 422), ((300, 300), 200), ((300, 800), 200)],
)
def test_ca78_lato_corto(client, bottega, archivio, size, esito):
    assert carica(client, immagine(size=size)).status_code == esito


@pytest.mark.parametrize(
    "dimensione,esito", [(logo.MAX_BYTE, 200), (logo.MAX_BYTE + 1, 422)]
)
def test_ca78_limite_peso_inclusivo(client, bottega, archivio, dimensione, esito):
    dati = immagine()
    dati += b"\x00" * (dimensione - len(dati))
    assert carica(client, dati).status_code == esito
    assert len(archivio.file_salvati) == (1 if esito == 200 else 0)


def test_ca77_sostituzione_e_rimozione_conservano_file_snapshot(
    db, client, bottega, archivio
):
    _, p = bottega
    prima = immagine(colore="red")
    vecchio = carica(client, prima).json()["logo"]
    c = campagna_inviata(db, profilo_id=p.id)
    nuovo = carica(client, immagine(colore="blue")).json()["logo"]
    assert nuovo != vecchio
    assert c.profilo_snapshot["logo"] == vecchio
    assert archivio.leggi(vecchio) == prima
    assert client.delete("/api/profilo/logo").status_code == 204
    assert client.get("/api/profilo").json()["logo"] is None
    assert archivio.esiste(vecchio) and archivio.esiste(nuovo)
    assert c.profilo_snapshot["logo"] == vecchio
    assert client.get("/api/profilo/logo").status_code == 404
    assert client.delete("/api/profilo/logo").status_code == 404


@pytest.mark.parametrize("azione", ["get", "put", "delete"])
def test_profilo_assente_404(client, utente_di_prova, archivio, azione):
    utente_di_prova("artigiano")
    risposta = (
        carica(client)
        if azione == "put"
        else getattr(client, azione)("/api/profilo/logo")
    )
    assert risposta.status_code == 404
    assert not archivio.file_salvati


@pytest.mark.parametrize("azione", ["get", "delete"])
def test_logo_assente_404(client, bottega, archivio, azione):
    assert getattr(client, azione)("/api/profilo/logo").status_code == 404


def test_file_mancante_archivio_404(db, client, bottega, archivio):
    nome = carica(client).json()["logo"]
    archivio.elimina(nome)
    assert client.get("/api/profilo/logo").status_code == 404


@pytest.mark.parametrize("ruolo", ["operatore", "admin"])
@pytest.mark.parametrize("azione", ["get", "put", "delete"])
def test_ruoli_non_ammessi(client, utente_di_prova, archivio, ruolo, azione):
    utente_di_prova(ruolo)
    risposta = (
        carica(client)
        if azione == "put"
        else getattr(client, azione)("/api/profilo/logo")
    )
    assert risposta.status_code == 403
    assert not archivio.file_salvati


@pytest.mark.parametrize("azione", ["get", "put", "delete"])
def test_senza_sessione_401(client, archivio, azione):
    risposta = (
        carica(client)
        if azione == "put"
        else getattr(client, azione)("/api/profilo/logo")
    )
    assert risposta.status_code == 401


def test_isolamento_botteghe(db, client, bottega, archivio, utente_di_prova):
    _, primo = bottega
    nome = carica(client).json()["logo"]
    altro = utente_di_prova("artigiano")
    secondo = profilo(db, utente_id=altro.id)
    assert client.get("/api/profilo/logo").status_code == 404
    assert client.delete("/api/profilo/logo").status_code == 404
    assert carica(client).status_code == 200
    db.refresh(primo)
    db.refresh(secondo)
    assert primo.logo == nome and secondo.logo != nome
    assert archivio.esiste(nome)


def test_upload_errato_preserva_logo(db, client, bottega, archivio):
    _, p = bottega
    nome = carica(client).json()["logo"]
    assert carica(client, b"non immagine").status_code == 422
    db.refresh(p)
    assert p.logo == nome and archivio.file_salvati == [nome]


def test_rollback_transazione_toglie_solo_file_nuovo(db, client, bottega, archivio):
    u, p = bottega
    precedente = carica(client).json()["logo"]
    db.commit()  # Il logo precedente proviene da una richiesta già riuscita.
    nuovo = None
    with pytest.raises(RuntimeError), db.begin_nested():
        nuovo = logo.salva(db, u.id, immagine(colore="blue"), ORA).logo
        raise RuntimeError("Annulla richiesta")
    db.refresh(p)
    assert p.logo == precedente
    assert archivio.esiste(precedente) and not archivio.esiste(nuovo)


def test_errore_flush_toglie_file_nuovo(db, client, bottega, archivio, monkeypatch):
    u, p = bottega
    precedente = carica(client).json()["logo"]

    flush_originale = db.flush

    def fallisce(*args, **kwargs):
        if p.logo != precedente:
            assert archivio.esiste(p.logo)
            raise RuntimeError("Salvataggio fallito")
        return flush_originale(*args, **kwargs)

    monkeypatch.setattr(db, "flush", fallisce)
    with pytest.raises(RuntimeError):
        logo.salva(db, u.id, immagine(colore="blue"), ORA)
    assert archivio.file_salvati == [precedente]


def test_commit_reale_conserva_file(db, client, bottega, archivio):
    u, _ = bottega
    nome = logo.salva(db, u.id, immagine(), ORA).logo
    db.commit()
    db.rollback()
    assert archivio.esiste(nome)


def test_ca78_file_obbligatorio_errore_italiano(client, bottega, archivio):
    risposta = client.put("/api/profilo/logo")
    assert risposta.status_code == 422
    assert risposta.json() == {"detail": "Dati del profilo non validi."}
    assert not archivio.file_salvati


def test_rollback_richiesta_api_conserva_precedente(db, client, bottega, archivio):
    from app.core.db import get_db

    _, p = bottega
    precedente = carica(client).json()["logo"]
    db.commit()

    def richiesta_fallita():
        with db.begin_nested():
            yield db
            raise RuntimeError("Transazione non confermata")

    app.dependency_overrides[get_db] = richiesta_fallita
    with pytest.raises(RuntimeError):
        carica(client, immagine(colore="blue"))
    db.refresh(p)
    assert p.logo == precedente
    assert archivio.file_salvati == [precedente]


def test_contratto_openapi_logo_file_obbligatorio(client):
    import warnings

    app.openapi_schema = None
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        risposta = client.get("/openapi.json")
    assert risposta.status_code == 200
    schema = risposta.json()
    operazioni = schema["paths"]["/api/profilo/logo"]
    assert {"get", "put", "delete"} <= set(operazioni)
    riferimento = operazioni["put"]["requestBody"]["content"]["multipart/form-data"][
        "schema"
    ]["$ref"]
    corpo = schema["components"]["schemas"][riferimento.rsplit("/", 1)[-1]]
    assert "file" in corpo["required"]
    assert corpo["properties"]["file"]["type"] == "string"
