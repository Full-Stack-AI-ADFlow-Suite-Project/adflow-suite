"""La matrice dei permessi provata per davvero, cella per cella (T4-102).

Legge lo schema OpenAPI dell'app e prova ogni operazione × ruolo con la
sonda preparata per quel percorso: una riga senza matrice, o una cella che
risponde diversamente dall'atteso di `matrice.py`, fa fallire il test.
"""

from __future__ import annotations

import io
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.main import app
from app.moduli.accesso.service import utente_corrente
from app.moduli.campagne import service as service_campagne
from app.moduli.campagne.models import Foto, GruppoFoto
from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_revisione, gruppo_di_archivio
from tests.moduli.contenuti.fabbrica import chiamata_ai, post_da_approvare

from .matrice import AMMESSO, MATRICE, RUOLI

METODI = ("get", "post", "put", "patch", "delete")


def _operazioni_dello_schema() -> list[tuple[str, str]]:
    schema = app.openapi()
    return [
        (metodo, percorso)
        for percorso, metodi in sorted(schema["paths"].items())
        for metodo in METODI
        if metodo in metodi
    ]


@pytest.fixture
def mondo(db: Session, client: TestClient, tmp_path) -> dict:
    """Due botteghe, un operatore, un admin e le risorse di A (T4-102).

    A ha una campagna in revisione con un post, una foto con file vero su
    disco, un gruppo d'archivio con la sua foto e una chiamata AI nello
    storico: tutte le sonde con un id puntano a risorse di A.
    """
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        artigiano_a = utente(db, "artigiano")
        artigiano_b = utente(db, "artigiano")
        operatore = utente(db, "operatore")
        admin = utente(db, "admin")
        bottega_a = profilo(db, utente_id=artigiano_a.id)
        profilo(db, utente_id=artigiano_b.id)

        campagna = campagna_in_revisione(db, profilo_id=bottega_a.id)
        gruppo_campagna = db.scalar(
            select(GruppoFoto).where(GruppoFoto.campagna_id == campagna.id)
        )
        post = post_da_approvare(db, campagna_id=campagna.id)

        # una foto non usata dal post, con il file vero su disco
        buffer = io.BytesIO()
        Image.new("RGB", (1080, 1350), (90, 60, 30)).save(buffer, format="JPEG")
        nome_file = archivio.salva(buffer.getvalue(), "jpg")
        foto_a = db.scalars(
            select(Foto)
            .where(Foto.campagna_id == campagna.id, Foto.n_utilizzi == 0)
            .order_by(Foto.id)
        ).first()
        foto_a.file = nome_file
        # anche la foto del post ha un file vero: l'anteprima la rende (RT-08)
        for legame in post.versione_corrente.legami_foto:
            db.get(Foto, legame.foto_id).file = archivio.salva(buffer.getvalue(), "jpg")

        archivio_gruppo = gruppo_di_archivio(db, profilo_id=bottega_a.id)
        archivio_foto = db.scalars(
            select(Foto).where(Foto.gruppo_id == archivio_gruppo.id)
        ).first()
        chiamata = chiamata_ai(db, campagna)
        db.flush()

        sonda = io.BytesIO()
        Image.new("RGB", (24, 24), (10, 10, 10)).save(sonda, format="JPEG")

        yield {
            "utenti": {
                "artigiano_a": artigiano_a,
                "artigiano_b": artigiano_b,
                "operatore": operatore,
                "admin": admin,
            },
            "email_a": artigiano_a.email,
            "campagna_rev": campagna.id,
            "gruppo_campagna": gruppo_campagna.id,
            "foto_a": foto_a.id,
            "post": post.id,
            "archivio_gruppo": archivio_gruppo.id,
            "archivio_foto": archivio_foto.id,
            "chiamata": chiamata.id,
            "jpeg_piccolo": sonda.getvalue(),
            "url_pubblica": service_campagne.url_foto_pubblica(
                db, foto_a.id, canale="instagram"
            ),
        }


def _autentica(mondo: dict, ruolo: str) -> None:
    """Sceglie chi è l'utente della richiesta: nessuno, se anonimo."""
    if ruolo == "anonimo":
        app.dependency_overrides.pop(utente_corrente, None)
    else:
        record = mondo["utenti"][ruolo]
        app.dependency_overrides[utente_corrente] = lambda: record


def _url(mondo: dict, percorso: str) -> str:
    valori = {
        "campagna_id": mondo["campagna_rev"],
        "post_id": mondo["post"],
        "utente_id": mondo["utenti"]["artigiano_a"].id,
        "gruppo_id": mondo["gruppo_campagna"],
        "foto_id": mondo["foto_a"],
    }
    if "{id}" in percorso:
        if percorso.startswith("/api/foto/"):
            valori["id"] = mondo["foto_a"]
        elif percorso.startswith("/api/archivio/foto/"):
            valori["id"] = mondo["archivio_foto"]
        elif percorso.startswith("/api/archivio/gruppi/"):
            valori["id"] = mondo["archivio_gruppo"]
        elif percorso.startswith("/api/storico-ai/"):
            valori["id"] = mondo["chiamata"]
        else:
            valori["id"] = mondo["campagna_rev"]
    for nome, valore in valori.items():
        percorso = percorso.replace("{" + nome + "}", str(valore))
    return percorso


def _chiama(client: TestClient, metodo: str, url: str, mondo: dict, percorso: str):
    """La sonda dell'operazione: corpo minimo, valido dove serve."""
    if percorso == "/api/auth/login":
        return client.post(
            url, json={"email": mondo["email_a"], "password": PASSWORD_DI_PROVA}
        )
    if percorso == "/api/foto/{id}/pubblica":
        return client.get(mondo["url_pubblica"])  # firma valida
    if percorso in ("/api/campagne/{id}/foto", "/api/archivio/foto"):
        gruppo = (
            mondo["gruppo_campagna"]
            if "campagne" in percorso
            else mondo["archivio_gruppo"]
        )
        return client.post(
            url,
            files={"file": ("sonda.jpg", mondo["jpeg_piccolo"], "image/jpeg")},
            data={"gruppo_id": str(gruppo)},
        )
    if percorso == "/api/campagne/{id}/richiesta/foto":
        return client.post(
            url,
            files={"file": ("sonda.jpg", mondo["jpeg_piccolo"], "image/jpeg")},
            data={"foto_id": str(mondo["foto_a"]), "dichiarazione": "true"},
        )
    if metodo in ("post", "put", "patch"):
        return client.request(metodo, url, json={})
    return client.request(metodo, url)


def test_la_matrice_copre_esattamente_le_operazioni_dello_schema():
    """Un'operazione nuova nello schema senza riga nella matrice: qui si vede."""
    dello_schema = sorted(_operazioni_dello_schema())
    della_matrice = sorted(MATRICE)

    senza_riga = [op for op in dello_schema if op not in MATRICE]
    senza_operazione = [op for op in della_matrice if op not in dello_schema]
    assert not senza_riga, f"operazioni senza riga nella matrice: {senza_riga}"
    assert (
        not senza_operazione
    ), f"righe senza operazione nello schema: {senza_operazione}"
    assert (
        len(dello_schema) == 58
    ), f"attese 58 operazioni, ce ne sono {len(dello_schema)}"


@pytest.mark.parametrize("metodo,percorso", sorted(MATRICE))
def test_la_cella_della_matrice(mondo, client, metodo, percorso):
    """Ogni operazione × ruolo risponde come la matrice attende (T4-102)."""
    differenze = []
    url = _url(mondo, percorso)
    for ruolo in RUOLI:
        atteso = MATRICE[(metodo, percorso)][ruolo]
        _autentica(mondo, ruolo)
        risposta = _chiama(client, metodo, url, mondo, percorso)
        codice = risposta.status_code
        if atteso == AMMESSO:
            if codice in (401, 403, 404, 500):
                differenze.append(
                    f"{ruolo}: permesso atteso, risposta {codice} "
                    f"({risposta.json()['detail'] if codice != 500 else 'errore interno'})"
                )
        elif codice != int(atteso):
            differenze.append(
                f"{ruolo}: atteso {atteso}, risposta {codice} "
                f"({risposta.json().get('detail', '')})"
            )
    assert not differenze, (
        f"{metodo.upper()} {percorso} differisce dalla matrice attesa "
        f"(costituzione §3, spec):\n  " + "\n  ".join(differenze)
    )
