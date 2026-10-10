"""Profilo 2a: isolamento, validazione, aggiornamento e snapshot immutati."""
from copy import deepcopy
import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.orologio import adesso
from app.main import app
from app.moduli.accesso import service as accesso
from app.moduli.artigiani import service
from app.moduli.artigiani.models import AccountSocial, ProfiloBottega
from app.moduli.artigiani.profilo_schemas import ProfiloScrittura
from tests.moduli.accesso.fabbrica import utente, PASSWORD_DI_PROVA
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_inviata

ORA = datetime(2030, 1, 1, tzinfo=timezone.utc)
DATI = {
    "nome": "Bottega nuova",
    "referente": "Referente",
    "citta": "Roma",
    "tipo_prodotto": "ceramica_vetro",
    "clienti_ideali": "Clienti locali",
    "obiettivo": "notorieta",
    "canali": ["facebook", "instagram"],
    "frequenza": "f3_4",
}


def test_ca05_profilo_assente_restituisce_404(client, utente_di_prova):
    utente_di_prova()
    assert client.get("/api/profilo").status_code == 404


def test_ca06_crea_legge_e_modifica_senza_duplicare(db, client, utente_di_prova):
    persona = utente_di_prova()
    app.dependency_overrides[adesso] = lambda: ORA
    risposta = client.put("/api/profilo", json=DATI)
    assert risposta.status_code == 200
    record = risposta.json()
    assert record["nome"] == DATI["nome"]
    assert datetime.fromisoformat(record["aggiornato_il"].replace("Z", "+00:00")) == ORA
    assert "utente_id" not in record
    assert risposta.headers["cache-control"] == "no-store"
    assert client.get("/api/profilo").json() == record
    nuovo = dict(DATI, nome="Bottega modificata")
    risposta = client.put("/api/profilo", json=nuovo)
    assert risposta.status_code == 200
    assert risposta.json()["id"] == record["id"]
    assert risposta.json()["nome"] == nuovo["nome"]
    assert (
        db.scalar(
            select(func.count())
            .select_from(ProfiloBottega)
            .where(ProfiloBottega.utente_id == persona.id)
        )
        == 1
    )
    assert client.get("/api/canali").json() == [
        {"canale": "facebook", "collegato": False},
        {"canale": "instagram", "collegato": False},
    ]


@pytest.mark.parametrize(
    "campo",
    [
        "nome",
        "referente",
        "citta",
        "tipo_prodotto",
        "clienti_ideali",
        "obiettivo",
        "canali",
    ],
)
def test_ca07_obbligatorio_mancante_non_crea(db, client, utente_di_prova, campo):
    persona = utente_di_prova()
    dati = dict(DATI)
    del dati[campo]
    risposta = client.put("/api/profilo", json=dati)
    assert risposta.status_code == 422
    assert campo in risposta.json()["detail"]
    assert service.profilo_di(db, persona.id) is None


@pytest.mark.parametrize(
    "campo,valore",
    [
        ("nome", "  "),
        ("clienti_ideali", ""),
        ("canali", []),
        ("canali", ["tiktok"]),
        ("canali", ["facebook", "facebook"]),
        ("tipo_prodotto", "inesistente"),
        ("obiettivo", "inesistente"),
        ("fascia_prezzo", "inesistente"),
        ("cortesia", "inesistente"),
        ("frequenza", "inesistente"),
        ("valori", ["inesistente"]),
        ("tono", ["inesistente"]),
        ("anni_attivita", -1),
        ("anni_attivita", 2147483648),
        ("anni_attivita", True),
        ("foto_policy", {"persone": "inesistente"}),
        ("social_esistenti", {"canali": ["nessuno", "facebook"]}),
        ("social_esistenti", {"profili": 12}),
        (
            "eventi_ricorrenti",
            [{"nome": "Fiera", "quando": "ottobre", "tipo": "inesistente"}],
        ),
        ("storia", "Privato\x00"),
        ("storia", "Privato\ud800"),
        ("orari", {"lunedi": "Privato\x00"}),
        ("orari", {"numero": float("inf")}),
        ("id", 999),
        ("utente_id", 999),
        ("logo", "../../Privato"),
    ],
)
def test_dati_invalidi_non_modificano_profilo(
    db, client, utente_di_prova, campo, valore
):
    persona = utente_di_prova()
    record = profilo(db, utente_id=persona.id)
    risposta = client.put(
        "/api/profilo",
        content=json.dumps(dict(DATI, **{campo: valore}), ensure_ascii=True),
        headers={"Content-Type": "application/json"},
    )
    assert risposta.status_code == 422
    assert isinstance(risposta.json()["detail"], str)
    assert "Privato" not in risposta.text
    db.refresh(record)
    assert record.nome == "Bottega di prova"


def test_profilo_completo_roundtrip_e_sostituzione_opzionali(client, utente_di_prova):
    utente_di_prova()
    dati = dict(
        DATI,
        anni_attivita=12,
        storia="Tradizione",
        valori=["artigianalita"],
        tono=["caldo"],
        foto_policy={
            "quantita_mese": "meno_5",
            "chi_scatta": "artigiano",
            "persone": "mai",
        },
        social_esistenti={
            "canali": ["facebook"],
            "profili": "Pagina",
            "cosa_funziona": "Foto",
        },
        orari={"lunedi": ["09:00", "18:00"]},
        eventi_ricorrenti=[
            {"nome": "Fiera", "quando": "ottobre", "tipo": "fiera_mercatino"}
        ],
    )
    risposta = client.put("/api/profilo", json=dati)
    assert risposta.status_code == 200
    assert all(risposta.json()[k] == v for k, v in dati.items())
    assert client.put("/api/profilo", json=DATI).json()["storia"] is None


def test_artigiani_isolati_e_account_logo_preservati(db, client, utente_di_prova):
    persona = utente_di_prova()
    mio = profilo(db, utente_id=persona.id, logo="logo-server.png")
    altro = profilo(db, nome="Bottega altrui")
    account = db.scalar(select(AccountSocial).where(AccountSocial.profilo_id == mio.id))
    account.permesso = "PermessoSegreto"
    db.flush()
    risposta = client.put("/api/profilo", json=DATI)
    assert risposta.status_code == 200
    assert risposta.json()["id"] == mio.id
    assert risposta.json()["logo"] == "logo-server.png"
    assert "PermessoSegreto" not in risposta.text
    db.refresh(altro)
    db.refresh(account)
    assert altro.nome == "Bottega altrui"
    assert account.permesso == "PermessoSegreto"
    assert client.get("/api/canali").json()[1]["collegato"]


def test_ca16_modifica_profilo_non_altera_snapshot(db, client, utente_di_prova):
    persona = utente_di_prova()
    mio = profilo(db, utente_id=persona.id)
    campagna = campagna_inviata(db, profilo_id=mio.id)
    prima = deepcopy(campagna.profilo_snapshot)
    assert client.put("/api/profilo", json=DATI).status_code == 200
    db.refresh(campagna)
    assert campagna.profilo_snapshot == prima


@pytest.mark.parametrize("metodo", ["get", "put"])
@pytest.mark.parametrize("ruolo", [None, "operatore", "admin", "artigiano"])
def test_permessi_con_sessione_reale(db, client, metodo, ruolo):
    if ruolo is not None:
        persona = utente(db, ruolo=ruolo)
        _, token = accesso.login(db, persona.email, PASSWORD_DI_PROVA, ORA)
        client.cookies.set(accesso.COOKIE_SESSIONE, token)
        app.dependency_overrides[adesso] = lambda: ORA
    risposta = getattr(client, metodo)(
        "/api/profilo", **({"json": DATI} if metodo == "put" else {})
    )
    atteso = (
        401
        if ruolo is None
        else 403
        if ruolo != "artigiano"
        else 404
        if metodo == "get"
        else 200
    )
    assert risposta.status_code == atteso


def test_service_non_fa_commit_e_rollback_annulla(db):
    persona = utente(db)
    record = service.salva_profilo_personale(
        db, persona.id, ProfiloScrittura(**DATI), ORA
    )
    assert record.nome == DATI["nome"]
    db.rollback()
    assert (
        db.scalar(select(ProfiloBottega).where(ProfiloBottega.utente_id == persona.id))
        is None
    )


def test_prime_scritture_concorrenti_creano_un_solo_profilo(motore_test):
    from concurrent.futures import ThreadPoolExecutor

    with Session(motore_test) as preparazione, preparazione.begin():
        persona = utente(preparazione)
        persona_id = persona.id

    def salva(numero):
        with Session(motore_test) as sessione, sessione.begin():
            record = service.salva_profilo_personale(
                sessione,
                persona_id,
                ProfiloScrittura(**dict(DATI, nome=f"Bottega {numero}")),
                ORA,
            )
            return record.id

    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(salva, range(4)))
    assert len(set(ids)) == 1
    with Session(motore_test) as controllo, controllo.begin():
        record = service.profilo_di(controllo, persona_id)
        assert record.id == ids[0]
        assert (
            controllo.scalar(
                select(func.count())
                .select_from(ProfiloBottega)
                .where(ProfiloBottega.utente_id == persona_id)
            )
            == 1
        )
        controllo.delete(record)
        from app.moduli.accesso.models import Utente

        controllo.delete(controllo.get(Utente, persona_id))
