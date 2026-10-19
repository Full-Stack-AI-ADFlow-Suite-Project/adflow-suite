"""T3-63: la richiesta del consorzio all'artigiano (spec R-46, R-41, CA-86…CA-90)."""
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import select

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.core.errori import DatiNonValidi, NonTrovato
from app.main import app
from app.moduli.accesso.service import utente_corrente
from app.moduli.campagne import service as campagne
from app.moduli.campagne.models import DecisioneCampagna, Foto, GruppoFoto
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_in_bozza,
    campagna_in_revisione,
    foto as fabbrica_foto,
    gruppo as fabbrica_gruppo,
    richiesta,
)
from tests.moduli.contenuti.fabbrica import post_da_approvare


@pytest.fixture(autouse=True)
def archivio_finto(tmp_path: Path):
    with usa_archivio(ArchivioDisco(tmp_path)):
        yield tmp_path


def _immagine(lato: int = 1080) -> bytes:
    uscita = BytesIO()
    Image.new("RGB", (lato, lato), (200, 120, 60)).save(uscita, "PNG")
    return uscita.getvalue()


def _entra(persona):
    app.dependency_overrides[utente_corrente] = lambda: persona


def _scena(db, utente_di_prova):
    """Un artigiano con la sua campagna in revisione (4 foto in un gruppo) e un operatore."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    foto = list(
        db.scalars(
            select(Foto).where(Foto.campagna_id == campagna.id).order_by(Foto.id)
        )
    )
    operatore = utente(db, "operatore")
    return campagna, foto, artigiano, operatore


def _decisioni(db, campagna, esito):
    return list(
        db.scalars(
            select(DecisioneCampagna)
            .where(
                DecisioneCampagna.campagna_id == campagna.id,
                DecisioneCampagna.esito == esito,
            )
            .order_by(DecisioneCampagna.id)
        )
    )


def _carica(client, campagna, foto_id, *, dichiarazione=True, contenuto=None):
    dati = {"foto_id": str(foto_id)}
    if dichiarazione:
        dati["dichiarazione"] = "true"
    return client.post(
        f"/api/campagne/{campagna.id}/richiesta/foto",
        data=dati,
        files={"file": ("nuova.png", BytesIO(contenuto or _immagine()), "image/png")},
    )


# --- CA-86: chiedere all'artigiano ----------------------------------------------


def test_ca86_chiedi_all_artigiano_con_domanda_e_due_foto(db, client, utente_di_prova):
    campagna, foto, _, operatore = _scena(db, utente_di_prova)
    _entra(operatore)

    risposta = client.post(
        f"/api/campagne/{campagna.id}/richiesta",
        json={
            "domanda": "  Puoi mandarne una senza persone?  ",
            "foto": [foto[0].id, foto[1].id],
        },
    )
    assert risposta.status_code == 201
    corpo = risposta.json()
    assert corpo["stato"] == "aperta"
    assert corpo["domanda"] == "Puoi mandarne una senza persone?"
    assert corpo["foto"] == [
        {"foto_id": foto[0].id, "gruppo_id": foto[0].gruppo_id, "nuova_foto_id": None},
        {"foto_id": foto[1].id, "gruppo_id": foto[1].gruppo_id, "nuova_foto_id": None},
    ]
    assert corpo["risposta"] is None

    db.refresh(campagna)
    assert campagna.stato == "in_revisione"
    [decisione] = _decisioni(db, campagna, "integrazione")
    assert decisione.utente_id == operatore.id
    assert decisione.nota == "Puoi mandarne una senza persone?"
    assert decisione.foto_segnate == [foto[0].id, foto[1].id]
    dettaglio = client.get(f"/api/campagne/{campagna.id}").json()
    assert dettaglio["richiesta"]["stato"] == "aperta"


def test_ca86_senza_domanda_422(db, client, utente_di_prova):
    campagna, foto, _, operatore = _scena(db, utente_di_prova)
    _entra(operatore)
    for domanda in ("", "   "):
        assert (
            client.post(
                f"/api/campagne/{campagna.id}/richiesta",
                json={"domanda": domanda, "foto": [foto[0].id]},
            ).status_code
            == 422
        )
    assert _decisioni(db, campagna, "integrazione") == []


def test_ca86_quattro_foto_422(db, client, utente_di_prova):
    campagna, foto, _, operatore = _scena(db, utente_di_prova)
    _entra(operatore)
    assert (
        client.post(
            f"/api/campagne/{campagna.id}/richiesta",
            json={"domanda": "Quattro?", "foto": [f.id for f in foto]},
        ).status_code
        == 422
    )
    assert _decisioni(db, campagna, "integrazione") == []


def test_ca86_foto_di_un_altra_campagna_o_immagine_ai_422(db, client, utente_di_prova):
    campagna, foto, _, operatore = _scena(db, utente_di_prova)
    altra = campagna_in_revisione(db)
    estranea = db.scalars(select(Foto).where(Foto.campagna_id == altra.id)).first()
    immagine_ai = fabbrica_foto(
        db,
        gruppo=fabbrica_gruppo(db, campagna, origine="create_ai"),
        origine="creata_ai",
    )
    _entra(operatore)
    for sbagliata in (estranea.id, immagine_ai.id, 99999):
        assert (
            client.post(
                f"/api/campagne/{campagna.id}/richiesta",
                json={"domanda": "Questa?", "foto": [foto[0].id, sbagliata]},
            ).status_code
            == 422
        )
    assert _decisioni(db, campagna, "integrazione") == []


def test_ca86_campagna_non_in_revisione_409(db, client, utente_di_prova):
    artigiano = utente_di_prova("artigiano")
    attiva = campagna_attiva(db, profilo_id=profilo(db, utente_id=artigiano.id).id)
    _entra(utente(db, "operatore"))
    assert (
        client.post(
            f"/api/campagne/{attiva.id}/richiesta", json={"domanda": "Ciao", "foto": []}
        ).status_code
        == 409
    )


def test_ca86_artigiano_403(db, client, utente_di_prova):
    campagna, _, artigiano, _ = _scena(db, utente_di_prova)
    _entra(artigiano)
    assert (
        client.post(
            f"/api/campagne/{campagna.id}/richiesta",
            json={"domanda": "Ciao", "foto": []},
        ).status_code
        == 403
    )


# --- CA-87: caricare la foto nuova -------------------------------------------------


def test_ca87_carica_la_foto_nuova_con_la_dichiarazione(
    db, client, utente_di_prova, archivio_finto
):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    richiesta(db, campagna, [foto[0]], operatore=operatore)
    _entra(artigiano)

    risposta = _carica(client, campagna, foto[0].id)
    assert risposta.status_code == 201
    nuova = risposta.json()
    assert nuova["gruppo_id"] == foto[0].gruppo_id
    assert nuova["origine"] == "caricata"
    assert nuova["campagna_id"] == campagna.id
    assert (archivio_finto / nuova["file"]).is_file()

    registrata = db.get(Foto, nuova["id"])
    assert registrata.analisi_ai is None
    [decisione] = _decisioni(db, campagna, "integrazione_foto")
    assert decisione.utente_id == artigiano.id
    assert decisione.foto_segnate == [foto[0].id, nuova["id"]]

    dettaglio = client.get(f"/api/campagne/{campagna.id}").json()["richiesta"]
    assert dettaglio["foto"][0]["nuova_foto_id"] == nuova["id"]
    assert dettaglio["stato"] == "aperta"


def test_ca87_senza_dichiarazione_422(db, client, utente_di_prova):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    richiesta(db, campagna, [foto[0]], operatore=operatore)
    _entra(artigiano)
    assert _carica(client, campagna, foto[0].id, dichiarazione=False).status_code == 422
    assert _decisioni(db, campagna, "integrazione_foto") == []


def test_ca87_foto_non_segnata_422(db, client, utente_di_prova):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    richiesta(db, campagna, [foto[0]], operatore=operatore)
    _entra(artigiano)
    assert _carica(client, campagna, foto[1].id).status_code == 422


def test_ca87_seconda_foto_per_la_stessa_409(db, client, utente_di_prova):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    richiesta(db, campagna, [foto[0]], operatore=operatore)
    _entra(artigiano)
    assert _carica(client, campagna, foto[0].id).status_code == 201
    assert _carica(client, campagna, foto[0].id).status_code == 409
    assert len(_decisioni(db, campagna, "integrazione_foto")) == 1


def test_ca87_file_non_valido_422(db, client, utente_di_prova, archivio_finto):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    richiesta(db, campagna, [foto[0]], operatore=operatore)
    _entra(artigiano)
    non_immagine = _carica(client, campagna, foto[0].id, contenuto=b"testo")
    piccola = _carica(client, campagna, foto[0].id, contenuto=_immagine(600))
    assert (non_immagine.status_code, piccola.status_code) == (422, 422)
    assert _decisioni(db, campagna, "integrazione_foto") == []
    assert list(archivio_finto.iterdir()) == []


def test_ca87_senza_richiesta_aperta_409(db, client, utente_di_prova):
    campagna, foto, artigiano, _ = _scena(db, utente_di_prova)
    _entra(artigiano)
    assert _carica(client, campagna, foto[0].id).status_code == 409


def test_ca87_gruppo_pieno_422(db, client, utente_di_prova):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    gruppo = db.get(GruppoFoto, foto[0].gruppo_id)
    for _ in range(16):
        fabbrica_foto(db, gruppo=gruppo)
    richiesta(db, campagna, [foto[0]], operatore=operatore)
    _entra(artigiano)
    assert _carica(client, campagna, foto[0].id).status_code == 422


def test_ca87_artigiano_di_un_altra_bottega_404(db, client, utente_di_prova):
    campagna, foto, _, operatore = _scena(db, utente_di_prova)
    richiesta(db, campagna, [foto[0]], operatore=operatore)
    estraneo = utente_di_prova("artigiano")
    profilo(db, utente_id=estraneo.id)
    assert _carica(client, campagna, foto[0].id).status_code == 404
    assert (
        client.post(
            f"/api/campagne/{campagna.id}/richiesta/invia", json={"risposta": "Ciao"}
        ).status_code
        == 404
    )


# --- CA-88: inviare la risposta ----------------------------------------------------


def test_ca88_invia_la_risposta(db, client, utente_di_prova):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    richiesta(db, campagna, [foto[0]], operatore=operatore)
    _entra(artigiano)
    nuova = _carica(client, campagna, foto[0].id).json()

    risposta = client.post(
        f"/api/campagne/{campagna.id}/richiesta/invia",
        json={"risposta": "  Ecco la foto senza persone  "},
    )
    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["stato"] == "inviata"
    assert corpo["risposta"] == "Ecco la foto senza persone"
    assert corpo["inviata_il"] is not None
    assert corpo["foto"][0]["nuova_foto_id"] == nuova["id"]

    [decisione] = _decisioni(db, campagna, "integrazione_risposta")
    assert decisione.utente_id == artigiano.id
    assert decisione.nota == "Ecco la foto senza persone"
    assert decisione.foto_segnate == [nuova["id"]]
    # Dopo l'invio la richiesta non è più aperta: niente altre foto né un secondo invio.
    assert (
        client.post(f"/api/campagne/{campagna.id}/richiesta/invia").status_code == 409
    )
    assert _carica(client, campagna, foto[0].id).status_code == 409
    _entra(operatore)
    [riga] = [
        r for r in client.get("/api/da-approvare").json() if r["id"] == campagna.id
    ]
    assert riga["richiesta"] == "inviata"


def test_ca88_mancano_foto_409(db, client, utente_di_prova):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    richiesta(db, campagna, [foto[0], foto[1]], operatore=operatore)
    _entra(artigiano)
    assert _carica(client, campagna, foto[0].id).status_code == 201
    risposta = client.post(
        f"/api/campagne/{campagna.id}/richiesta/invia", json={"risposta": "Una sola"}
    )
    assert risposta.status_code == 409
    assert "Mancano 1 foto" in risposta.json()["detail"]
    assert _decisioni(db, campagna, "integrazione_risposta") == []


def test_ca88_senza_foto_e_senza_testo_422(db, client, utente_di_prova):
    campagna, _, artigiano, operatore = _scena(db, utente_di_prova)
    richiesta(db, campagna, [], domanda="Il prezzo è corretto?", operatore=operatore)
    _entra(artigiano)
    for corpo in ({}, {"risposta": "   "}):
        assert (
            client.post(
                f"/api/campagne/{campagna.id}/richiesta/invia", json=corpo
            ).status_code
            == 422
        )
    assert (
        client.post(f"/api/campagne/{campagna.id}/richiesta/invia").status_code == 422
    )
    assert (
        client.post(
            f"/api/campagne/{campagna.id}/richiesta/invia",
            json={"risposta": "Sì, è corretto"},
        ).status_code
        == 200
    )


def test_ca88_da_approvare_segna_la_richiesta(db, client, utente_di_prova):
    senza = campagna_in_revisione(db)
    aperta = campagna_in_revisione(db)
    operatore = utente(db, "operatore")
    richiesta(db, aperta, [], domanda="Domanda", operatore=operatore)
    inviata = campagna_in_revisione(db)
    richiesta(db, inviata, [], domanda="Altra", operatore=operatore)
    db.add(
        DecisioneCampagna(
            campagna_id=inviata.id,
            utente_id=utente(db, "artigiano").id,
            esito="integrazione_risposta",
            nota="Fatto",
            foto_segnate=[],
        )
    )
    db.flush()
    _entra(operatore)
    righe = {r["id"]: r["richiesta"] for r in client.get("/api/da-approvare").json()}
    assert righe == {senza.id: None, aperta.id: "aperta", inviata.id: "inviata"}


# --- CA-89: approvare o respingere con la richiesta, decaduta -------------------------


def test_ca89_approva_e_respingi_ammessi_con_la_richiesta_aperta(
    db, client, utente_di_prova
):
    approvata, foto_a, _, operatore = _scena(db, utente_di_prova)
    post_da_approvare(db, campagna_id=approvata.id)
    richiesta(db, approvata, [foto_a[0]], operatore=operatore)
    respinta = campagna_in_revisione(db)
    post_da_approvare(db, campagna_id=respinta.id)
    richiesta(db, respinta, [], operatore=operatore)
    _entra(operatore)

    assert client.post(f"/api/campagne/{approvata.id}/approva").status_code == 200
    assert (
        client.post(
            f"/api/campagne/{respinta.id}/respingi",
            json={"motivo": "altro", "nota": "Non va", "foto_segnate": []},
        ).status_code
        == 200
    )


def test_ca89_dopo_l_approvazione_caricare_o_inviare_409(db, client, utente_di_prova):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    post_da_approvare(db, campagna_id=campagna.id)
    richiesta(db, campagna, [foto[0]], operatore=operatore)
    _entra(operatore)
    assert client.post(f"/api/campagne/{campagna.id}/approva").status_code == 200

    _entra(artigiano)
    assert _carica(client, campagna, foto[0].id).status_code == 409
    assert (
        client.post(
            f"/api/campagne/{campagna.id}/richiesta/invia", json={"risposta": "Tardi"}
        ).status_code
        == 409
    )
    stato = client.get(f"/api/campagne/{campagna.id}").json()["richiesta"]["stato"]
    assert stato == "decaduta"


def test_ca89_una_richiesta_nuova_sostituisce_quella_aperta(
    db, client, utente_di_prova
):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    richiesta(db, campagna, [foto[0]], domanda="Prima", operatore=operatore)
    _entra(artigiano)
    assert _carica(client, campagna, foto[0].id).status_code == 201

    _entra(operatore)
    nuova = client.post(
        f"/api/campagne/{campagna.id}/richiesta",
        json={"domanda": "Seconda", "foto": [foto[1].id]},
    )
    assert nuova.status_code == 201
    corpo = nuova.json()
    assert corpo["domanda"] == "Seconda"
    assert [f["foto_id"] for f in corpo["foto"]] == [foto[1].id]
    assert corpo["foto"][0]["nuova_foto_id"] is None
    assert len(_decisioni(db, campagna, "integrazione")) == 2


# --- CA-90: l'artigiano apre la campagna con la richiesta ------------------------------


def test_ca90_l_artigiano_vede_la_richiesta_e_nessun_post(db, client, utente_di_prova):
    campagna, foto, artigiano, operatore = _scena(db, utente_di_prova)
    post_da_approvare(db, campagna_id=campagna.id)
    richiesta(
        db, campagna, [foto[0]], domanda="Una foto senza persone?", operatore=operatore
    )
    _entra(artigiano)

    dettaglio = client.get(f"/api/campagne/{campagna.id}")
    assert dettaglio.status_code == 200
    corpo = dettaglio.json()
    assert corpo["richiesta"]["domanda"] == "Una foto senza persone?"
    assert corpo["richiesta"]["foto"][0]["foto_id"] == foto[0].id
    assert "post" not in corpo and "piano" not in corpo
    # Le decisioni sono interne: l'artigiano legge la richiesta, non le decisioni.
    assert corpo["decisioni"] == []


def test_ca90_la_campagna_con_la_richiesta_si_apre_per_prima(
    db, client, utente_di_prova
):
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    bozza = campagna_in_bozza(db, profilo_id=bottega.id)
    in_corso = campagna_attiva(db, profilo_id=bottega.id)
    con_richiesta = campagna_in_revisione(db, profilo_id=bottega.id)
    senza_richiesta = campagna_in_revisione(db, profilo_id=bottega.id)
    richiesta(db, con_richiesta, [])

    elenco = client.get("/api/campagne").json()
    assert [c["id"] for c in elenco][:2] == [con_richiesta.id, bozza.id]
    per_id = {c["id"]: c["richiesta"] for c in elenco}
    assert per_id[con_richiesta.id] == "aperta"
    assert per_id[senza_richiesta.id] is None
    assert per_id[in_corso.id] is None


def test_richiesta_di_senza_richieste_e_campagna_che_non_c_e(db):
    assert campagne.richiesta_di(db, campagna_in_revisione(db).id) is None
    with pytest.raises(NonTrovato):
        campagne.richiesta_di(db, 99999)


def test_apri_richiesta_toglie_gli_id_ripetuti(db):
    campagna = campagna_in_revisione(db)
    foto = db.scalars(select(Foto).where(Foto.campagna_id == campagna.id)).first()
    operatore = utente(db, "operatore")
    nuova = campagne.apri_richiesta(
        db, campagna.id, operatore.id, "Ciao", [foto.id, foto.id, foto.id]
    )
    assert [f.foto_id for f in nuova.foto] == [foto.id]
    with pytest.raises(DatiNonValidi):
        campagne.apri_richiesta(db, campagna.id, operatore.id, "Ciao", [1, 2, 3, 4])
