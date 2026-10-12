"""T2b-22: le viste della campagna per l'artigiano (spec §4).

Verifica i criteri di accettazione:
- CA-31: campagna respinta → l'artigiano vede motivo, nota e foto da rifare.
- CA-53: il canale tolto compare con la nota dell'operatore.
- CA-70: con più campagne l'elenco arriva nell'ordine di apertura e le
  "campagne passate" in fondo.
- R-32: le note interne non arrivano mai all'artigiano.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.moduli.campagne.models import Foto
from app.moduli.campagne.service import registra_decisione
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_in_bozza,
    campagna_inviata,
    nota_interna,
)


def test_elenco_ordine_di_apertura_e_passate_ca70(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-70: prima la campagna che chiede qualcosa, in fondo le passate."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    conclusa = campagna_in_bozza(db, profilo_id=bottega.id, stato="conclusa")
    respinta_vecchia = campagna_in_bozza(db, profilo_id=bottega.id, stato="respinta")
    attiva = campagna_in_bozza(db, profilo_id=bottega.id, stato="attiva")
    in_revisione = campagna_in_bozza(db, profilo_id=bottega.id, stato="in_revisione")
    bozza = campagna_in_bozza(db, profilo_id=bottega.id)
    scaduta = campagna_in_bozza(db, profilo_id=bottega.id, stato="scaduta")
    altrui = campagna_inviata(db)

    risposta = client.get("/api/campagne")
    assert risposta.status_code == 200
    ids = [c["id"] for c in risposta.json()]
    # bozza → scaduta non sostituita → in corso → in lavorazione → passate.
    assert ids == [
        bozza.id,
        scaduta.id,
        attiva.id,
        in_revisione.id,
        respinta_vecchia.id,
        conclusa.id,
    ]
    assert altrui.id not in ids

    filtrata = client.get("/api/campagne?stato=attiva")
    assert [c["id"] for c in filtrata.json()] == [attiva.id]


def test_dettaglio_respinta_motivo_nota_e_foto_segnate_ca31(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-31: respinta → l'artigiano legge motivo, nota e foto da rifare."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    campagna.stato = "respinta"
    campagna.chiusa_il = datetime(2030, 1, 5, tzinfo=timezone.utc)
    db.flush()
    operatore = utente(db, "operatore")
    foto_segnate = list(
        db.scalars(select(Foto).where(Foto.campagna_id == campagna.id).limit(2))
    )
    registra_decisione(
        db,
        campagna,
        operatore.id,
        "respinta",
        "foto",
        "Le foto del banco sono troppo buie.",
        [f.id for f in foto_segnate],
    )
    nota_interna(db, campagna, nota="Ricontrollare i prezzi.", utente_id=operatore.id)

    risposta = client.get(f"/api/campagne/{campagna.id}")
    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["esito_respinta"] == {
        "motivo": "foto",
        "nota": "Le foto del banco sono troppo buie.",
        "foto_segnate": [f.id for f in foto_segnate],
    }
    # R-32: né la nota interna né la decisione stessa arrivano all'artigiano.
    assert corpo["decisioni"] == []
    assert corpo["profilo_snapshot"] is None


def test_dettaglio_canale_tolto_con_nota_ca53(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-53: il canale tolto si vede con la nota; le altre decisioni no."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["facebook", "instagram"])
    campagna = campagna_inviata(db, profilo_id=bottega.id, canali_tolti=["instagram"])
    campagna.stato = "attiva"
    db.flush()
    operatore = utente(db, "operatore")
    registra_decisione(db, campagna, operatore.id, "approvata", None, None, [])
    nota_interna(db, campagna, nota="Mario risponde tardi.", utente_id=operatore.id)
    registra_decisione(
        db,
        campagna,
        operatore.id,
        "canale_tolto",
        None,
        "Le foto non sono adatte a Instagram.",
        [],
        canale="instagram",
    )

    corpo = client.get(f"/api/campagne/{campagna.id}").json()
    assert corpo["canali_tolti"] == ["instagram"]
    assert [d["esito"] for d in corpo["decisioni"]] == ["canale_tolto"]
    assert corpo["decisioni"][0]["canale"] == "instagram"
    assert corpo["decisioni"][0]["nota"] == "Le foto non sono adatte a Instagram."
    assert corpo["esito_respinta"] is None


def test_dettaglio_operatore_resta_completo(
    client: TestClient, utente_di_prova, db: Session
):
    """L'operatore continua a vedere decisioni e fotografia del profilo."""
    artigiano = utente(db, "artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    campagna.stato = "in_revisione"
    db.flush()
    operatore = utente_di_prova("operatore")
    nota_interna(db, campagna, nota="Da ricontrollare.", utente_id=operatore.id)

    corpo = client.get(f"/api/campagne/{campagna.id}").json()
    assert [d["esito"] for d in corpo["decisioni"]] == ["nota"]
    assert corpo["decisioni"][0]["nota"] == "Da ricontrollare."
    assert corpo["profilo_snapshot"] is not None
    assert corpo["esito_respinta"] is None
