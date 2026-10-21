"""T3-78: il percorso delle pagine della corsia 7 (ADR-117, CA-99).

Un artigiano ha una campagna approvata con un'immagine AI e un post, e una
campagna in revisione con una richiesta del consorzio aperta e le sue
immagini AI. Tutto passa dalle API:

1. l'operatore trova l'artigiano nell'elenco, ne apre la scheda, le campagne
   e l'archivio foto, dove c'è l'immagine AI della campagna approvata;
2. l'artigiano vede la richiesta aperta nel suo elenco e, nel suo archivio,
   l'immagine AI della campagna approvata ma non quelle della campagna in
   revisione (spec §4, CA-31);
3. il calendario della settimana del post approvato lo mostra a tutti e due.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.main import app
from app.moduli.accesso.service import utente_corrente
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_in_revisione,
    foto,
    gruppo,
    richiesta,
)
from tests.moduli.contenuti.fabbrica import post_approvato, post_da_approvare

# Il giovedì 10 gennaio 2030 alle 10:00 UTC, nella settimana che comincia lunedì 7.
QUANDO = datetime(2030, 1, 10, 10, tzinfo=timezone.utc)
LUNEDI = date(2030, 1, 7)


def _immagine_ai(db: Session, campagna) -> int:
    return foto(db, gruppo=gruppo(db, campagna), gruppo_id=None, origine="creata_ai").id


def test_ca99_percorso_pagine(db: Session, client: TestClient, utente_di_prova):
    proprietario = utente(db, "artigiano", nome="Mario Bianchi")
    bottega = profilo(db, utente_id=proprietario.id, nome="Falegnameria Bianchi")
    approvata = campagna_attiva(db, profilo_id=bottega.id, titolo="Autunno")
    ai_approvata = _immagine_ai(db, approvata)
    post = post_approvato(db, campagna_id=approvata.id, data_ora=QUANDO)
    in_revisione = campagna_in_revisione(
        db, profilo_id=bottega.id, titolo="Natale", inizio=date(2030, 2, 1)
    )
    ai_in_revisione = _immagine_ai(db, in_revisione)
    post_da_approvare(db, campagna_id=in_revisione.id, data_ora=QUANDO)
    richiesta(db, in_revisione)

    # 1. L'operatore: elenco → scheda → campagne → archivio.
    utente_di_prova("operatore")
    elenco = client.get("/api/artigiani").json()
    riga = next(r for r in elenco if r["id"] == proprietario.id)
    assert (riga["bottega"], riga["n_in_corso"], riga["n_da_approvare"]) == (
        "Falegnameria Bianchi",
        1,
        1,
    )

    scheda = client.get(f"/api/artigiani/{proprietario.id}").json()
    assert scheda["profilo"]["nome"] == "Falegnameria Bianchi"
    assert scheda["email"] == proprietario.email

    campagne = client.get("/api/campagne", params={"artigiano": proprietario.id})
    assert {c["id"] for c in campagne.json()} == {approvata.id, in_revisione.id}

    archivio = client.get("/api/archivio-foto", params={"artigiano": proprietario.id})
    visibili = {f["id"] for b in archivio.json() for f in b["foto"]}
    assert {ai_approvata, ai_in_revisione} <= visibili  # l'operatore le vede tutte

    # 2. L'artigiano: la richiesta aperta e il suo archivio.
    app.dependency_overrides[utente_corrente] = lambda: proprietario
    sue = {c["id"]: c for c in client.get("/api/campagne").json()}
    assert sue[in_revisione.id]["richiesta"] == "aperta"

    suo = client.get("/api/archivio-foto").json()
    sue_foto = {f["id"] for b in suo for f in b["foto"]}
    assert ai_approvata in sue_foto
    assert ai_in_revisione not in sue_foto

    # 3. Il calendario della settimana del post, per tutti e due.
    per_artigiano = client.get("/api/calendario", params={"dal": LUNEDI.isoformat()})
    assert per_artigiano.status_code == 200
    giorni = per_artigiano.json()["giorni"]
    assert len(giorni) == 7
    assert [p["id"] for g in giorni for p in g["post"]] == [post.id]
    assert giorni[3]["post"][0]["campagna_titolo"] == "Autunno"  # giovedì

    utente_di_prova("operatore")
    per_operatore = client.get("/api/calendario", params={"dal": LUNEDI.isoformat()})
    assert post.id in [
        p["id"] for g in per_operatore.json()["giorni"] for p in g["post"]
    ]
    # Lo stesso post, dalla settimana dopo, non c'è.
    dopo = LUNEDI + timedelta(days=7)
    vuota = client.get("/api/calendario", params={"dal": dopo.isoformat()}).json()
    assert post.id not in [p["id"] for g in vuota["giorni"] for p in g["post"]]
