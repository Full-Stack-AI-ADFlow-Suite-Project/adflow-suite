"""Test di ``GET /artigiani``, l'elenco degli artigiani dell'operatore (T3-71, spec R-38, CA-92)."""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.core.orologio import ROMA
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
from tests.moduli.contenuti.fabbrica import post_da_approvare

PRIMA = datetime(2030, 2, 2, 9, tzinfo=timezone.utc)
DOPO = datetime(2030, 2, 5, 9, tzinfo=timezone.utc)


def test_ca92_elenco_con_la_situazione_delle_campagne(
    db: Session, client: TestClient, utente_di_prova
):
    """CA-92: canali collegati, campagne da approvare e in corso, prossima scadenza."""
    utente_di_prova("operatore")
    artigiano = utente(db, "artigiano", nome="Mario Rossi", email="mario@example.test")
    bottega = profilo(
        db,
        utente_id=artigiano.id,
        nome="Ceramiche Rossi",
        referente="Mario",
        citta="Faenza",
        canali=["instagram"],
    )
    account_social(db, bottega, piattaforma="facebook", stato="scollegato")

    in_revisione = campagna_in_revisione(
        db, profilo_id=bottega.id, inizio=date(2030, 2, 1), fine=date(2030, 2, 28)
    )
    post_da_approvare(db, campagna_id=in_revisione.id, data_ora=DOPO)
    post_da_approvare(db, campagna_id=in_revisione.id, data_ora=PRIMA)
    # Senza piano: «entro quando» sono le 00:00 del giorno di inizio.
    campagna_inviata(
        db, profilo_id=bottega.id, inizio=date(2030, 3, 10), fine=date(2030, 3, 31)
    )
    campagna_attiva(db, profilo_id=bottega.id)
    campagna_sospesa(db, profilo_id=bottega.id)
    # Non contano né tra le da approvare né tra le in corso.
    campagna_in_bozza(db, profilo_id=bottega.id)
    campagna_conclusa(db, profilo_id=bottega.id)

    # Gli operatori e gli admin non sono artigiani.
    utente(db, "operatore")
    utente(db, "admin")

    risposta = client.get("/api/artigiani")
    assert risposta.status_code == 200
    righe = risposta.json()
    assert [r["id"] for r in righe] == [artigiano.id]
    riga = righe[0]
    assert riga["nome"] == "Mario Rossi"
    assert riga["email"] == "mario@example.test"
    assert riga["attivo"] is True
    assert riga["bottega"] == "Ceramiche Rossi"
    assert riga["referente"] == "Mario"
    assert riga["citta"] == "Faenza"
    assert riga["canali_collegati"] == ["instagram"]
    assert riga["n_da_approvare"] == 2
    assert riga["n_in_corso"] == 2
    assert datetime.fromisoformat(riga["prossima_scadenza"]) == PRIMA


def test_ca92_artigiano_senza_profilo_e_non_attivo(
    db: Session, client: TestClient, utente_di_prova
):
    """CA-92: anche chi non ha il profilo e chi non è attivo sta nell'elenco."""
    utente_di_prova("operatore")
    senza_profilo = utente(db, "artigiano", nome="Nuovo Artigiano")
    sospeso = utente(db, "artigiano", nome="Account Spento", attivo=False)
    profilo(db, utente_id=sospeso.id, nome="Bottega Spenta")

    righe = {r["id"]: r for r in client.get("/api/artigiani").json()}
    assert set(righe) == {senza_profilo.id, sospeso.id}

    nuovo = righe[senza_profilo.id]
    assert nuovo["bottega"] is None
    assert nuovo["referente"] is None
    assert nuovo["citta"] is None
    assert nuovo["canali_collegati"] == []
    assert nuovo["n_da_approvare"] == 0
    assert nuovo["n_in_corso"] == 0
    assert nuovo["prossima_scadenza"] is None

    spento = righe[sospeso.id]
    assert spento["attivo"] is False
    assert spento["bottega"] == "Bottega Spenta"


def test_ca92_ordine_per_scadenza_poi_bottega(
    db: Session, client: TestClient, utente_di_prova
):
    """CA-92: prima la scadenza più vicina; chi non l'ha va in fondo, per bottega."""
    utente_di_prova("operatore")

    def artigiano_con(nome_bottega: str | None, inizio: date | None = None) -> int:
        # Senza profilo conta il nome dell'account.
        proprietario = utente(db, "artigiano", nome=nome_bottega or "gamma")
        if nome_bottega is None:
            return proprietario.id
        bottega = profilo(db, utente_id=proprietario.id, nome=nome_bottega)
        if inizio is not None:
            campagna_inviata(db, profilo_id=bottega.id, inizio=inizio, fine=inizio)
        return proprietario.id

    lontano = artigiano_con("Zeta", date(2030, 6, 1))
    vicino = artigiano_con("Omega", date(2030, 3, 1))
    senza_b = artigiano_con("beta")
    senza_a = artigiano_con("Alfa")
    senza_profilo = artigiano_con(None)

    ordine = [r["id"] for r in client.get("/api/artigiani").json()]
    assert ordine == [
        vicino,
        lontano,
        senza_a,
        senza_b,
        senza_profilo,
    ]  # Alfa, beta, gamma

    scadenze = {
        r["id"]: r["prossima_scadenza"] for r in client.get("/api/artigiani").json()
    }
    assert datetime.fromisoformat(scadenze[vicino]) == datetime(2030, 3, 1, tzinfo=ROMA)


def test_ca92_artigiano_403_admin_passa(
    db: Session, client: TestClient, utente_di_prova
):
    utente_di_prova("artigiano")
    assert client.get("/api/artigiani").status_code == 403

    utente_di_prova("admin")
    assert client.get("/api/artigiani").status_code == 200
