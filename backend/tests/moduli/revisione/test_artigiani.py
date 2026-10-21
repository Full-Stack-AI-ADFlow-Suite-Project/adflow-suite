"""Test di ``GET /artigiani`` e ``GET /artigiani/{id}`` (elenco e scheda, plan §3)."""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import account_social, profilo
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_conclusa,
    campagna_in_bozza,
    campagna_in_revisione,
    campagna_inviata,
    campagna_sospesa,
)
from tests.moduli.contenuti.fabbrica import (
    post_approvato,
    post_da_approvare,
    post_fallito,
)


def test_elenco_artigiani_con_situazione_campagne(
    db: Session, client: TestClient, utente_di_prova
):
    """Ogni riga porta account, profilo, canali e il quadro delle campagne."""
    utente_di_prova("operatore")
    primo = utente(db, "artigiano", nome="Mario Bianchi")
    bottega = profilo(
        db,
        utente_id=primo.id,
        nome="Falegnameria Bianchi",
        citta="Bra (CN)",
        canali=["facebook", "instagram"],
    )
    secondo = utente(db, "artigiano", nome="Anna Olivero")
    ceramiche = profilo(db, utente_id=secondo.id, nome="Ceramiche Olivero")
    # Senza profilo: la riga c'è lo stesso, con bottega e città nulle.
    terzo = utente(db, "artigiano", nome="Luca Ferrero", attivo=False)
    # Operatore e admin non entrano nell'elenco.
    utente(db, "operatore")
    utente(db, "admin")

    urgente = campagna_in_revisione(
        db, profilo_id=bottega.id, inizio=date(2030, 3, 1), fine=date(2030, 3, 31)
    )
    post_da_approvare(
        db,
        campagna_id=urgente.id,
        data_ora=datetime(2030, 3, 2, 9, tzinfo=timezone.utc),
    )
    campagna_attiva(db, profilo_id=bottega.id)
    campagna_conclusa(db, profilo_id=bottega.id)
    in_ritardo = campagna_inviata(
        db, profilo_id=ceramiche.id, inizio=date(2030, 1, 10), fine=date(2030, 2, 10)
    )

    risposta = client.get("/api/artigiani")
    assert risposta.status_code == 200
    # Altri test lasciano artigiani nel database: si guardano solo questi tre.
    creati = {primo.id, secondo.id, terzo.id}
    righe = [r for r in risposta.json() if r["id"] in creati]
    assert [r["id"] for r in righe] == [secondo.id, primo.id, terzo.id]

    prima = righe[0]  # Ceramiche Olivero: scadenza più vicina (inizio senza piano)
    assert prima["bottega"] == "Ceramiche Olivero"
    assert prima["n_da_approvare"] == 1
    assert prima["n_in_corso"] == 0
    assert prima["prossima_scadenza"] is not None
    assert prima["prossima_campagna_id"] == in_ritardo.id

    seconda = righe[1]
    assert seconda["bottega"] == "Falegnameria Bianchi"
    assert seconda["citta"] == "Bra (CN)"
    assert seconda["email"] == primo.email
    assert seconda["canali_collegati"] == ["facebook", "instagram"]
    assert seconda["n_da_approvare"] == 1
    assert seconda["n_in_corso"] == 1
    assert seconda["prossima_campagna_id"] == urgente.id

    terza = righe[2]
    assert terza["bottega"] is None
    assert terza["citta"] is None
    assert terza["profilo_id"] is None
    assert terza["attivo"] is False
    assert terza["n_da_approvare"] == 0
    assert terza["prossima_scadenza"] is None


def test_scheda_artigiano_per_sezioni(db: Session, client: TestClient, utente_di_prova):
    """Dettaglio: account, profilo, bozza, da approvare, in corso, ultime 3 chiuse."""
    utente_di_prova("operatore")
    record = utente(db, "artigiano", nome="Mario Bianchi")
    bottega = profilo(
        db, utente_id=record.id, nome="Falegnameria Bianchi", canali=["facebook"]
    )
    account_social(db, bottega, piattaforma="instagram", stato="scaduto")

    bozza = campagna_in_bozza(db, profilo_id=bottega.id, titolo="Bozza maggio")
    in_revisione = campagna_in_revisione(db, profilo_id=bottega.id)
    post_da_approvare(db, campagna_id=in_revisione.id)
    attiva = campagna_attiva(db, profilo_id=bottega.id, titolo="Aprile")
    post_approvato(db, campagna_id=attiva.id)
    post_fallito(db, campagna_id=attiva.id)
    sospesa = campagna_sospesa(db, profilo_id=bottega.id)
    for titolo, inizio in (
        ("Una", date(2029, 7, 1)),
        ("Due", date(2029, 8, 1)),
        ("Tre", date(2029, 9, 1)),
        ("Quattro", date(2029, 10, 1)),
    ):
        campagna_conclusa(db, profilo_id=bottega.id, titolo=titolo, inizio=inizio)

    risposta = client.get(f"/api/artigiani/{record.id}")
    assert risposta.status_code == 200
    scheda = risposta.json()

    assert scheda["artigiano"] == {
        "id": record.id,
        "email": record.email,
        "nome": "Mario Bianchi",
        "attivo": True,
    }
    assert scheda["profilo"]["nome"] == "Falegnameria Bianchi"
    # Solo facebook è collegato: instagram è scaduto.
    assert scheda["canali_collegati"] == ["facebook"]
    assert scheda["bozza"]["id"] == bozza.id
    assert [c["id"] for c in scheda["da_approvare"]] == [in_revisione.id]
    assert scheda["da_approvare"][0]["conteggi"]["da_approvare"] == 1
    assert {c["id"] for c in scheda["in_corso"]} == {attiva.id, sospesa.id}
    attiva_vista = next(c for c in scheda["in_corso"] if c["id"] == attiva.id)
    assert attiva_vista["n_post"] == 2
    assert attiva_vista["n_falliti"] == 1
    # Le ultime 3 chiuse per data, con il totale di tutte.
    assert scheda["totale_chiuse"] == 4
    assert len(scheda["chiuse"]) == 3
    assert [c["titolo"] for c in scheda["chiuse"]] == ["Quattro", "Tre", "Due"]
    assert scheda["chiuse"][0]["n_foto"] == 4


def test_scheda_artigiano_senza_profilo(
    db: Session, client: TestClient, utente_di_prova
):
    """L'account esiste ma il profilo non è compilato: sezioni vuote, nessun errore."""
    utente_di_prova("operatore")
    record = utente(db, "artigiano", nome="Nuovo arrivato")

    risposta = client.get(f"/api/artigiani/{record.id}")
    assert risposta.status_code == 200
    scheda = risposta.json()
    assert scheda["artigiano"]["nome"] == "Nuovo arrivato"
    assert scheda["profilo"] is None
    assert scheda["canali_collegati"] == []
    assert scheda["bozza"] is None
    assert scheda["da_approvare"] == []
    assert scheda["in_corso"] == []
    assert scheda["chiuse"] == []
    assert scheda["totale_chiuse"] == 0


def test_scheda_artigiano_non_trovato(db: Session, client: TestClient, utente_di_prova):
    """404 se l'id non esiste o non è di un artigiano."""
    utente_di_prova("operatore")
    operatore = utente(db, "operatore")

    assert client.get("/api/artigiani/999999").status_code == 404
    assert client.get(f"/api/artigiani/{operatore.id}").status_code == 404


def test_artigiani_riservati_all_operatore(
    db: Session, client: TestClient, utente_di_prova
):
    """L'artigiano non legge l'elenco né la scheda; l'admin passa (R-29)."""
    record = utente(db, "artigiano")

    utente_di_prova("artigiano")
    assert client.get("/api/artigiani").status_code == 403
    assert client.get(f"/api/artigiani/{record.id}").status_code == 403

    utente_di_prova("operatore")
    assert client.get("/api/artigiani").status_code == 200

    utente_di_prova("admin")
    assert client.get("/api/artigiani").status_code == 200
    assert client.get(f"/api/artigiani/{record.id}").status_code == 200
