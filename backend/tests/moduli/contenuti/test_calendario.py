"""Calendario della campagna: permessi, stati, versioni, foto e giorni Europe/Rome (spec R-45, CA-56)."""
from datetime import date, datetime, timezone

import pytest
from app.moduli.contenuti.models import VersionePost, VersionePostFoto
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva, foto, gruppo_di_archivio
from tests.moduli.contenuti.fabbrica import piano, post_da_approvare, post_approvato
from app.moduli.campagne import service as campagne
from tests.moduli.accesso.fabbrica import utente, PASSWORD_DI_PROVA


def prepara(db, utente_di_prova, ruolo="artigiano", stato="attiva"):
    persona = utente_di_prova(ruolo)
    bottega = profilo(db, utente_id=persona.id) if ruolo == "artigiano" else profilo(db)
    campagna = campagna_attiva(db, profilo_id=bottega.id)
    campagna.stato = stato
    db.flush()
    piano(db, campagna, strategia="Strategia approvata della bottega")
    return persona, bottega, campagna


def post_in(db, campagna, stato, data_ora=None):
    altri = {"data_ora": data_ora} if data_ora else {}
    return post_da_approvare(db, campagna_id=campagna.id, stato=stato, **altri)


def test_ca56_soli_stati_visibili_versione_corrente_e_numero_scaduti(
    db, client, utente_di_prova
):
    _, _, campagna = prepara(db, utente_di_prova)
    visibili = [
        post_in(db, campagna, s)
        for s in ("approvato", "pubblicato", "fallito", "annullato")
    ]
    for stato in ("da_approvare", "scartato", "scaduto", "scaduto"):
        post_in(db, campagna, stato)
    post = visibili[0]
    legame = post.versione_corrente.legami_foto[0]
    nuova = VersionePost(
        post_id=post.id,
        numero=2,
        testo="Testo corrente pubblico",
        hashtag=["corrente"],
        tipo_intervento="modifica_operatore",
        nota="Nota privata da non esporre",
    )
    db.add(nuova)
    db.flush()
    db.add(VersionePostFoto(versione_id=nuova.id, foto_id=legame.foto_id, posizione=1))
    db.flush()
    risposta = client.get(f"/api/campagne/{campagna.id}/calendario")
    assert risposta.status_code == 200
    result = risposta.json()
    assert result["strategia"] == "Strategia approvata della bottega"
    assert result["n_post_scaduti"] == 2
    posts = [p for g in result["giorni"] for p in g["post"]]
    assert [p["id"] for p in posts] == [p.id for p in visibili]
    assert {p["stato"] for p in posts} == {
        "approvato",
        "pubblicato",
        "fallito",
        "annullato",
    }
    corrente = next(p for p in posts if p["id"] == post.id)
    assert corrente["testo"] == "Testo corrente pubblico" and corrente["hashtag"] == [
        "corrente"
    ]
    assert corrente["foto"][0]["url"] == f"/api/foto/{legame.foto_id}/file"
    assert "Nota privata" not in risposta.text
    assert "versioni" not in risposta.text and "profilo_snapshot" not in risposta.text
    assert risposta.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("ruolo", ["artigiano", "operatore", "admin"])
@pytest.mark.parametrize("stato", ["attiva", "sospesa", "conclusa", "annullata"])
def test_ca56_calendario_dopo_approvazione_per_ruoli_ammessi(
    db, client, utente_di_prova, ruolo, stato
):
    _, _, campagna = prepara(db, utente_di_prova, ruolo, stato)
    post_approvato(db, campagna_id=campagna.id)
    assert client.get(f"/api/campagne/{campagna.id}/calendario").status_code == 200


@pytest.mark.parametrize(
    "stato",
    [
        "bozza",
        "inviata",
        "in_generazione",
        "in_revisione",
        "piano_da_rivedere",
        "generazione_fallita",
        "respinta",
        "scaduta",
    ],
)
def test_ca56_prima_approvazione_409(db, client, utente_di_prova, stato):
    _, _, campagna = prepara(db, utente_di_prova, stato=stato)
    assert client.get(f"/api/campagne/{campagna.id}/calendario").status_code == 409


@pytest.mark.parametrize("stato", ["attiva", "bozza"])
def test_ca56_campagna_altrui_404_prima_dello_stato(db, client, utente_di_prova, stato):
    utente_di_prova("artigiano")
    altra = campagna_attiva(db)
    altra.stato = stato
    db.flush()
    risposta = client.get(f"/api/campagne/{altra.id}/calendario")
    assert risposta.status_code == 404 and risposta.json() == {
        "detail": "Campagna non trovata."
    }


def test_ca56_anonimo_e_campagna_assente(client, utente_di_prova):
    assert client.get("/api/campagne/-1/calendario").status_code == 401
    utente_di_prova("operatore")
    assert client.get("/api/campagne/-1/calendario").status_code == 404


def test_ca56_giorni_e_ora_roma_con_passaggio_ora_legale(db, client, utente_di_prova):
    _, _, campagna = prepara(db, utente_di_prova)
    campagna.inizio = date(2030, 3, 30)
    campagna.fine = date(2030, 4, 2)
    # Il 31 marzo 2030 è l'ultima domenica del mese: alle 01 UTC scatta l'ora legale.
    istanti = [
        datetime(2030, 3, 31, 1, 30, tzinfo=timezone.utc),
        datetime(2030, 3, 30, 23, 30, tzinfo=timezone.utc),
        datetime(2030, 3, 31, 22, 30, tzinfo=timezone.utc),
    ]
    posts = [post_in(db, campagna, "approvato", t) for t in istanti]
    risultato = client.get(f"/api/campagne/{campagna.id}/calendario").json()
    assert [g["data"] for g in risultato["giorni"]] == ["2030-03-31", "2030-04-01"]
    assert [p["id"] for p in risultato["giorni"][0]["post"]] == [
        posts[1].id,
        posts[0].id,
    ]
    assert [p["ora"] for p in risultato["giorni"][0]["post"]] == ["00:30", "03:30"]


def test_ca56_note_canali_tolti_senza_note_interne(db, client, utente_di_prova):
    persona, _, campagna = prepara(db, utente_di_prova)
    campagna.canali_tolti = ["facebook"]
    campagne.registra_decisione(
        db,
        campagna,
        persona.id,
        "canale_tolto",
        None,
        "Nota pubblica",
        [],
        canale="facebook",
    )
    campagne.registra_decisione(
        db, campagna, persona.id, "nota", None, "Nota segreta", []
    )
    risposta = client.get(f"/api/campagne/{campagna.id}/calendario")
    assert risposta.status_code == 200
    assert risposta.json()["canali_tolti"] == [
        {"canale": "facebook", "nota": "Nota pubblica"}
    ]
    assert "Nota segreta" not in risposta.text


def test_ca56_foto_archivio_ammessa_e_metadati_senza_nome_file(
    db, client, utente_di_prova
):
    _, bottega, campagna = prepara(db, utente_di_prova)
    post = post_approvato(db, campagna_id=campagna.id)
    gruppo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)
    archivio = foto(db, gruppo=gruppo, file="nome-file-privato.jpg")
    legame = post.versione_corrente.legami_foto[0]
    legame.foto_id = archivio.id
    db.flush()
    risposta = client.get(f"/api/campagne/{campagna.id}/calendario")
    assert risposta.status_code == 200
    p = risposta.json()["giorni"][0]["post"][0]
    assert p["foto"][0]["id"] == archivio.id
    assert "nome-file-privato" not in risposta.text


def test_ca56_foto_di_altro_profilo_non_esposta(db, client, utente_di_prova):
    _, _, campagna = prepara(db, utente_di_prova)
    post = post_approvato(db, campagna_id=campagna.id)
    estranea = foto(db)
    post.versione_corrente.legami_foto[0].foto_id = estranea.id
    db.flush()
    assert client.get(f"/api/campagne/{campagna.id}/calendario").status_code == 404


def test_ca56_ultima_strategia_e_calendario_vuoto(db, client, utente_di_prova):
    _, _, campagna = prepara(db, utente_di_prova)
    piano(db, campagna, numero=2, strategia="Strategia più recente")
    risultato = client.get(f"/api/campagne/{campagna.id}/calendario").json()
    assert risultato["strategia"] == "Strategia più recente"
    assert risultato["giorni"] == [] and risultato["n_post_scaduti"] == 0


@pytest.mark.parametrize("ruolo", ["artigiano", "operatore", "admin"])
def test_ca56_calendario_con_cookie_reale(db, client, ruolo):
    persona = utente(db, ruolo)
    bottega = profilo(db, utente_id=persona.id) if ruolo == "artigiano" else profilo(db)
    campagna = campagna_attiva(db, profilo_id=bottega.id)
    piano(db, campagna)
    post = post_approvato(db, campagna_id=campagna.id)
    login = client.post(
        "/api/auth/login", json={"email": persona.email, "password": PASSWORD_DI_PROVA}
    )
    assert login.status_code == 200
    risposta = client.get(f"/api/campagne/{campagna.id}/calendario")
    assert risposta.status_code == 200
    assert risposta.json()["giorni"][0]["post"][0]["id"] == post.id
