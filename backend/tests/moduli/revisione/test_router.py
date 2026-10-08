"""Test degli endpoint di revisione: Vedi campagna, Approva e Prosegui (T1-42)."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.moduli.campagne.models import DecisioneCampagna, Foto
from app.moduli.contenuti.models import ErroreGenerazione, Post
from app.moduli.revisione.models import Approvazione
from tests.moduli.campagne.fabbrica import (
    campagna_con_piano_da_rivedere,
    campagna_in_revisione,
    campagna_inviata,
    foto,
)
from tests.moduli.contenuti.fabbrica import piano, post_da_approvare

FUTURO = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)
PASSATO = datetime(2020, 1, 5, 12, tzinfo=timezone.utc)


def _dettaglio(client, campagna_id, **params):
    return client.get(f"/api/campagne/{campagna_id}/post", params=params)


def test_vedi_campagna_struttura_completa(db, client, utente_di_prova):
    """Piano, uscite con post dei canali, foto non usate ed errore."""
    campagna = campagna_in_revisione(db)
    piano(db, campagna, strategia="Strategia di prova", debole=False)
    post = post_da_approvare(db, campagna_id=campagna.id, canale="instagram")
    utente_di_prova("operatore")

    risposta = _dettaglio(client, campagna.id)
    assert risposta.status_code == 200
    dati = risposta.json()

    assert dati["campagna"]["id"] == campagna.id
    assert dati["campagna"]["stato"] == "in_revisione"
    assert dati["campagna"]["inizio"] == "2030-01-01"

    assert dati["piano"]["strategia"] == "Strategia di prova"
    assert dati["piano"]["debole"] is False

    assert len(dati["uscite"]) == 1
    uscita = dati["uscite"][0]
    assert uscita["tema"] == "Tema di prova"
    assert uscita["gruppo"]["descrizione"] == "Gruppo di prova"
    assert [p["post_id"] for p in uscita["post"]] == [post.id]

    corrente = uscita["post"][0]["versione_corrente"]
    assert corrente["testo"] == "Testo di prova"
    assert corrente["hashtag"] == ["artigianato"]
    assert len(corrente["foto"]) == 1
    assert corrente["foto"][0]["posizione"] == 1
    assert uscita["post"][0]["riempitivo"] is None
    assert len(uscita["post"][0]["versioni"]) == 1

    # Delle 4 foto del gruppo una è usata dal post: le altre 3 restano fuori.
    non_usate = [
        f["foto_id"] for gruppo in dati["foto_non_usate"] for f in gruppo["foto"]
    ]
    assert len(non_usate) == 3
    assert dati["ultimo_errore"] is None


def test_ca60_ultimo_errore_in_generazione_fallita(db, client, utente_di_prova):
    """In generazione_fallita l'operatore legge tipo, messaggio, tappa e canale."""
    campagna = campagna_inviata(db)
    campagna.stato = "generazione_fallita"
    db.add(
        ErroreGenerazione(
            campagna_id=campagna.id,
            tipo="configurazione",
            messaggio="Chiave AI mancante",
            tappa="piano",
            canale="instagram",
        )
    )
    db.flush()
    utente_di_prova("operatore")

    dati = _dettaglio(client, campagna.id).json()
    assert dati["ultimo_errore"] == {
        "tipo": "configurazione",
        "messaggio": "Chiave AI mancante",
        "tappa": "piano",
        "canale": "instagram",
        "creata_il": dati["ultimo_errore"]["creata_il"],
    }
    assert dati["ultimo_errore"]["creata_il"] is not None


def test_vedi_campagna_inviata_senza_piano(db, client, utente_di_prova):
    """In inviata il piano non c'è ancora: il campo resta nullo."""
    campagna = campagna_inviata(db)
    utente_di_prova("operatore")

    dati = _dettaglio(client, campagna.id).json()
    assert dati["piano"] is None
    assert dati["uscite"] == []
    assert dati["ultimo_errore"] is None


def test_vedi_campagna_foto_non_usata_con_motivo(db, client, utente_di_prova):
    """La foto scartata dall'analisi compare con il suo motivo."""
    campagna = campagna_in_revisione(db)
    post_da_approvare(db, campagna_id=campagna.id)
    esclusa = foto(db, campagna=campagna)
    esclusa.analisi_ai = {"idonea": False, "motivo": "Sfocata"}
    db.flush()
    utente_di_prova("operatore")

    dati = _dettaglio(client, campagna.id).json()
    scartate = {
        f["foto_id"]: f["motivo"]
        for gruppo in dati["foto_non_usate"]
        for f in gruppo["foto"]
    }
    assert scartate[esclusa.id] == "Sfocata"


def test_vedi_campagna_filtra_per_stato(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    da_approvare = post_da_approvare(db, campagna_id=campagna.id)
    scartato = post_da_approvare(
        db, campagna_id=campagna.id, canale="facebook", stato="scartato"
    )
    utente_di_prova("operatore")

    tutti = _dettaglio(client, campagna.id).json()["uscite"]
    solo_scartati = _dettaglio(client, campagna.id, stato="scartato").json()["uscite"]
    ids_tutti = {p["post_id"] for u in tutti for p in u["post"]}
    ids_scartati = {p["post_id"] for u in solo_scartati for p in u["post"]}
    assert ids_tutti == {da_approvare.id, scartato.id}
    assert ids_scartati == {scartato.id}


def test_vedi_campagna_permessi(db, client, utente_di_prova):
    """L'artigiano non entra (403), l'admin sì; campagna assente → 404."""
    campagna = campagna_in_revisione(db)

    utente_di_prova("artigiano")
    assert _dettaglio(client, campagna.id).status_code == 403

    utente_di_prova("admin")
    assert _dettaglio(client, campagna.id).status_code == 200
    assert _dettaglio(client, 99999).status_code == 404


def test_ca21_approva_in_blocco(db, client, utente_di_prova, coda):
    """Tutti i post da_approvare approvati, riga per post, campagna attiva."""
    campagna = campagna_in_revisione(db)
    primo = post_da_approvare(db, campagna_id=campagna.id, canale="instagram")
    secondo = post_da_approvare(db, campagna_id=campagna.id, canale="facebook")
    operatore = utente_di_prova("operatore")

    risposta = client.post(f"/api/campagne/{campagna.id}/approva")
    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "attiva"}

    db.refresh(campagna)
    db.refresh(primo)
    db.refresh(secondo)
    assert campagna.stato == "attiva"
    assert primo.stato == "approvato"
    assert secondo.stato == "approvato"

    righe = db.scalars(
        select(Approvazione).where(
            Approvazione.versione_id.in_(
                [primo.versione_corrente.id, secondo.versione_corrente.id]
            )
        )
    ).all()
    assert len(righe) == 2
    assert {r.utente_id for r in righe} == {operatore.id}
    assert {r.esito for r in righe} == {"approvato"}

    decisione = db.scalar(
        select(DecisioneCampagna).where(DecisioneCampagna.campagna_id == campagna.id)
    )
    assert decisione.esito == "approvata"
    assert decisione.utente_id == operatore.id


def test_ca21_post_passato_diventa_scaduto(db, client, utente_di_prova):
    """Un post con la data già passata non si approva: diventa scaduto (R-14)."""
    campagna = campagna_in_revisione(db)
    vecchio = post_da_approvare(db, campagna_id=campagna.id, data_ora=PASSATO)
    post_da_approvare(db, campagna_id=campagna.id, canale="facebook")
    utente_di_prova("operatore")

    assert client.post(f"/api/campagne/{campagna.id}/approva").status_code == 200

    db.refresh(vecchio)
    assert vecchio.stato == "scaduto"
    # Il post scaduto non ha riga di approvazione.
    assert (
        db.scalar(
            select(Approvazione).where(
                Approvazione.versione_id == vecchio.versione_corrente.id
            )
        )
        is None
    )


def test_ca22_approva_con_da_rivedere_409(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    post_da_approvare(db, campagna_id=campagna.id, da_rivedere=True)
    post_da_approvare(db, campagna_id=campagna.id, canale="facebook")
    utente_di_prova("operatore")

    risposta = client.post(f"/api/campagne/{campagna.id}/approva")
    assert risposta.status_code == 409
    db.refresh(campagna)
    assert campagna.stato == "in_revisione"


def test_ca22_approva_con_intervento_in_corso_409(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    post_da_approvare(
        db,
        campagna_id=campagna.id,
        intervento_in_corso="rigenera_totale",
        intervento_dal=datetime.now(timezone.utc) - timedelta(minutes=2),
    )
    utente_di_prova("operatore")

    assert client.post(f"/api/campagne/{campagna.id}/approva").status_code == 409


def test_ca22_approva_senza_post_da_approvare_409(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    post_da_approvare(db, campagna_id=campagna.id, stato="scartato")
    utente_di_prova("operatore")

    assert client.post(f"/api/campagne/{campagna.id}/approva").status_code == 409


def test_approva_fuori_revisione_409(db, client, utente_di_prova):
    campagna = campagna_inviata(db)
    utente_di_prova("operatore")

    assert client.post(f"/api/campagne/{campagna.id}/approva").status_code == 409


def test_approva_artigiano_403(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    utente_di_prova("artigiano")

    assert client.post(f"/api/campagne/{campagna.id}/approva").status_code == 403


def test_ca49_prosegui_riparte_la_generazione(db, client, utente_di_prova, coda):
    """piano_da_rivedere → in_generazione, decisione e job accodato."""
    campagna = campagna_con_piano_da_rivedere(db)
    post = post_da_approvare(db, campagna_id=campagna.id)
    foto_idonea = db.get(Foto, post.versione_corrente.legami_foto[0].foto_id)
    foto_idonea.analisi_ai = {"idonea": True}
    db.flush()
    operatore = utente_di_prova("operatore")

    risposta = client.post(f"/api/campagne/{campagna.id}/prosegui")
    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "in_generazione"}

    db.refresh(campagna)
    assert campagna.stato == "in_generazione"

    decisione = db.scalar(
        select(DecisioneCampagna).where(DecisioneCampagna.campagna_id == campagna.id)
    )
    assert decisione.esito == "proseguita"
    assert decisione.utente_id == operatore.id

    job = list(coda.jobs.values())
    assert len(job) == 1
    assert job[0]["task_name"] == "genera_campagna"
    assert job[0]["args"] == {"campagna_id": campagna.id}


def test_prosegui_fuori_da_piano_da_rivedere_409(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    utente_di_prova("operatore")

    assert client.post(f"/api/campagne/{campagna.id}/prosegui").status_code == 409


def test_prosegui_senza_post_409(db, client, utente_di_prova):
    """Il piano non ha post: Prosegui non è ammesso."""
    campagna = campagna_con_piano_da_rivedere(db)
    utente_di_prova("operatore")

    assert client.post(f"/api/campagne/{campagna.id}/prosegui").status_code == 409


def test_prosegui_senza_foto_disponibili_409(db, client, utente_di_prova):
    """Post nel piano ma nessuna foto idonea: resta ferma (R-20)."""
    campagna = campagna_con_piano_da_rivedere(db)
    post_da_approvare(db, campagna_id=campagna.id)
    # Le foto del gruppo non hanno analisi: nessuna è idonea.
    utente_di_prova("operatore")

    risposta = client.post(f"/api/campagne/{campagna.id}/prosegui")
    assert risposta.status_code == 409

    db.refresh(campagna)
    assert campagna.stato == "piano_da_rivedere"
