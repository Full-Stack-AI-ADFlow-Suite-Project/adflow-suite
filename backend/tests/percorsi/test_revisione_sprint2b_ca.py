"""T2b-07: API vere, login del seed, worker e notifiche con adattatori finti.

Il percorso usa le stesse fixture della chiusura 1: ora iniettata, PostgreSQL
adflow_test, commit per richiesta/job. Nessuna email o chiamata esterna reale.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image
from sqlalchemy import select

from app import worker
from app.adapters.ai import AIFinto, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.adapters.email import EmailFinto, usa_email
from app.adapters.social import SocialFinto, usa_social
from app.core.coda import INVIA_NOTIFICA, RIGENERA_POST
from app.moduli.contenuti import jobs, service as contenuti
from app.moduli.notifiche import jobs as posta
from app.moduli.notifiche.models import Notifica
from tests.moduli.accesso.fabbrica import utente
from tests.percorsi.test_percorso_sprint1 import (
    ADMIN,
    ARTIGIANO,
    INIZIO,
    OPERATORE,
    UNA_SETTIMANA,
    _bozza,
    _post_per_canale,
    _stato,
    _vedi,
    accessi,
    api,
    entra,
    lavora,
    orologio,
)


@pytest.fixture(autouse=True)
def finti():
    ai, social, archivio, email = (
        AIFinto(),
        SocialFinto(),
        ArchivioFinto(),
        EmailFinto(),
    )
    with usa_ai(ai), usa_social(social), usa_archivio(archivio), usa_email(email):
        yield SimpleNamespace(ai=ai, social=social, archivio=archivio, email=email)


@pytest.fixture(autouse=True)
def ora_della_posta(db, orologio, monkeypatch):
    @contextmanager
    def transazione():
        with db.begin_nested():
            yield db
        db.commit()

    monkeypatch.setattr(posta, "transazione", transazione)
    monkeypatch.setattr(posta, "adesso", orologio)


@pytest.fixture
def altri_job(coda):
    """Consuma gli argomenti accodati dalle API, comprese le miniature."""
    fatti = set()

    def esegui():
        for job_id, job in list(coda.jobs.items()):
            if job_id in fatti:
                continue
            nome, args = job["task_name"], job["args"]
            if nome == RIGENERA_POST:
                for tentativo in range(1, 4):
                    if not jobs.esegui_rigenerazione(**args, esecuzione=tentativo):
                        break
                else:
                    pytest.fail("Rigenerazione ancora da riprovare dopo tre tentativi.")
            elif nome == INVIA_NOTIFICA:
                for tentativo in range(1, 4):
                    if not posta.esegui_invio(
                        args["notifica_id"], args.get("contenuto"), tentativo
                    ):
                        break
                else:
                    pytest.fail("Email ancora da riprovare dopo tre tentativi.")
            else:
                continue
            fatti.add(job_id)

    return esegui


def _pronta(api, entra, lavora):
    entra(ARTIGIANO)
    campagna, foto = _bozza(api, UNA_SETTIMANA, foto_per_gruppo=(2, 2))
    assert api("PUT", f"/foto/{foto[-1]}", json={"da_usare": True}).status_code == 200
    assert api("POST", f"/campagne/{campagna}/invia").status_code == 200
    assert lavora() == [1]
    entra(OPERATORE)
    assert _stato(api, campagna) == "in_revisione"
    return campagna, foto


def _post(api, campagna):
    return [p for u in _vedi(api, campagna)["uscite"] for p in u["post"]]


def _notifiche(db, campagna, tipo=None):
    query = select(Notifica).where(Notifica.campagna_id == campagna)
    if tipo:
        query = query.where(Notifica.tipo == tipo)
    return list(db.scalars(query.order_by(Notifica.id)))


def _ok(api, metodo, percorso, **args):
    risposta = api(metodo, percorso, **args)
    assert risposta.status_code < 400, risposta.text
    return risposta.json()


def test_ca55_generazione_notifica_ogni_operatore_una_sola_volta(
    api, entra, lavora, db, altri_job, finti
):
    secondo = utente(db, "operatore")
    db.commit()
    campagna, _ = _pronta(api, entra, lavora)
    righe = _notifiche(db, campagna, "campagna_pronta")
    assert len(righe) == 3  # due operatori e admin
    assert secondo.id in {n.utente_id for n in righe}
    assert jobs.esegui_generazione(campagna, 1) is False
    assert len(_notifiche(db, campagna, "campagna_pronta")) == 3
    altri_job()
    assert len(finti.email.inviate) == 3
    assert all(n.stato_invio == "inviata" for n in righe)
    altri_job()
    assert len(finti.email.inviate) == 3


def test_ca23_nota_interna_privata_e_ca69_elenco_urgente(
    api, entra, lavora, db, altri_job, finti
):
    campagna, _ = _pronta(api, entra, lavora)
    altri_job()
    prima = len(finti.email.inviate)
    _ok(api, "POST", f"/campagne/{campagna}/nota", json={"nota": "Da controllare"})
    assert _stato(api, campagna) == "in_revisione"
    decisioni = _ok(api, "GET", f"/campagne/{campagna}")["decisioni"]
    assert decisioni[-1]["esito"] == "nota"
    elenco = _ok(api, "GET", "/da-approvare")
    assert elenco[0]["id"] == campagna
    assert elenco[0]["ultima_nota"] == "Da controllare"
    assert elenco[0]["conteggi"]["totale"] == 6
    assert elenco[0]["conteggi"]["da_approvare"] == 6
    assert elenco[0]["entro_quando"] == min(p["data_ora"] for p in _post(api, campagna))
    entra(ARTIGIANO)
    dettaglio = _ok(api, "GET", f"/campagne/{campagna}")
    assert dettaglio["decisioni"] == []
    assert "Da controllare" not in str(dettaglio)
    altri_job()
    assert len(finti.email.inviate) == prima


def test_ca64_modifica_validata_e_ca65_spunta_azzerata(api, entra, lavora, db):
    campagna, _ = _pronta(api, entra, lavora)
    post = _post(api, campagna)[0]
    id_post = post["post_id"]
    vecchia = post["versione_corrente"]
    _ok(api, "POST", f"/post/{id_post}/controllato", json={"valore": True})
    marcato = _post(api, campagna)[0]
    assert marcato["controllato_da"] and marcato["controllato_il"]
    for testo, hashtag in ((vecchia["testo"], vecchia["hashtag"]), ("Costa 10€", [])):
        assert (
            api(
                "POST",
                f"/post/{id_post}/modifica",
                json={"testo": testo, "hashtag": hashtag},
            ).status_code
            == 422
        )
    _ok(
        api,
        "POST",
        f"/post/{id_post}/modifica",
        json={
            "testo": "Un pezzo lavorato a mano nella nostra bottega.",
            "hashtag": ["artigianato"],
        },
    )
    nuovo = _post(api, campagna)[0]
    assert nuovo["versione_corrente"]["tipo_intervento"] == "modifica_operatore"
    assert nuovo["versione_corrente"]["autore_id"] == marcato["controllato_da"]
    assert nuovo["versione_corrente"]["foto"] == vecchia["foto"]
    assert _cicli(db, campagna, id_post) == 0
    assert nuovo["controllato_da"] is None and nuovo["controllato_il"] is None
    assert len(nuovo["versioni"]) == len(post["versioni"]) + 1


def test_ca26_rigenera_e_ca27_proposta_e_ca28_limite(api, entra, lavora, altri_job, db):
    campagna, _ = _pronta(api, entra, lavora)
    primo = _post(api, campagna)[0]
    id_post = primo["post_id"]
    foto = primo["versione_corrente"]["foto"]
    assert (
        api(
            "POST", f"/post/{id_post}/rigenera", json={"modalita": "da_proposta"}
        ).status_code
        == 422
    )
    for ciclo, modalita in enumerate(("totale", "da_proposta", "totale"), start=1):
        _ok(
            api,
            "POST",
            f"/post/{id_post}/rigenera",
            json={
                "modalita": modalita,
                "testo_proposto": "La creazione della nostra bottega."
                if modalita == "da_proposta"
                else None,
            },
        )
        assert api("POST", f"/campagne/{campagna}/approva").status_code == 409
        assert _post(api, campagna)[0]["intervento_in_corso"] is not None
        altri_job()
        nuovo = _post(api, campagna)[0]
        assert _cicli(db, campagna, id_post) == ciclo
        assert nuovo["intervento_in_corso"] is None
        assert nuovo["versione_corrente"]["foto"] == foto
        assert not nuovo["da_rivedere"]
        if modalita == "da_proposta":
            assert (
                nuovo["versione_corrente"]["testo_proposto"]
                == "La creazione della nostra bottega."
            )
    assert (
        api(
            "POST", f"/post/{id_post}/rigenera", json={"modalita": "totale"}
        ).status_code
        == 409
    )
    _ok(
        api,
        "POST",
        f"/post/{id_post}/modifica",
        json={
            "testo": "La modifica a mano resta disponibile dopo tre cicli.",
            "hashtag": [],
        },
    )
    assert _cicli(db, campagna, id_post) == 3


def test_ca66_rigenerazione_fallita_e_intervento_scaduto(
    api, entra, lavora, altri_job, finti, orologio, db
):
    campagna, _ = _pronta(api, entra, lavora)
    prima = _post(api, campagna)[0]
    id_post = prima["post_id"]
    finti.ai.comanda_errore("genera_post", "temporaneo", volte=3)
    _ok(api, "POST", f"/post/{id_post}/rigenera", json={"modalita": "totale"})
    altri_job()
    dopo = _post(api, campagna)[0]
    assert dopo["versioni"] == prima["versioni"]
    assert _cicli(db, campagna, id_post) == 0
    assert dopo["intervento_in_corso"] is None
    _ok(api, "POST", f"/post/{id_post}/rigenera", json={"modalita": "totale"})
    assert api("POST", f"/campagne/{campagna}/approva").status_code == 409
    orologio.ora += timedelta(minutes=11)
    assert api("POST", f"/campagne/{campagna}/approva").status_code == 200


def test_ca53_togli_canale_approva_e_visibilita_artigiano(api, entra, lavora):
    campagna, _ = _pronta(api, entra, lavora)
    _ok(
        api,
        "POST",
        f"/campagne/{campagna}/togli-canale",
        json={"canale": "instagram", "nota": "Account da sistemare"},
    )
    assert (
        api(
            "POST",
            f"/campagne/{campagna}/togli-canale",
            json={"canale": "facebook", "nota": "Ultimo canale"},
        ).status_code
        == 409
    )
    _ok(api, "POST", f"/campagne/{campagna}/approva")
    per_canale = _post_per_canale(_vedi(api, campagna))
    assert {p["stato"] for p in per_canale["instagram"]} == {"scartato"}
    assert {p["stato"] for p in per_canale["facebook"]} == {"approvato"}
    entra(ARTIGIANO)
    dettaglio = _ok(api, "GET", f"/campagne/{campagna}")
    assert dettaglio["canali_tolti"] == ["instagram"]
    assert dettaglio["decisioni"][0]["nota"] == "Account da sistemare"


def test_ca24_respingi_incompleta_e_ca25_email_e_ca31_viste(
    api, entra, lavora, altri_job, finti
):
    campagna, foto = _pronta(api, entra, lavora)
    entra(ARTIGIANO)
    prima = _ok(api, "GET", f"/campagne/{campagna}")
    assert "piano" not in prima and "post" not in prima
    assert api("GET", f"/campagne/{campagna}/post").status_code == 403
    entra(OPERATORE)
    for corpo in (
        {"nota": "Rifare"},
        {"motivo": "foto"},
        {"motivo": "foto", "nota": ""},
    ):
        assert (
            api("POST", f"/campagne/{campagna}/respingi", json=corpo).status_code == 422
        )
    nota = "Rifare le due foto: più luce nel laboratorio."
    _ok(
        api,
        "POST",
        f"/campagne/{campagna}/respingi",
        json={"motivo": "foto", "nota": nota, "foto_segnate": foto[:2]},
    )
    assert _stato(api, campagna) == "respinta"
    assert {p["stato"] for p in _post(api, campagna)} == {"scartato"}
    altri_job()
    email = [m for m in finti.email.inviate if "respinta" in m.oggetto.lower()]
    assert len(email) == 1
    assert nota in email[0].corpo and "foto da rifare" in email[0].corpo
    assert len(email[0].allegati) == 2
    for allegato in email[0].allegati:
        with Image.open(BytesIO(allegato.contenuto)) as immagine:
            assert max(immagine.size) <= 320
    entra(ARTIGIANO)
    dettaglio = _ok(api, "GET", f"/campagne/{campagna}")
    assert dettaglio["esito_respinta"] == {
        "motivo": "foto",
        "nota": nota,
        "foto_segnate": foto[:2],
    }


def test_ca32_sospendi_riattiva_annulla_e_ca29_blocco_interventi(
    api, entra, lavora, orologio, finti
):
    campagna, _ = _pronta(api, entra, lavora)
    _ok(api, "POST", f"/campagne/{campagna}/approva")
    primo = _post(api, campagna)[0]["post_id"]
    for stato in ("attiva", "sospesa"):
        if stato == "sospesa":
            _ok(api, "POST", f"/campagne/{campagna}/sospendi")
        for azione, corpo in (
            ("modifica", {"testo": "Testo nuovo", "hashtag": []}),
            ("rigenera", {"modalita": "totale"}),
            ("controllato", {"valore": True}),
        ):
            assert api("POST", f"/post/{primo}/{azione}", json=corpo).status_code == 409
    post = _post(api, campagna)
    prima_data = min(datetime.fromisoformat(p["data_ora"]) for p in post)
    orologio.ora = prima_data + timedelta(minutes=1)
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    assert finti.social.pubblicazioni == []
    arretrati = [
        p["post_id"]
        for p in post
        if datetime.fromisoformat(p["data_ora"]) <= orologio.ora
    ]
    _ok(
        api,
        "POST",
        f"/campagne/{campagna}/riattiva",
        json={"pubblica_ora": arretrati[:1]},
    )
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    assert len(finti.social.pubblicazioni) == 1
    stati = {p["post_id"]: p["stato"] for p in _post(api, campagna)}
    assert stati[arretrati[0]] == "pubblicato"
    assert all(stati[n] == "annullato" for n in arretrati[1:])
    _ok(api, "POST", f"/campagne/{campagna}/annulla")
    assert _stato(api, campagna) == "annullata"
    assert not any(p["stato"] == "approvato" for p in _post(api, campagna))
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    assert len(finti.social.pubblicazioni) == 1
    assert {
        d["esito"] for d in _ok(api, "GET", f"/campagne/{campagna}")["decisioni"]
    } >= {
        "sospesa",
        "riattivata",
        "annullata",
    }


def test_ca67_riprogramma_post_fallito_e_ca55_notifica(
    api, entra, lavora, orologio, altri_job, finti, db
):
    campagna, _ = _pronta(api, entra, lavora)
    post = _post(api, campagna)[0]
    id_post = post["post_id"]
    _ok(
        api,
        "POST",
        f"/post/{id_post}/modifica",
        json={"testo": "FAIL_DEF Creazione della bottega.", "hashtag": []},
    )
    _ok(api, "POST", f"/campagne/{campagna}/approva")
    orologio.ora = datetime.fromisoformat(post["data_ora"]) + timedelta(seconds=1)
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    righe = _notifiche(db, campagna, "post_fallito")
    assert len(righe) == 2  # operatore e admin
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    assert len(_notifiche(db, campagna, "post_fallito")) == 2
    for data in (
        (orologio.ora - timedelta(days=1)).isoformat(),
        "2030-02-15T12:00:00Z",
    ):
        assert (
            api(
                "POST", f"/post/{id_post}/riprogramma", json={"data_ora": data}
            ).status_code
            == 422
        )
    nuova_data = orologio.ora + timedelta(hours=1)
    _ok(
        api,
        "POST",
        f"/post/{id_post}/riprogramma",
        json={"data_ora": nuova_data.isoformat()},
    )
    assert (
        api(
            "POST",
            f"/post/{id_post}/riprogramma",
            json={"data_ora": nuova_data.isoformat()},
        ).status_code
        == 409
    )
    assert any(
        d["esito"] == "riprogrammato"
        for d in _ok(api, "GET", f"/campagne/{campagna}")["decisioni"]
    )
    assert (
        next(p for p in _post(api, campagna) if p["post_id"] == id_post)["stato"]
        == "approvato"
    )
    altri_job()
    assert all(n.stato_invio == "inviata" for n in righe)


def test_ca30_scadenza_morbida_email_e_tick_idempotente(
    api, entra, lavora, orologio, altri_job, finti, db
):
    campagna, _ = _pronta(api, entra, lavora)
    date_post = sorted(
        {datetime.fromisoformat(p["data_ora"]) for p in _post(api, campagna)}
    )
    orologio.ora = date_post[0] + timedelta(seconds=1)
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    assert _stato(api, campagna) == "in_revisione"
    assert any(p["stato"] == "scaduto" for p in _post(api, campagna))
    orologio.ora = date_post[-2] + timedelta(seconds=1)
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    assert _stato(api, campagna) == "scaduta"
    assert {p["stato"] for p in _post(api, campagna)} == {"scaduto"}
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    assert len(_notifiche(db, campagna, "campagna_scaduta")) == 1
    altri_job()
    assert len([m for m in finti.email.inviate if "scaduta" in m.oggetto.lower()]) == 1


def test_ca68_campagna_ferma_errore_e_riprova_e_ca30_senza_piano(
    api, entra, orologio, db, altri_job, finti
):
    entra(ARTIGIANO)
    campagna, _ = _bozza(api, UNA_SETTIMANA, foto_per_gruppo=(2, 2))
    _ok(api, "POST", f"/campagne/{campagna}/invia")
    orologio.ora += timedelta(minutes=31)
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    entra(OPERATORE)
    vista = _vedi(api, campagna)
    assert vista["campagna"]["stato"] == "generazione_fallita"
    assert vista["ultimo_errore"]["tipo"] == "temporaneo"
    _ok(api, "POST", f"/campagne/{campagna}/riprova")
    assert _stato(api, campagna) == "inviata"
    orologio.ora = datetime(2030, 1, 10, 23, tzinfo=timezone.utc)
    worker.tick_pubblicazione(0)  # mezzanotte di Roma dell'11 gennaio
    entra(OPERATORE)
    assert _stato(api, campagna) == "scaduta"
    assert len(_notifiche(db, campagna, "campagna_scaduta")) == 1
    altri_job()
    assert any("scaduta" in m.oggetto.lower() for m in finti.email.inviate)


def test_ca70_ordine_campagne_e_permessi_del_percorso(api, entra, lavora):
    campagna, foto = _pronta(api, entra, lavora)
    _ok(
        api,
        "POST",
        f"/campagne/{campagna}/respingi",
        json={"motivo": "foto", "nota": "Rifare", "foto_segnate": foto[:2]},
    )
    entra(ARTIGIANO)
    seconda = _ok(
        api,
        "POST",
        "/campagne",
        json={
            "titolo": "Nuova proposta",
            "inizio": (INIZIO + timedelta(days=20)).isoformat(),
            "fine": (UNA_SETTIMANA + timedelta(days=20)).isoformat(),
            "canali": ["facebook", "instagram"],
        },
    )
    assert [c["id"] for c in _ok(api, "GET", "/campagne")] == [seconda["id"], campagna]
    for endpoint, corpo in (
        (f"/campagne/{campagna}/nota", {"nota": "Vietata"}),
        (f"/campagne/{campagna}/respingi", {"motivo": "altro", "nota": "Vietata"}),
        (
            f"/post/{_post_id_operatore(api, entra, campagna)}/modifica",
            {"testo": "Vietato", "hashtag": []},
        ),
    ):
        entra(ARTIGIANO)
        assert api("POST", endpoint, json=corpo).status_code == 403
    assert api("GET", "/da-approvare").status_code == 403
    entra(ADMIN)
    assert api("GET", "/da-approvare").status_code == 200
    assert (
        api(
            "POST", f"/campagne/{seconda['id']}/nota", json={"nota": "Bozza"}
        ).status_code
        == 409
    )
    assert (
        api(
            "POST",
            f"/campagne/{seconda['id']}/respingi",
            json={"motivo": "altro", "nota": "Bozza"},
        ).status_code
        == 409
    )


def _post_id_operatore(api, entra, campagna):
    entra(OPERATORE)
    return _post(api, campagna)[0]["post_id"]


def _cicli(db, campagna, post_id):
    return next(
        p.n_rigenerazioni_testo
        for p in contenuti.post_della_campagna(db, campagna)
        if p.id == post_id
    )


def test_ca31_piano_debole_privato_e_ca55_notifica(
    api, entra, lavora, db, finti, altri_job
):
    entra(ARTIGIANO)
    fine = INIZIO + timedelta(days=27)
    campagna, _ = _bozza(api, fine, foto_per_gruppo=(2, 2))
    _ok(api, "POST", f"/campagne/{campagna}/invia")
    assert lavora() == [1]
    dettaglio = _ok(api, "GET", f"/campagne/{campagna}")
    assert dettaglio["stato"] == "piano_da_rivedere"
    assert "piano" not in dettaglio and "post" not in dettaglio
    assert api("GET", f"/campagne/{campagna}/post").status_code == 403
    assert len(_notifiche(db, campagna, "piano_da_rivedere")) == 2
    altri_job()
    assert len(finti.email.inviate) == 2
    entra(OPERATORE)
    assert _vedi(api, campagna)["piano"] is not None
    _ok(api, "POST", f"/campagne/{campagna}/prosegui")
    assert lavora() == [1]
    assert _stato(api, campagna) == "in_revisione"


def test_ca30_un_post_scaduto_non_blocca_approvazione(api, entra, lavora, orologio):
    campagna, _ = _pronta(api, entra, lavora)
    prima_data = min(
        datetime.fromisoformat(p["data_ora"]) for p in _post(api, campagna)
    )
    orologio.ora = prima_data + timedelta(seconds=1)
    worker.tick_pubblicazione(0)
    entra(OPERATORE)
    _ok(api, "POST", f"/campagne/{campagna}/approva")
    assert _stato(api, campagna) == "attiva"
    assert {p["stato"] for p in _post(api, campagna)} == {"scaduto", "approvato"}
