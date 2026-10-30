"""§1.2 — Niente si cancella: versioni, foto, decisioni, campagne restano.

Attacchi di §4.3: le 4 DELETE (`/foto/{id}`, gruppi, archivio) solo in bozza,
mai su foto già usate in una versione; cercare `db.delete` e DELETE su tabelle
con storico.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.errori import StatoNonValido
from app.main import app
from app.moduli.campagne.models import Campagna, Foto, GruppoFoto
from app.moduli.campagne import service as campagne_service
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_in_bozza,
    campagna_in_revisione,
    foto,
    gruppo,
)
from tests.moduli.contenuti.fabbrica import post_da_approvare

METODI_DELETE_ATTESI = {
    "/api/foto/{id}",
    "/api/campagne/{id}/gruppi/{gruppo_id}",
    "/api/archivio/foto/{id}",
    "/api/archivio/gruppi/{id}",
}


def test_le_uniche_delete_sono_le_quattro_su_foto_e_gruppi():
    """Nessuna rotta DELETE su campagne, post, versioni, decisioni, storico."""
    schema = app.openapi()
    delete = {
        percorso for percorso, metodi in schema["paths"].items() if "delete" in metodi
    }
    assert delete == METODI_DELETE_ATTESI


def test_una_foto_usata_in_una_versione_non_si_cancella(db, utente_di_prova):
    """La foto di un post non si elimina: 409, la riga resta (R-13, §1.2)."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    post_da_approvare(db, campagna_id=campagna.id)
    db.flush()
    usata = db.scalars(
        select(Foto)
        .where(Foto.campagna_id == campagna.id, Foto.n_utilizzi > 0)
        .order_by(Foto.id)
    ).first()
    assert usata is not None

    # la campagna non è in bozza: il motivo dichiarato è lo stato
    with pytest.raises(StatoNonValido):
        campagne_service.elimina_foto(
            db, utente_id=artigiano.id, ruolo="artigiano", foto_id=usata.id
        )
    assert db.scalar(select(Foto.id).where(Foto.id == usata.id)) == usata.id


def test_un_gruppo_con_una_foto_usata_non_si_cancella(db, utente_di_prova):
    """Il gruppo della campagna con la foto usata resta: 409 (§1.2)."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    post_da_approvare(db, campagna_id=campagna.id)
    db.flush()
    mazzo = db.scalars(
        select(GruppoFoto).where(GruppoFoto.campagna_id == campagna.id)
    ).first()

    with pytest.raises(StatoNonValido):
        campagne_service.elimina_gruppo(
            db,
            utente_id=artigiano.id,
            ruolo="artigiano",
            campagna_id=campagna.id,
            gruppo_id=mazzo.id,
        )
    assert db.scalar(select(GruppoFoto.id).where(GruppoFoto.id == mazzo.id)) == mazzo.id


def test_una_foto_di_bozza_non_usata_si_cancella_e_il_resto_resta(db, utente_di_prova):
    """Il caso ammesso: in bozza una foto non usata si elimina, la campagna resta."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_bozza(db, profilo_id=bottega.id)
    mazzo = gruppo(db, campagna)
    db.flush()
    immagine = foto(db, gruppo=mazzo, n_utilizzi=0)
    db.flush()

    campagne_service.elimina_foto(
        db, utente_id=artigiano.id, ruolo="artigiano", foto_id=immagine.id
    )
    assert db.scalar(select(Foto.id).where(Foto.id == immagine.id)) is None
    assert (
        db.scalar(select(Campagna.id).where(Campagna.id == campagna.id)) == campagna.id
    )
