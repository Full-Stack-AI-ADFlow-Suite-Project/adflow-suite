"""Test di ``GET /archivio-foto``, l'archivio in sola lettura (T3-72, spec R-47, CA-95, CA-96)."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_in_bozza,
    foto,
    gruppo,
    gruppo_di_archivio,
)


def _campagna(db: Session, bottega, stato: str, *, caricate: int, ai: int):
    """Una campagna in quello stato con ``caricate`` foto e ``ai`` immagini AI."""
    campagna = campagna_in_bozza(db, profilo_id=bottega.id, stato=stato)
    mazzo = gruppo(db, campagna)
    ids = [foto(db, gruppo=mazzo).id for _ in range(caricate)]
    ids_ai = [
        foto(db, gruppo=mazzo, gruppo_id=None, origine="creata_ai").id
        for _ in range(ai)
    ]
    return campagna, ids, ids_ai


def test_ca95_artigiano_blocchi_per_campagna(
    db: Session, client: TestClient, utente_di_prova
):
    proprietario = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=proprietario.id)
    bozza, ids_bozza, _ = _campagna(db, bottega, "bozza", caricate=2, ai=0)
    revisione, ids_rev, _ = _campagna(db, bottega, "in_revisione", caricate=3, ai=2)
    attiva, ids_att, ids_att_ai = _campagna(db, bottega, "attiva", caricate=2, ai=1)
    # L'archivio di prima: foto senza campagna, in fondo.
    vecchio = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=1)

    risposta = client.get("/api/archivio-foto")
    assert risposta.status_code == 200
    blocchi = risposta.json()

    # Dalla più recente; le foto in ordine di id.
    assert [b["campagna"] and b["campagna"]["id"] for b in blocchi] == [
        attiva.id,
        revisione.id,
        bozza.id,
        None,
    ]
    assert [f["id"] for f in blocchi[0]["foto"]] == ids_att + ids_att_ai
    assert [f["id"] for f in blocchi[1]["foto"]] == ids_rev  # niente immagini AI
    assert [f["id"] for f in blocchi[2]["foto"]] == ids_bozza
    assert [f["id"] for f in blocchi[3]["foto"]] == [f.id for f in vecchio.foto]

    assert blocchi[0]["campagna"] == {
        "id": attiva.id,
        "titolo": attiva.titolo,
        "stato": "attiva",
        "inizio": attiva.inizio.isoformat(),
        "fine": attiva.fine.isoformat(),
    }
    prima = blocchi[0]["foto"][0]
    assert prima["url"] == f"/api/foto/{prima['id']}/file"
    assert prima["origine"] == "caricata"
    assert (prima["mime"], prima["larghezza"], prima["altezza"]) == (
        "image/jpeg",
        1080,
        1350,
    )
    assert prima["pubblicata_su"] == {}
    assert blocchi[0]["foto"][-1]["origine"] == "creata_ai"


def test_ca95_immagini_ai_solo_dopo_l_approvazione(
    db: Session, client: TestClient, utente_di_prova
):
    proprietario = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=proprietario.id)
    approvate = [
        _campagna(db, bottega, stato, caricate=0, ai=1)[0].id
        for stato in ("attiva", "sospesa", "conclusa", "annullata")
    ]
    for stato in ("inviata", "in_generazione", "generazione_fallita", "in_revisione"):
        _campagna(db, bottega, stato, caricate=1, ai=1)
    _campagna(db, bottega, "respinta", caricate=1, ai=1)

    blocchi = client.get("/api/archivio-foto").json()
    for blocco in blocchi:
        origini = {f["origine"] for f in blocco["foto"]}
        if blocco["campagna"]["id"] in approvate:
            assert origini == {"creata_ai"}
        else:
            assert origini == {"caricata"}


def test_ca95_niente_cartoline_niente_foto_di_altri(
    db: Session, client: TestClient, utente_di_prova
):
    proprietario = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=proprietario.id)
    campagna, ids, _ = _campagna(db, bottega, "attiva", caricate=1, ai=0)
    mazzo = gruppo(db, campagna)
    foto(db, gruppo=mazzo, gruppo_id=None, origine="cartolina")

    altro = utente(db, "artigiano")
    _campagna(db, profilo(db, utente_id=altro.id), "attiva", caricate=2, ai=1)

    blocchi = client.get("/api/archivio-foto").json()
    assert [f["id"] for b in blocchi for f in b["foto"]] == ids

    # Un artigiano senza profilo ha l'archivio vuoto. E il parametro non conta.
    utente_di_prova("artigiano")
    assert client.get("/api/archivio-foto", params={"artigiano": altro.id}).json() == []


def test_ca96_operatore_tutte_le_foto_dell_artigiano(
    db: Session, client: TestClient, utente_di_prova
):
    utente_di_prova("operatore")
    proprietario = utente(db, "artigiano")
    bottega = profilo(db, utente_id=proprietario.id)
    revisione, ids_rev, ids_rev_ai = _campagna(
        db, bottega, "in_revisione", caricate=2, ai=2
    )
    pubblicata = foto(db, campagna=revisione, pubblicata_su={})
    pubblicata.pubblicata_su = {
        "facebook": "2030-01-05T12:00:00+00:00",
        "instagram": "2030-01-06T09:30:00+00:00",
    }
    db.flush()
    _campagna(db, profilo(db), "attiva", caricate=3, ai=0)  # di un altro artigiano

    risposta = client.get("/api/archivio-foto", params={"artigiano": proprietario.id})
    assert risposta.status_code == 200
    blocchi = risposta.json()
    assert [b["campagna"]["id"] for b in blocchi] == [revisione.id]
    visibili = {f["id"]: f for b in blocchi for f in b["foto"]}
    # All'operatore anche le immagini AI di una campagna in revisione.
    assert set(ids_rev + ids_rev_ai + [pubblicata.id]) == set(visibili)
    assert {
        canale: datetime.fromisoformat(quando)
        for canale, quando in visibili[pubblicata.id]["pubblicata_su"].items()
    } == {
        "facebook": datetime(2030, 1, 5, 12, tzinfo=timezone.utc),
        "instagram": datetime(2030, 1, 6, 9, 30, tzinfo=timezone.utc),
    }


def test_ca96_operatore_senza_artigiano_422(
    db: Session, client: TestClient, utente_di_prova
):
    for ruolo in ("operatore", "admin"):
        utente_di_prova(ruolo)
        risposta = client.get("/api/archivio-foto")
        assert risposta.status_code == 422
        assert risposta.json() == {
            "detail": "Indica l'artigiano di cui vedere le foto."
        }


def test_ca96_id_non_artigiano_404(db: Session, client: TestClient, utente_di_prova):
    utente_di_prova("operatore")
    un_operatore = utente(db, "operatore")
    for id_ in (un_operatore.id, 987654):
        risposta = client.get("/api/archivio-foto", params={"artigiano": id_})
        assert risposta.status_code == 404
        assert risposta.json() == {"detail": "Artigiano non trovato."}


def test_archivio_foto_in_sola_lettura(
    db: Session, client: TestClient, utente_di_prova
):
    utente_di_prova("artigiano")
    for metodo in (client.post, client.put, client.patch, client.delete):
        assert metodo("/api/archivio-foto").status_code == 405
