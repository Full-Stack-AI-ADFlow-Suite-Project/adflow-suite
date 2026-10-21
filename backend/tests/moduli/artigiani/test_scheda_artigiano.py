"""Test di ``GET /artigiani/{id}``, la pagina dell'artigiano (T3-71, spec R-38, CA-93)."""

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.moduli.artigiani.profilo_schemas import ProfiloPubblico
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import account_social, profilo


def test_ca93_scheda_con_profilo_e_canali(
    db: Session, client: TestClient, utente_di_prova
):
    utente_di_prova("operatore")
    artigiano = utente(db, "artigiano", nome="Mario Rossi", email="mario@example.test")
    bottega = profilo(
        db,
        utente_id=artigiano.id,
        nome="Ceramiche Rossi",
        canali=["instagram"],
    )
    account_social(db, bottega, piattaforma="facebook", stato="scaduto")

    risposta = client.get(f"/api/artigiani/{artigiano.id}")
    assert risposta.status_code == 200
    assert risposta.headers["Cache-Control"] == "no-store"
    scheda = risposta.json()
    assert scheda["id"] == artigiano.id
    assert scheda["nome"] == "Mario Rossi"
    assert scheda["email"] == "mario@example.test"
    assert scheda["attivo"] is True
    assert scheda["canali_collegati"] == ["instagram"]
    # Il profilo ha la stessa forma di GET /profilo.
    assert set(scheda["profilo"]) == set(ProfiloPubblico.model_fields)
    assert scheda["profilo"]["nome"] == "Ceramiche Rossi"
    assert scheda["profilo"]["citta"] == bottega.citta


def test_ca93_senza_profilo(db: Session, client: TestClient, utente_di_prova):
    utente_di_prova("operatore")
    artigiano = utente(db, "artigiano", attivo=False)

    scheda = client.get(f"/api/artigiani/{artigiano.id}").json()
    assert scheda["profilo"] is None
    assert scheda["canali_collegati"] == []
    assert scheda["attivo"] is False


def test_ca93_operatore_o_inesistente_404(
    db: Session, client: TestClient, utente_di_prova
):
    utente_di_prova("operatore")
    altro_operatore = utente(db, "operatore")

    for id_ in (altro_operatore.id, 987654):
        risposta = client.get(f"/api/artigiani/{id_}")
        assert risposta.status_code == 404
        assert risposta.json() == {"detail": "Artigiano non trovato."}


def test_ca93_artigiano_403(db: Session, client: TestClient, utente_di_prova):
    proprietario = utente_di_prova("artigiano")
    assert client.get(f"/api/artigiani/{proprietario.id}").status_code == 403

    utente_di_prova("admin")
    assert client.get(f"/api/artigiani/{proprietario.id}").status_code == 200
