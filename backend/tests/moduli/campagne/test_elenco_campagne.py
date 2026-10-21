"""Test di ``GET /campagne?artigiano=``: le campagne di un artigiano (T3-71, spec R-38, CA-94)."""

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_in_bozza


def test_ca94_operatore_filtra_per_artigiano(
    db: Session, client: TestClient, utente_di_prova
):
    utente_di_prova("operatore")
    primo = utente(db, "artigiano")
    bottega = profilo(db, utente_id=primo.id, nome="Ceramiche Rossi", citta="Faenza")
    sua = campagna_attiva(db, profilo_id=bottega.id)
    sua_bozza = campagna_in_bozza(db, profilo_id=bottega.id)
    campagna_attiva(db, profilo_id=profilo(db).id)  # di un altro artigiano

    assert len(client.get("/api/campagne").json()) == 3

    risposta = client.get("/api/campagne", params={"artigiano": primo.id})
    assert risposta.status_code == 200
    righe = risposta.json()
    assert [r["id"] for r in righe] == [sua_bozza.id, sua.id]
    assert {r["bottega"] for r in righe} == {"Ceramiche Rossi"}
    assert {r["citta"] for r in righe} == {"Faenza"}

    # Il filtro per stato si combina con quello per artigiano.
    solo_attive = client.get(
        "/api/campagne", params={"artigiano": primo.id, "stato": "attiva"}
    ).json()
    assert [r["id"] for r in solo_attive] == [sua.id]

    # Un artigiano senza profilo non ha campagne.
    senza_profilo = utente(db, "artigiano")
    assert (
        client.get("/api/campagne", params={"artigiano": senza_profilo.id}).json() == []
    )


def test_ca94_artigiano_non_trovato_404(
    db: Session, client: TestClient, utente_di_prova
):
    utente_di_prova("admin")
    un_operatore = utente(db, "operatore")

    for id_ in (un_operatore.id, 987654):
        risposta = client.get("/api/campagne", params={"artigiano": id_})
        assert risposta.status_code == 404
        assert risposta.json() == {"detail": "Artigiano non trovato."}


def test_ca94_artigiano_vede_solo_le_sue(
    db: Session, client: TestClient, utente_di_prova
):
    proprietario = utente_di_prova("artigiano")
    mia = campagna_attiva(db, profilo_id=profilo(db, utente_id=proprietario.id).id)
    altro = utente(db, "artigiano")
    campagna_attiva(db, profilo_id=profilo(db, utente_id=altro.id).id)

    # Il parametro non conta: nemmeno con l'id di un altro, nemmeno con uno falso.
    for id_ in (altro.id, 987654):
        risposta = client.get("/api/campagne", params={"artigiano": id_})
        assert risposta.status_code == 200
        assert [r["id"] for r in risposta.json()] == [mia.id]
