"""Login e sessioni reali sulle API di revisione entrate in main (T1-42)."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.orologio import adesso
from app.main import app
from app.moduli.accesso import service
from app.moduli.accesso.models import Sessione
from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente
from tests.moduli.campagne.fabbrica import (
    campagna_con_piano_da_rivedere,
    campagna_in_revisione,
    foto,
)
from tests.moduli.contenuti.fabbrica import post_da_approvare


ORA = datetime(2030, 1, 3, 12, tzinfo=timezone.utc)


def _campagna(db, azione):
    record = (
        campagna_con_piano_da_rivedere(db)
        if azione == "prosegui"
        else campagna_in_revisione(db)
    )
    if azione == "prosegui":
        foto(db, campagna=record, analisi_ai={"idonea": True})
    post_da_approvare(db, campagna_id=record.id)
    return record


def _richiesta(client, record_id, azione):
    percorso = f"/api/campagne/{record_id}/{azione}"
    return client.get(percorso) if azione == "post" else client.post(percorso)


@pytest.mark.parametrize("azione", ["post", "approva", "prosegui"])
@pytest.mark.parametrize("ruolo", ["artigiano", "operatore", "admin"])
def test_ca03_ca61_revisione_con_login_reale(db, client, ruolo, azione):
    """Nessun override utente: admin/operatore passano, artigiano prende 403."""
    campagna = _campagna(db, azione)
    record = utente(db, ruolo)
    orologio = [ORA]
    app.dependency_overrides[adesso] = lambda: orologio[0]
    ingresso = client.post(
        "/api/auth/login",
        json={"email": record.email, "password": PASSWORD_DI_PROVA},
    )
    assert ingresso.status_code == 200
    token = client.cookies.get(service.COOKIE_SESSIONE)
    orologio[0] += timedelta(minutes=5)
    risposta = _richiesta(client, campagna.id, azione)
    assert risposta.status_code == (403 if ruolo == "artigiano" else 200)
    db.refresh(campagna)
    if ruolo == "artigiano":
        assert campagna.stato == (
            "piano_da_rivedere" if azione == "prosegui" else "in_revisione"
        )
        assert "set-cookie" not in risposta.headers
    else:
        assert "httponly" in risposta.headers["set-cookie"].lower()
        assert risposta.headers["cache-control"] == "no-store"
        assert client.cookies.get(service.COOKIE_SESSIONE) == token
        sessione = db.scalar(
            select(Sessione).where(Sessione.token_hash == service.hash_token(token))
        )
        assert sessione.scade_il == orologio[0] + timedelta(hours=12)
        if azione != "post":
            assert campagna.stato == (
                "attiva" if azione == "approva" else "in_generazione"
            )


@pytest.mark.parametrize("azione", ["post", "approva", "prosegui"])
def test_revisione_rifiuta_sessione_revocata(db, client, azione):
    campagna = _campagna(db, azione)
    record = utente(db, "operatore")
    app.dependency_overrides[adesso] = lambda: ORA
    assert (
        client.post(
            "/api/auth/login",
            json={"email": record.email, "password": PASSWORD_DI_PROVA},
        ).status_code
        == 200
    )
    token = client.cookies.get(service.COOKIE_SESSIONE)
    assert client.post("/api/auth/logout").status_code == 204
    # Un client che riutilizza il vecchio cookie non deve tornare autorizzato.
    client.cookies.set(service.COOKIE_SESSIONE, token)
    assert _richiesta(client, campagna.id, azione).status_code == 401


@pytest.mark.parametrize("azione", ["post", "approva", "prosegui"])
def test_ca62_revisione_rifiuta_sessione_scaduta(db, client, azione):
    campagna = _campagna(db, azione)
    record = utente(db, "operatore")
    orologio = [ORA]
    app.dependency_overrides[adesso] = lambda: orologio[0]
    assert (
        client.post(
            "/api/auth/login",
            json={"email": record.email, "password": PASSWORD_DI_PROVA},
        ).status_code
        == 200
    )
    orologio[0] += timedelta(hours=12)
    risposta = _richiesta(client, campagna.id, azione)
    assert risposta.status_code == 401
    assert "set-cookie" not in risposta.headers
