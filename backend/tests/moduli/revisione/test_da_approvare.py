"""Test di ``GET /da-approvare`` (T2b-45, spec §4, R-38, CA-69)."""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.core.orologio import ROMA
from app.moduli.campagne.models import DecisioneCampagna
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_conclusa,
    campagna_in_bozza,
    campagna_in_revisione,
    campagna_inviata,
    nota_interna,
)
from tests.moduli.contenuti.fabbrica import post_da_approvare

PRIMA = datetime(2030, 2, 2, 9, tzinfo=timezone.utc)
DOPO = datetime(2030, 2, 5, 9, tzinfo=timezone.utc)


def test_ca69_conteggi_entro_quando_e_ultima_nota(
    db: Session, client: TestClient, utente_di_prova
):
    """CA-69: conteggi, entro quando e ultima nota, dalla più urgente."""
    operatore = utente_di_prova("operatore")
    artigiano = utente(db, "artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["instagram", "facebook"])

    # Senza post: "entro quando" sono le 00:00 del giorno di inizio (R-38).
    senza_piano = campagna_inviata(
        db, profilo_id=bottega.id, inizio=date(2030, 1, 20), fine=date(2030, 2, 10)
    )
    in_revisione = campagna_in_revisione(
        db, profilo_id=bottega.id, inizio=date(2030, 2, 1), fine=date(2030, 2, 28)
    )
    post_da_approvare(db, campagna_id=in_revisione.id, data_ora=DOPO)
    post_da_approvare(
        db,
        campagna_id=in_revisione.id,
        canale="facebook",
        data_ora=PRIMA,
        riempitivo="cartolina",
    )
    post_da_approvare(db, campagna_id=in_revisione.id, data_ora=DOPO, da_rivedere=True)
    nota_interna(db, in_revisione, nota="Prima nota.", utente_id=operatore.id)
    nota_interna(db, in_revisione, nota="Ultima nota.", utente_id=operatore.id)
    db.add(
        DecisioneCampagna(
            campagna_id=in_revisione.id,
            utente_id=operatore.id,
            esito="approvata",
            foto_segnate=[],
        )
    )

    # Fuori dalla sezione: conclusa, bozza e la campagna di un altro stato.
    campagna_conclusa(db, profilo_id=bottega.id)
    campagna_in_bozza(db, profilo_id=bottega.id)

    risposta = client.get("/api/da-approvare")
    assert risposta.status_code == 200
    righe = risposta.json()
    assert [r["id"] for r in righe] == [senza_piano.id, in_revisione.id]

    prima_riga = righe[0]
    assert prima_riga["bottega"] == bottega.nome
    assert prima_riga["citta"] == bottega.citta
    assert prima_riga["conteggi"] == {
        "totale": 0,
        "da_approvare": 0,
        "da_rivedere": 0,
        "riempitivi": {},
    }
    assert datetime.fromisoformat(prima_riga["entro_quando"]) == datetime(
        2030, 1, 20, 0, 0, tzinfo=ROMA
    )
    assert prima_riga["ultima_nota"] is None

    seconda = righe[1]
    assert seconda["conteggi"]["totale"] == 3
    assert seconda["conteggi"]["da_approvare"] == 3
    assert seconda["conteggi"]["da_rivedere"] == 1
    assert seconda["conteggi"]["riempitivi"] == {"facebook": 1}
    # Entro quando = la data del primo post da approvare, non l'ultima nota.
    assert datetime.fromisoformat(seconda["entro_quando"]) == PRIMA
    assert seconda["ultima_nota"] == "Ultima nota."


def test_da_approvare_riservata_all_operatore(
    db: Session, client: TestClient, utente_di_prova
):
    utente_di_prova("artigiano")
    assert client.get("/api/da-approvare").status_code == 403

    utente_di_prova("operatore")
    assert client.get("/api/da-approvare").status_code == 200
