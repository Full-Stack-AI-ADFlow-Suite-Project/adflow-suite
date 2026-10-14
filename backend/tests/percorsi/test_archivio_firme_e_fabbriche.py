"""T2a-01: apertura dello sprint 2a (colonna, firme e fabbriche)."""
import inspect
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, text

from app.moduli.campagne import domain
from app.moduli.campagne import service as campagne
from app.moduli.campagne.models import Foto
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    ANALISI_IDONEA,
    campagna_conclusa,
    campagna_in_bozza,
    campagna_inviata,
    foto,
    gruppo_di_archivio,
)

ORA = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)


def test_foto_nasce_mai_pubblicata_e_ricorda_canale_e_istante(db):
    immagine = foto(db)
    db.expire(immagine)
    assert immagine.pubblicata_su == {}
    immagine.pubblicata_su = {"instagram": ORA.isoformat()}
    db.flush()
    db.expire(immagine)
    assert immagine.pubblicata_su == {"instagram": "2030-01-05T12:00:00+00:00"}
    assert datetime.fromisoformat(immagine.pubblicata_su["instagram"]) == ORA


def test_pubblicata_su_non_resta_vuota_nel_database(db):
    immagine = foto(db)
    assert (
        db.scalar(
            text("select pubblicata_su::text from foto where id = :id"),
            {"id": immagine.id},
        )
        == "{}"
    )


@pytest.mark.parametrize(
    ("funzione", "parametri"),
    [
        ("foto_di_archivio", ["db", "profilo_id", "canale", "adesso"]),
        ("segna_pubblicata", ["db", "foto_id", "canale", "quando"]),
        ("foto_per_id", ["db", "ids"]),
    ],
)
def test_firme_dello_sprint_2a(funzione, parametri):
    """Le firme di plan §6: chi le scrive e chi le usa parte da queste."""
    firma = inspect.signature(getattr(campagne, funzione))
    assert list(firma.parameters) == parametri


def test_foto_di_archivio_dice_foto_gruppo_e_se_e_mai_uscita():
    assert campagne.FotoDiArchivio._fields == ("foto", "gruppo", "mai_uscita")


def test_foto_per_id_legge_foto_di_campagne_diverse_e_dell_archivio(db):
    di_campagna = foto(db)
    di_archivio = gruppo_di_archivio(db, n_foto=1).foto[0]
    foto(db)  # non richiesta
    trovate = campagne.foto_per_id(db, [di_archivio.id, di_campagna.id, -1])
    assert trovate == [di_campagna, di_archivio]
    assert campagne.foto_per_id(db, []) == []


def test_gruppo_di_archivio_senza_campagna_con_foto_idonee(db):
    mazzo = gruppo_di_archivio(db)
    db.expire_all()
    assert mazzo.campagna_id is None
    assert mazzo.origine == "caricate"
    assert mazzo.descrizione
    assert len(mazzo.foto) == 2
    for immagine in mazzo.foto:
        assert immagine.profilo_id == mazzo.profilo_id
        assert immagine.campagna_id is None
        assert immagine.origine == "caricata"
        assert immagine.analisi_ai == ANALISI_IDONEA
        assert immagine.pubblicata_su == {}


def test_gruppo_di_archivio_del_profilo_indicato_e_senza_foto(db):
    bottega = profilo(db)
    mazzo = gruppo_di_archivio(db, profilo_id=bottega.id, n_foto=0)
    assert mazzo.profilo_id == bottega.id
    assert mazzo.foto == []
    da_analizzare = foto(db, gruppo=mazzo)
    db.expire_all()
    assert mazzo.foto == [da_analizzare]
    assert da_analizzare.analisi_ai is None


def test_il_gruppo_di_archivio_non_e_di_nessuna_campagna(db):
    record = campagna_inviata(db)
    gruppo_di_archivio(db, profilo_id=record.profilo_id)
    assert len(campagne.gruppi_della_campagna(db, record.id)) == 1
    assert len(campagne.foto_della_campagna(db, record.id)) == 4


def test_campagna_conclusa_chiusa_con_foto_idonee_mai_pubblicate(db):
    record = campagna_conclusa(db)
    db.expire_all()
    assert record.stato == "conclusa"
    assert record.stato in domain.STATI_CHIUSI
    assert record.inviata_il < record.chiusa_il
    assert record.chiusa_il.date() > record.fine
    assert record.profilo_snapshot["nome"] == "Bottega di prova"
    immagini = db.scalars(select(Foto).where(Foto.campagna_id == record.id)).all()
    assert len(immagini) == 4
    assert all(i.analisi_ai == ANALISI_IDONEA for i in immagini)
    assert all(i.pubblicata_su == {} for i in immagini)


def test_campagna_conclusa_non_si_sovrappone_a_una_bozza_dello_stesso_profilo(db):
    chiusa = campagna_conclusa(db)
    bozza = campagna_in_bozza(db, profilo_id=chiusa.profilo_id)
    assert chiusa.fine < bozza.inizio


def test_le_fabbriche_non_condividono_l_analisi(db):
    prima, seconda = gruppo_di_archivio(db).foto
    prima.analisi_ai["idonea"] = False
    assert seconda.analisi_ai["idonea"] is True
    assert ANALISI_IDONEA["idonea"] is True
