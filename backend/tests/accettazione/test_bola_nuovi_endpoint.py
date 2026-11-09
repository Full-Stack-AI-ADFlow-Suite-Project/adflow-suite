"""Letture trasversali (BOLA) sui nuovi endpoint della corsia 9 (T4-102, R-17).

Due botteghe complete, A e B: ogni elenco o scelta che parta da una risorsa di
A non deve mai mostrare o accettare una foto di B. L'atteso viene da R-36,
R-47, R-48, R-50 e CA-94.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.main import app
from app.moduli.accesso.service import utente_corrente
from app.moduli.campagne.models import Foto, GruppoFoto
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_in_revisione,
    gruppo_di_archivio,
)
from tests.moduli.contenuti.fabbrica import (
    chiamata_ai,
    post_approvato,
    post_da_approvare,
)


@pytest.fixture
def due_botteghe(db: Session, client: TestClient, utente_di_prova):
    """A e B con campagna in revisione, archivio e (per A) un post approvato."""
    operatore = utente_di_prova("operatore")
    a = utente(db, "artigiano")
    b = utente(db, "artigiano")
    bottega_a = profilo(db, utente_id=a.id)
    bottega_b = profilo(db, utente_id=b.id)

    campagna_a = campagna_in_revisione(db, profilo_id=bottega_a.id)
    post_a = post_da_approvare(db, campagna_id=campagna_a.id)
    archivio_a = gruppo_di_archivio(db, profilo_id=bottega_a.id)

    campagna_b = campagna_in_revisione(db, profilo_id=bottega_b.id)
    post_b = post_da_approvare(db, campagna_id=campagna_b.id)
    archivio_b = gruppo_di_archivio(db, profilo_id=bottega_b.id)

    # una campagna attiva di A con un post approvato nella settimana nota
    attiva_a = campagna_attiva(db, profilo_id=bottega_a.id)
    lunedi = date(2030, 1, 7)  # un lunedì della campagna di A
    approvato_a = post_approvato(
        db,
        campagna_id=attiva_a.id,
        data_ora=datetime(2030, 1, 9, 12, tzinfo=timezone.utc),
    )

    chiamata_a = chiamata_ai(db, campagna_a)

    db.flush()
    yield {
        "a": a,
        "b": b,
        "operatore": operatore,
        "bottega_a": bottega_a,
        "bottega_b": bottega_b,
        "campagna_a": campagna_a.id,
        "campagna_b": campagna_b.id,
        "post_a": post_a.id,
        "post_b": post_b.id,
        "approvato_a": approvato_a.id,
        "archivio_a": archivio_a.id,
        "archivio_b": archivio_b.id,
        "chiamata_a": chiamata_a.id,
        "lunedi": lunedi.isoformat(),
    }


def _foto_del_gruppo(db: Session, gruppo_id: int) -> list[int]:
    return list(db.scalars(select(Foto.id).where(Foto.gruppo_id == gruppo_id)).all())


def _gruppo_della_campagna(db: Session, campagna_id: int) -> int:
    return db.scalar(select(GruppoFoto.id).where(GruppoFoto.campagna_id == campagna_id))


def _entra_da(record) -> None:
    app.dependency_overrides[utente_corrente] = lambda: record


def test_foto_possibili_non_mai_foto_di_un_altra_bottega(due_botteghe, client, db):
    """L'elenco di cambio immagine parte dal post di A: solo foto di A (R-36)."""
    _entra_da(due_botteghe["operatore"])
    risposta = client.get(f"/api/post/{due_botteghe['post_a']}/foto-possibili")
    assert risposta.status_code == 200
    foto_bottega_b = set(
        _foto_del_gruppo(db, due_botteghe["archivio_b"])
        + _foto_del_gruppo(db, _gruppo_della_campagna(db, due_botteghe["campagna_b"]))
    )
    ids = {f["foto_id"] for f in risposta.json()}
    assert ids, "l'elenco non può essere vuoto: la campagna di A ha foto libere"
    assert not (ids & foto_bottega_b), "foto di un'altra bottega nell'elenco: BOLA"


def test_cambia_foto_con_una_foto_di_un_altra_bottega_e_rifiutato(
    due_botteghe, client, db
):
    """R-36: la foto nuova viene dall'elenco; una foto di B è fuori elenco → 422."""
    _entra_da(due_botteghe["operatore"])
    foto_di_b = _foto_del_gruppo(
        db, _gruppo_della_campagna(db, due_botteghe["campagna_b"])
    )
    risposta = client.post(
        f"/api/post/{due_botteghe['post_a']}/cambia-foto",
        json={"foto_id": foto_di_b[0]},
    )
    assert risposta.status_code == 422, (
        f"atteso 422 (foto fuori dall'elenco), risposta {risposta.status_code}: "
        f"{risposta.json()}"
    )


def test_archivio_foto_dell_artigiano_ignora_il_parametro_di_un_altro(
    due_botteghe, client, db
):
    """L'artigiano B chiede l'archivio di A con ?artigiano=: vede solo il suo."""
    _entra_da(due_botteghe["b"])
    risposta = client.get(f"/api/archivio-foto?artigiano={due_botteghe['a'].id}")
    assert risposta.status_code == 200
    blocchi = risposta.json()
    foto_ottenute = {f["id"] for blocco in blocchi for f in blocco["foto"]}
    foto_di_a = set(
        _foto_del_gruppo(db, due_botteghe["archivio_a"])
        + _foto_del_gruppo(db, _gruppo_della_campagna(db, due_botteghe["campagna_a"]))
    )
    assert not (foto_ottenute & foto_di_a), "B vede foto di A: BOLA (blocco assoluto)"


def test_campagne_con_il_filtro_artigiano_di_un_altro_restano_le_sue(
    due_botteghe, client
):
    """CA-94: l'artigiano con ?artigiano di un altro vede solo le sue campagne."""
    _entra_da(due_botteghe["b"])
    risposta = client.get(f"/api/campagne?artigiano={due_botteghe['a'].id}")
    assert risposta.status_code == 200
    ids = {c["id"] for c in risposta.json()}
    assert due_botteghe["campagna_b"] in ids
    assert not (ids & {due_botteghe["campagna_a"]}), "B vede campagne di A: BOLA"


def test_calendario_dell_artigiano_non_mai_i_post_di_un_altro(due_botteghe, client):
    """R-48: B vede solo i suoi post; quello approvato di A non compare."""
    _entra_da(due_botteghe["b"])
    risposta = client.get(f"/api/calendario?dal={due_botteghe['lunedi']}")
    assert risposta.status_code == 200
    for giorno in risposta.json()["giorni"]:
        for post in giorno["post"]:
            assert (
                post["campagna_id"] != due_botteghe["campagna_a"]
            ), "il calendario di B mostra un post di A: BOLA"


def test_lo_storico_ai_di_a_non_si_legge_da_artigiano(due_botteghe, client):
    """R-50: lo storico è degli operatori; l'artigiano B non legge la riga di A."""
    _entra_da(due_botteghe["b"])
    risposta = client.get(f"/api/storico-ai/{due_botteghe['chiamata_a']}")
    assert risposta.status_code == 403
    risposta = client.get("/api/storico-ai")
    assert risposta.status_code == 403


def test_anteprima_della_foto_di_un_post_di_a_non_si_legge_da_b(due_botteghe, client):
    """RT-08: l'anteprima è del proprietario e dell'operatore; B riceve 404, mai la foto."""
    _entra_da(due_botteghe["b"])
    for post in (due_botteghe["approvato_a"], due_botteghe["post_a"]):
        risposta = client.get(f"/api/post/{post}/foto/anteprima")
        assert risposta.status_code == 404, risposta.text


def test_anteprima_dell_artigiano_solo_sui_post_approvati(due_botteghe, client):
    """D1: A vede il render dei suoi post approvati; il post ancora in revisione dà 409."""
    _entra_da(due_botteghe["a"])
    risposta = client.get(f"/api/post/{due_botteghe['post_a']}/foto/anteprima")
    assert risposta.status_code == 409
    assert "image" not in risposta.headers.get("content-type", "")
