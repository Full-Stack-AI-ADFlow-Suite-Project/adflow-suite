"""Invio e riprova T1-24: API, minimi, isolamento e conservazione delle tappe."""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone

import pytest

from app.core import coda as modulo_coda
from app.core.orologio import adesso
from app.main import app
from app.moduli.campagne import service
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_in_bozza,
    campagna_inviata,
    foto,
    gruppo,
)

ORA = datetime(2029, 12, 20, 12, tzinfo=timezone.utc)


@pytest.fixture
def bozza(db, client, utente_di_prova):
    u = utente_di_prova("artigiano")
    p = profilo(db, utente_id=u.id, orari={"lunedi": ["09:00", "18:00"]})
    c = campagna_in_bozza(db, profilo_id=p.id)
    g = gruppo(db, c)
    for _ in range(4):
        foto(db, gruppo=g)
    app.dependency_overrides[adesso] = lambda: ORA
    return u, p, c, g


def invia(client, c):
    return client.post(f"/api/campagne/{c.id}/invia")


def test_ca15_invio_salva_snapshot_e_accoda(db, client, bozza, coda):
    _, p, c, _ = bozza
    risposta = invia(client, c)
    assert risposta.status_code == 200
    assert risposta.json()["stato"] == "inviata"
    assert risposta.json()["profilo_snapshot"] is None  # visibile solo all'operatore
    db.refresh(c)
    assert (c.frequenza, c.obiettivo, c.inviata_il) == (p.frequenza, p.obiettivo, ORA)
    assert c.profilo_snapshot["nome"] == p.nome
    assert c.profilo_snapshot["orari"] == p.orari
    assert "aggiornato_il" not in c.profilo_snapshot
    job = next(iter(coda.jobs.values()))
    assert job["task_name"] == modulo_coda.GENERA_CAMPAGNA
    assert job["args"] == {"campagna_id": c.id}
    p.orari["lunedi"].append("20:00")
    p.nome = "Nuovo nome"
    assert c.profilo_snapshot["nome"] != p.nome
    assert c.profilo_snapshot["orari"]["lunedi"] == ["09:00", "18:00"]
    assert invia(client, c).status_code == 409
    assert len(coda.jobs) == 1


@pytest.mark.parametrize("giorni", [-1, 0, 1, 2])
def test_ca09_bozza_ferma_ricontrolla_inizio(db, client, bozza, coda, giorni):
    _, _, c, _ = bozza
    c.inizio = ORA.date() + timedelta(days=giorni)
    c.fine = c.inizio + timedelta(days=6)
    db.flush()
    assert invia(client, c).status_code == 422
    assert c.stato == "bozza" and c.profilo_snapshot is None
    assert not coda.jobs


def test_ca09_calendario_italiano(client, bozza, db, coda):
    _, _, c, _ = bozza
    app.dependency_overrides[adesso] = lambda: datetime(
        2029, 12, 20, 23, 30, tzinfo=timezone.utc
    )
    c.inizio = date(2029, 12, 23)  # Roma è già il 21: anticipo di soli due giorni
    c.fine = c.inizio + timedelta(days=6)
    db.flush()
    assert invia(client, c).status_code == 422
    assert not coda.jobs


@pytest.mark.parametrize(
    "durata,esito", [(0, 422), (6, 422), (7, 200), (92, 200), (93, 422)]
)
def test_durata_inclusiva_e_anticipo_esatto(db, client, bozza, durata, esito):
    _, _, c, _ = bozza
    c.inizio = ORA.date() + timedelta(days=3)
    c.fine = c.inizio + timedelta(days=durata - 1)
    db.flush()
    assert invia(client, c).status_code == esito


@pytest.mark.parametrize("descrizione", [None, "", " \n\t"])
def test_ca14_descrizione_obbligatoria(db, client, bozza, coda, descrizione):
    _, _, c, g = bozza
    g.descrizione = descrizione
    db.flush()
    assert invia(client, c).status_code == 422
    assert c.stato == "bozza" and c.inviata_il is None
    assert not coda.jobs


@pytest.mark.parametrize("numero", [0, 3, 21])
def test_ca14_minimi_e_limite_per_gruppo(db, client, bozza, coda, numero):
    _, _, c, g = bozza
    for f in list(g.foto):
        db.delete(f)
    db.flush()
    db.expire(g, ["foto"])
    for _ in range(numero):
        foto(db, gruppo=g)
    db.expire(g, ["foto"])
    assert invia(client, c).status_code == 422
    assert not coda.jobs


def test_ca14_quattro_foto_in_due_gruppi(db, client, bozza):
    _, _, c, primo = bozza
    for f in list(primo.foto)[2:]:
        db.delete(f)
    db.flush()
    db.expire(primo, ["foto"])
    secondo = gruppo(db, c)
    for _ in range(2):
        foto(db, gruppo=secondo)
    assert invia(client, c).status_code == 200


@pytest.mark.parametrize(
    "numero,esito", [(None, 422), (0, 422), (1, 200), (20, 200), (21, 422)]
)
def test_gruppo_create_ai_controllato(db, client, bozza, numero, esito):
    _, _, c, _ = bozza
    gruppo(db, c, origine="create_ai", n_immagini=numero)
    assert invia(client, c).status_code == esito


def test_ca14_create_ai_non_conta_come_foto(db, client, bozza, coda):
    _, _, c, g = bozza
    db.delete(g.foto[0])
    db.flush()
    db.expire(g, ["foto"])
    gruppo(db, c, origine="create_ai", n_immagini=20)
    assert invia(client, c).status_code == 422
    assert not coda.jobs


@pytest.mark.parametrize(
    "data,esito",
    [
        (date(2029, 12, 31), 422),
        (date(2030, 1, 1), 200),
        (date(2030, 1, 31), 200),
        (date(2030, 2, 1), 422),
    ],
)
def test_data_gruppo_ricontrollata(db, client, bozza, data, esito):
    _, _, c, g = bozza
    g.da_usare_il = data
    db.flush()
    assert invia(client, c).status_code == esito


def test_ca48_canale_scollegato_all_invio(db, client, bozza, coda, monkeypatch):
    _, _, c, _ = bozza
    monkeypatch.setattr(service.artigiani_service, "canali_collegati", lambda *args: [])
    assert invia(client, c).status_code == 409
    assert c.stato == "bozza" and c.profilo_snapshot is None
    assert not coda.jobs


def test_nessun_canale(db, client, bozza, coda):
    _, _, c, _ = bozza
    c.canali = []
    db.flush()
    assert invia(client, c).status_code == 422
    assert not coda.jobs


@pytest.mark.parametrize("frequenza", [None, "f1_2", "f3_4", "decidete_voi"])
def test_frequenza_copiata_senza_ricalcolo(db, client, bozza, frequenza):
    _, p, c, _ = bozza
    p.frequenza = frequenza
    db.flush()
    assert invia(client, c).status_code == 200
    assert c.frequenza == frequenza


def test_profilo_mancante(client, bozza, coda, monkeypatch):
    _, _, c, _ = bozza
    monkeypatch.setattr(service.artigiani_service, "profilo_di", lambda *args: None)
    assert invia(client, c).status_code == 409
    assert not coda.jobs


@pytest.mark.parametrize("ruolo", ["operatore", "admin"])
def test_invio_riservato_artigiano(client, bozza, coda, utente_di_prova, ruolo):
    _, _, c, _ = bozza
    utente_di_prova(ruolo)
    assert invia(client, c).status_code == 403
    assert not coda.jobs


def test_ca04_invio_altrui_e_inesistente(client, bozza, db, coda, utente_di_prova):
    _, _, c, _ = bozza
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id)
    assert invia(client, c).status_code == 404
    assert client.post("/api/campagne/999999/invia").status_code == 404
    assert not coda.jobs


@pytest.mark.parametrize("ruolo", ["operatore", "admin"])
def test_ca19_ca50_riprova_conserva_snapshot_e_analisi(
    db, client, coda, utente_di_prova, ruolo
):
    c = campagna_inviata(db)
    c.stato = "generazione_fallita"
    db.flush()
    fotografia = deepcopy(c.profilo_snapshot)
    data_invio = c.inviata_il
    f = service.foto_della_campagna(db, c.id)[0]
    f.analisi_ai = {"idonea": True, "punteggio": 80}
    p = service.artigiani_service.profilo(db, c.profilo_id)
    p.nome = "Profilo modificato"
    p.frequenza = "f3_4"
    db.flush()
    utente_di_prova(ruolo)
    app.dependency_overrides[adesso] = lambda: datetime(
        2030, 1, 15, tzinfo=timezone.utc
    )
    risposta = client.post(f"/api/campagne/{c.id}/riprova")
    assert risposta.status_code == 200
    assert risposta.json()["stato"] == "inviata"
    assert c.profilo_snapshot == fotografia
    assert c.frequenza == fotografia["frequenza"]
    assert c.obiettivo == fotografia["obiettivo"]
    assert c.inviata_il == data_invio
    assert f.analisi_ai == {"idonea": True, "punteggio": 80}
    assert len(coda.jobs) == 1
    assert client.post(f"/api/campagne/{c.id}/riprova").status_code == 409
    assert len(coda.jobs) == 1


@pytest.mark.parametrize(
    "stato",
    [
        "bozza",
        "inviata",
        "in_generazione",
        "in_revisione",
        "attiva",
        "conclusa",
        "piano_da_rivedere",
    ],
)
def test_riprova_rifiuta_altri_stati(db, client, utente_di_prova, coda, stato):
    c = campagna_inviata(db)
    c.stato = stato
    db.flush()
    utente_di_prova("operatore")
    assert client.post(f"/api/campagne/{c.id}/riprova").status_code == 409
    assert c.stato == stato and not coda.jobs


def test_riprova_artigiano_vietata_e_inesistente(db, client, utente_di_prova, coda):
    c = campagna_inviata(db)
    c.stato = "generazione_fallita"
    db.flush()
    utente_di_prova("artigiano")
    assert client.post(f"/api/campagne/{c.id}/riprova").status_code == 403
    utente_di_prova("operatore")
    assert client.post("/api/campagne/999999/riprova").status_code == 404
    assert not coda.jobs


@pytest.mark.parametrize("azione", ["invia", "riprova"])
def test_errore_coda_annulla_transazione(db, bozza, monkeypatch, azione):
    u, _, c, _ = bozza
    if azione == "riprova":
        c.stato = "generazione_fallita"
    db.flush()
    stato_originale = c.stato

    def fallisce(*args, **kwargs):
        raise RuntimeError("Coda indisponibile")

    monkeypatch.setattr(modulo_coda, "accoda", fallisce)
    with pytest.raises(RuntimeError), db.begin_nested():
        if azione == "invia":
            service.invia_campagna(db, u.id, c.id, ORA)
        else:
            service.riprova_campagna(db, c.id, ORA)
    db.refresh(c)
    assert c.stato == stato_originale
    assert c.inviata_il is None and c.profilo_snapshot is None
