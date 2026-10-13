"""T3-11 MVP: CA-79, onboarding e password restituita una volta sola."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.core import limite_login
from app.core.config import leggi_impostazioni
from app.core.errori import StatoNonValido
from app.core.security import verifica_password
from app.main import app
from app.moduli.accesso import service as accesso
from app.moduli.accesso.models import Utente
from app.moduli.artigiani.models import AccountSocial, ProfiloBottega
from tests.moduli.artigiani.test_profilo import DATI


@pytest.fixture(autouse=True)
def credenziali_di_test(monkeypatch, motore_test):
    monkeypatch.setattr(leggi_impostazioni(), "email_test_environment", True)
    monkeypatch.setattr(leggi_impostazioni(), "login_limite_tentativi", 1000)
    monkeypatch.setattr(limite_login, "motore", lambda: motore_test)
    with motore_test.begin() as c:
        c.execute(text("DELETE FROM limite_login"))
    yield
    with motore_test.begin() as c:
        c.execute(text("DELETE FROM limite_login"))


def dati(**altri):
    return {
        "email": f"{uuid4().hex}@example.test",
        "nome": "Referente di prova",
        **altri,
    }


@pytest.mark.parametrize("ruolo", ["operatore", "admin"])
def test_ca79_crea_login_profilo_e_account_come_seed(
    db, client, utente_di_prova, ruolo, caplog
):
    utente_di_prova(ruolo)
    payload = dati(nome="  Referente  ")
    risposta = client.post("/api/artigiani", json=payload)
    assert risposta.status_code == 201
    risultato = risposta.json()
    assert set(risultato) == {"id", "email", "nome", "password_provvisoria"}
    assert risultato["nome"] == "Referente"
    assert risposta.headers["cache-control"] == "no-store"
    password = risultato["password_provvisoria"]
    record = accesso.utente(db, risultato["id"])
    assert record.ruolo == "artigiano" and record.attivo
    assert verifica_password(password, record.password_hash)
    assert password not in caplog.text
    assert (
        db.scalar(
            select(ProfiloBottega.id).where(ProfiloBottega.utente_id == record.id)
        )
        is None
    )
    assert client.post("/api/artigiani", json=payload).status_code == 409
    app.dependency_overrides.pop(accesso.utente_corrente, None)
    login = client.post(
        "/api/auth/login", json={"email": record.email, "password": password}
    )
    assert login.status_code == 200 and password not in login.text
    assert client.get("/api/auth/me").status_code == 200
    assert client.get("/api/profilo").status_code == 404
    assert client.put("/api/profilo", json=DATI).status_code == 200
    assert client.get("/api/canali").json() == [
        {"canale": "facebook", "collegato": True},
        {"canale": "instagram", "collegato": True},
    ]
    lettura = client.get("/api/profilo")
    assert password not in lettura.text
    assert (
        client.put(
            "/api/profilo", json=dict(DATI, nome="Bottega aggiornata")
        ).status_code
        == 200
    )
    bottega = db.scalar(
        select(ProfiloBottega).where(ProfiloBottega.utente_id == record.id)
    )
    accounts = list(
        db.scalars(select(AccountSocial).where(AccountSocial.profilo_id == bottega.id))
    )
    assert len(accounts) == 2
    assert {a.id_pagina for a in accounts} == {
        "facebook-pagina-seed-finta",
        "instagram-pagina-seed-finta",
    }
    assert all(a.permesso is None for a in accounts)


@pytest.mark.parametrize("campo", ["email", "nome"])
@pytest.mark.parametrize("valore", [None, "", " ", "a\x00b", "a\ud800b"])
def test_dati_non_validi_non_creano_utenti(db, client, utente_di_prova, campo, valore):
    import json

    utente_di_prova("operatore")
    numero = db.scalar(select(func.count()).select_from(Utente))
    risposta = client.post(
        "/api/artigiani",
        content=json.dumps(dati(**{campo: valore})),
        headers={"Content-Type": "application/json"},
    )
    assert risposta.status_code == 422
    assert db.scalar(select(func.count()).select_from(Utente)) == numero


@pytest.mark.parametrize("email", ["senza-chiocciola", "a@", "a b@example.test"])
def test_email_non_valida_422(client, utente_di_prova, email):
    utente_di_prova("operatore")
    assert client.post("/api/artigiani", json=dati(email=email)).status_code == 422


def test_ca79_email_duplicata_normalizzata_non_riespone_password(
    db, client, utente_di_prova, caplog
):
    utente_di_prova("operatore")
    payload = dati()
    prima = client.post("/api/artigiani", json=payload)
    seconda = client.post(
        "/api/artigiani",
        json={**payload, "email": " " + payload["email"].upper() + " "},
    )
    assert seconda.status_code == 409
    assert seconda.json() == {"detail": "Email già registrata."}
    assert prima.json()["password_provvisoria"] not in seconda.text + caplog.text


def test_ca79_artigiano_403_e_anonimo_401(client, utente_di_prova):
    assert client.post("/api/artigiani", json=dati()).status_code == 401
    utente_di_prova("artigiano")
    assert client.post("/api/artigiani", json=dati()).status_code == 403


def test_campi_privilegiati_non_accettati(client, utente_di_prova):
    utente_di_prova("operatore")
    assert (
        client.post(
            "/api/artigiani", json=dati(ruolo="admin", password="SceltaClient")
        ).status_code
        == 422
    )


def test_due_creazioni_concorrenti_stessa_email_una_sola_riesce(motore_test):
    email = f"{uuid4().hex}@example.test"
    barriera = Barrier(2)

    def crea():
        barriera.wait(timeout=15)
        try:
            with Session(motore_test) as db, db.begin():
                record, password = accesso.crea_artigiano(db, email, "Referente")
                return record.id
        except StatoNonValido:
            return None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futuri = [pool.submit(crea) for _ in range(2)]
            risultati = [f.result(timeout=25) for f in futuri]
        assert risultati.count(None) == 1
        with Session(motore_test) as db:
            assert (
                db.scalar(
                    select(func.count())
                    .select_from(Utente)
                    .where(Utente.email == email)
                )
                == 1
            )
    finally:
        with motore_test.begin() as c:
            c.execute(delete(Utente).where(Utente.email == email))
