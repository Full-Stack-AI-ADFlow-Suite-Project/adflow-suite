"""Approva e la privacy: le zone da decidere (RT-29, ADR-124)."""

from __future__ import annotations

import numpy as np
import pytest
from sqlalchemy import select

from app.moduli.campagne import service as campagne
from app.moduli.contenuti.models import VersionePost
from tests import immagini
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.revisione.test_ritocca_foto import (  # noqa: F401
    ZONE,
    _due_post_stessa_foto,
    _ritocca,
    _versioni,
    archivio,
)


def _vista(client, campagna_id):
    return client.get(f"/api/campagne/{campagna_id}/post").json()


def _approva(client, campagna_id, **corpo):
    return client.post(f"/api/campagne/{campagna_id}/approva", json=corpo or None)


def _legami_correnti(db, *post):
    db.expire_all()
    return [_versioni(db, p)[-1].legami_foto[0] for p in post]


def test_la_vista_riassume_le_zone_da_decidere(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    uno, due = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db), zone=ZONE)
    riepilogo = _vista(client, uno.campagna_id)["privacy_da_decidere"]
    assert (riepilogo["foto"], riepilogo["zone"], riepilogo["minori"]) == (
        1,
        1,
        0,
    )  # una foto, su due canali
    assert riepilogo["dettaglio"][0]["post_ids"] == [uno.id, due.id]


def test_senza_zone_il_riepilogo_e_vuoto(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    assert _vista(client, uno.campagna_id)["privacy_da_decidere"] == {
        "foto": 0,
        "zone": 0,
        "minori": 0,
        "dettaglio": [],
    }


def test_i_minori_si_contano(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    zone = ZONE + [
        {"id": "z2", "origine": "V1", "ruolo": "minore", "b": [60, 10, 10, 10]}
    ]
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db), zone=zone)
    riepilogo = _vista(client, uno.campagna_id)["privacy_da_decidere"]
    assert (riepilogo["zone"], riepilogo["minori"]) == (2, 1)
    avvisi = next(
        p["foto"]["avvisi"]
        for u in _vista(client, uno.campagna_id)["uscite"]
        for p in u["post"]
        if p["post_id"] == uno.id
    )
    assert "privacy_da_decidere" in avvisi and "volto_minore" in avvisi


def test_approva_senza_conferma_con_zone_da_decidere_e_422_con_il_riepilogo(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, due = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db), zone=ZONE)
    for corpo in ({}, {"conferma_privacy": False, "oscura_tutte": False}):
        risposta = _approva(client, uno.campagna_id, **corpo)
        assert risposta.status_code == 422
        assert "1 foto con 1 zone di privacy da decidere" in risposta.json()["detail"]
    senza_corpo = client.post(f"/api/campagne/{uno.campagna_id}/approva")
    assert senza_corpo.status_code == 422
    db.refresh(uno)
    assert uno.stato == "da_approvare" and len(_versioni(db, uno)) == 1


def test_con_la_conferma_si_approva_e_le_zone_restano_spente(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, due = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db), zone=ZONE)

    assert _approva(client, uno.campagna_id, conferma_privacy=True).status_code == 200

    db.expire_all()
    assert (uno.stato, due.stato) == ("approvato", "approvato")
    for legame in _legami_correnti(db, uno, due):
        assert not (legame.ritocco or {}).get("privacy")
        assert legame.render is not None
    assert len(_versioni(db, uno)) == 1  # nessuna versione in più


def test_oscura_tutte_accende_le_zone_e_il_render_e_sfocato(
    db, client, utente_di_prova, archivio
):
    operatore = utente_di_prova("operatore")
    uno, due = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db), zone=ZONE)

    assert _approva(client, uno.campagna_id, oscura_tutte=True).status_code == 200

    db.expire_all()
    assert (uno.stato, due.stato) == ("approvato", "approvato")
    for post in (uno, due):
        precedente, ultima = _versioni(db, post)
        assert (
            ultima.tipo_intervento == "ritocco_foto"
            and ultima.autore_id == operatore.id
        )
        assert ultima.legami_foto[0].ritocco["privacy"] is True
    # il render approvato ha la zona sfocata: diverso da quello con la conferma sola
    legame = _legami_correnti(db, uno)[0]
    sfocato = archivio.leggi_derivato(legame.foto_id, legame.render)
    spenta = campagne.leggi_render(
        legame.foto_id,
        campagne.rendi_per_canale(
            db, legame.foto_id, "instagram", {"variante": "standard"}
        ),
    )
    assert sfocato != spenta
    zona = (
        slice(int(0.1 * 1080), int(0.5 * 1080)),
        slice(int(0.1 * 1440), int(0.5 * 1440)),
    )
    a, b = (np.asarray(immagini.apri(x)) for x in (sfocato, spenta))
    assert a.shape == b.shape and np.abs(a.astype(int) - b.astype(int))[zona].sum() > 0
    # le due versioni di quello che si è approvato hanno la riga di approvazione
    from app.moduli.revisione.models import Approvazione

    versioni_approvate = {a.versione_id for a in db.scalars(select(Approvazione))}
    assert (
        _versioni(db, uno)[-1].id in versioni_approvate
        and _versioni(db, due)[-1].id in versioni_approvate
    )


def test_senza_zone_si_approva_come_oggi_con_o_senza_corpo(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, due = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    assert client.post(f"/api/campagne/{uno.campagna_id}/approva").status_code == 200
    db.expire_all()
    assert uno.stato == "approvato"
    assert len(_versioni(db, uno)) == 1


def test_senza_zone_conferma_e_oscura_tutte_non_fanno_niente_di_male(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    assert _approva(client, uno.campagna_id, oscura_tutte=True).status_code == 200
    db.expire_all()
    assert len(_versioni(db, uno)) == 1


def test_le_zone_gia_decise_non_chiedono_niente(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db), zone=ZONE)
    assert (
        _ritocca(client, uno, privacy=False).status_code == 200
    )  # "lasciale spente", deciso a mano
    assert _vista(client, uno.campagna_id)["privacy_da_decidere"]["zone"] == 0
    assert _approva(client, uno.campagna_id).status_code == 200


def test_oscurata_a_mano_non_serve_oscurare_ancora(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db), zone=ZONE)
    _ritocca(client, uno, privacy=True)
    assert _approva(client, uno.campagna_id).status_code == 200
    db.expire_all()
    assert _legami_correnti(db, uno)[0].ritocco["privacy"] is True


def test_corpo_non_valido_422(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    assert _approva(client, uno.campagna_id, altro=True).status_code == 422
    assert (
        client.post(
            f"/api/campagne/{uno.campagna_id}/approva", json={"oscura_tutte": "forse"}
        ).status_code
        == 422
    )


def test_l_artigiano_non_approva(db, client, utente_di_prova, archivio):
    utente_di_prova("artigiano")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db), zone=ZONE)
    assert _approva(client, uno.campagna_id, oscura_tutte=True).status_code == 403
