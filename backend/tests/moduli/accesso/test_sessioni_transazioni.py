"""HTTP e CLI con transazioni vere, sessioni DB distinte e commit osservabili."""


from concurrent.futures import ThreadPoolExecutor


from datetime import datetime, timezone


from types import SimpleNamespace


from typing import Annotated


from uuid import uuid4


import pytest


from fastapi import Depends, FastAPI


from fastapi.testclient import TestClient


from sqlalchemy import delete, select, text


from sqlalchemy.orm import Session


from app import cli


from app.core import db as modulo_db


from app.core.orologio import adesso


from app.main import app


from app.moduli.accesso import service


from app.moduli.accesso.models import Sessione, Utente


from app.moduli.accesso.router import router


from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente


@pytest.fixture
def reale(motore_test, monkeypatch):
    # Nessun override get_db: passiamo soltanto il motore di test al codice
    # comune, così le richieste usano le transazioni reali del progetto.
    with motore_test.connect() as connessione:
        assert connessione.scalar(text("select current_database()")) == "adflow_test"
    monkeypatch.setattr(modulo_db, "motore", lambda: motore_test)
    prova = FastAPI()
    prova.exception_handlers.update(app.exception_handlers)
    prova.include_router(router, prefix="/api")
    prova.dependency_overrides[adesso] = lambda: datetime(
        2026, 10, 7, tzinfo=timezone.utc
    )

    @prova.get("/solo-operatore")
    def solo_operatore(
        record: Annotated[Utente, Depends(service.richiede_ruolo("operatore"))]
    ):
        return {"id": record.id}

    prefisso = uuid4().hex
    contatore = 0

    def email_nuova():
        nonlocal contatore
        contatore += 1
        return f"{prefisso}-{contatore}@example.test"

    def nuovo(ruolo="artigiano"):
        email = email_nuova()
        with Session(motore_test) as db, db.begin():
            record = utente(db, ruolo, email=email)
            record_id = record.id
        return record_id, email

    with TestClient(
        prova, base_url="https://testserver", raise_server_exceptions=False
    ) as client:
        try:
            yield SimpleNamespace(
                app=prova,
                client=client,
                motore=motore_test,
                nuovo=nuovo,
                email=email_nuova,
            )
        finally:
            with motore_test.begin() as connessione:
                ids = select(Utente.id).where(Utente.email.like(f"{prefisso}-%"))
                connessione.execute(delete(Sessione).where(Sessione.utente_id.in_(ids)))
                connessione.execute(delete(Utente).where(Utente.id.in_(ids)))


def entra(client, email):
    risposta = client.post(
        "/api/auth/login", json={"email": email, "password": PASSWORD_DI_PROVA}
    )
    assert risposta.status_code == 200
    return client.cookies.get(service.COOKIE_SESSIONE)


def test_login_commit_e_logout_visibili_da_altra_connessione(reale):
    record_id, email = reale.nuovo()
    token = entra(reale.client, email)
    with Session(reale.motore) as db:
        sessione = db.scalar(select(Sessione).where(Sessione.utente_id == record_id))
        assert sessione is not None
        assert sessione.token_hash == service.hash_token(token)
    assert reale.client.get("/api/auth/me").json()["id"] == record_id
    assert reale.client.post("/api/auth/logout").status_code == 204
    with Session(reale.motore) as db:
        assert (
            db.scalar(select(Sessione.id).where(Sessione.utente_id == record_id))
            is None
        )


def test_errore_db_durante_rotazione_fa_rollback(reale, monkeypatch):
    record_id, email = reale.nuovo()
    _, altra_email = reale.nuovo()
    vecchio_token = entra(reale.client, email)
    with TestClient(reale.app, base_url="https://testserver") as altro:
        token_occupato = entra(altro, altra_email)
    # Forziamo il vincolo unico dopo la cancellazione del token precedente.
    monkeypatch.setattr(service, "genera_token", lambda: token_occupato)
    risposta = reale.client.post(
        "/api/auth/login", json={"email": email, "password": PASSWORD_DI_PROVA}
    )
    assert risposta.status_code == 500
    assert "set-cookie" not in risposta.headers
    assert reale.client.cookies.get(service.COOKIE_SESSIONE) == vecchio_token
    with Session(reale.motore) as db:
        sessione = db.scalar(select(Sessione).where(Sessione.utente_id == record_id))
        assert sessione.token_hash == service.hash_token(vecchio_token)
    assert reale.client.get("/api/auth/me").status_code == 200


def test_modifica_ruolo_riletta_alla_richiesta_successiva(reale):
    record_id, email = reale.nuovo("operatore")
    entra(reale.client, email)
    assert reale.client.get("/solo-operatore").status_code == 200
    with Session(reale.motore) as db, db.begin():
        db.get(Utente, record_id).ruolo = "artigiano"
    assert reale.client.get("/solo-operatore").status_code == 403
    assert reale.client.get("/api/auth/me").json()["ruolo"] == "artigiano"


def test_disattivazione_riletta_da_connessione_distinta(reale):
    record_id, email = reale.nuovo("operatore")
    entra(reale.client, email)
    with Session(reale.motore) as db, db.begin():
        db.get(Utente, record_id).attivo = False
    assert reale.client.get("/solo-operatore").status_code == 401
    assert reale.client.get("/api/auth/me").status_code == 401


def test_token_revocato_da_altro_client_non_riutilizzabile(reale):
    _, email = reale.nuovo()
    token = entra(reale.client, email)
    with TestClient(reale.app, base_url="https://testserver") as altro:
        altro.cookies.set(service.COOKIE_SESSIONE, token)
        assert altro.post("/api/auth/logout").status_code == 204
    assert reale.client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize("concorrenti", [2, 4, 8])
def test_login_paralleli_dispositivi_distinti_token_unici(reale, concorrenti):
    record_id, email = reale.nuovo()

    def dispositivo(_):
        with TestClient(reale.app, base_url="https://testserver") as client:
            token = entra(client, email)
            assert client.get("/api/auth/me").json()["id"] == record_id
            return token

    with ThreadPoolExecutor(max_workers=concorrenti) as pool:
        tokens = list(pool.map(dispositivo, range(8)))
    assert len(set(tokens)) == 8
    with Session(reale.motore) as db:
        assert (
            len(
                list(
                    db.scalars(select(Sessione).where(Sessione.utente_id == record_id))
                )
            )
            == 8
        )
    # Revoca uno solo dei dispositivi: gli altri devono restare autenticati.
    reale.client.cookies.set(service.COOKIE_SESSIONE, tokens[0])
    assert reale.client.post("/api/auth/logout").status_code == 204
    reale.client.cookies.set(service.COOKIE_SESSIONE, tokens[1])
    assert reale.client.get("/api/auth/me").status_code == 200


def test_rinnovo_commit_visibile_da_altra_connessione(reale):
    from datetime import timedelta

    record_id, email = reale.nuovo("operatore")
    entra(reale.client, email)
    dopo = datetime(2026, 10, 7, 5, tzinfo=timezone.utc)
    reale.app.dependency_overrides[adesso] = lambda: dopo
    risposta = reale.client.get("/api/auth/me")
    assert risposta.status_code == 200
    with Session(reale.motore) as db:
        assert db.scalar(
            select(Sessione.scade_il).where(Sessione.utente_id == record_id)
        ) == dopo + timedelta(hours=12)


@pytest.mark.parametrize("evento", ["revoca", "scadenza", "disattivazione", "ruolo"])
def test_rinnovo_condizionale_non_ripristina_sessione_invalida(
    reale, monkeypatch, evento
):
    from datetime import timedelta
    from app.core.errori import NonAutenticato

    record_id, email = reale.nuovo("operatore")
    token = entra(reale.client, email)
    ora = datetime(2026, 10, 7, 1, tzinfo=timezone.utc)
    durata_reale = service.durata_sessione

    def modifica_dopo_lettura(ruolo):
        with Session(reale.motore) as altro, altro.begin():
            if evento == "revoca":
                service.logout(altro, token)
            elif evento == "scadenza":
                altro.scalar(
                    select(Sessione).where(Sessione.utente_id == record_id)
                ).scade_il = ora - timedelta(seconds=1)
            elif evento == "disattivazione":
                altro.get(Utente, record_id).attivo = False
            else:
                altro.get(Utente, record_id).ruolo = "artigiano"
        return durata_reale(ruolo)

    monkeypatch.setattr(service, "durata_sessione", modifica_dopo_lettura)
    with Session(reale.motore) as db, db.begin():
        with pytest.raises(NonAutenticato):
            service.utente_della_sessione(db, token, ora)
    with Session(reale.motore) as db:
        sessione = db.scalar(select(Sessione).where(Sessione.utente_id == record_id))
        if evento == "revoca":
            assert sessione is None
        elif evento == "scadenza":
            assert sessione.scade_il < ora
