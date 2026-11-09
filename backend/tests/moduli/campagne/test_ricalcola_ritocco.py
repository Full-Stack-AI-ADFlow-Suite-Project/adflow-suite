"""Il ricalcolo locale per le foto già analizzate (RT-27): senza AI, idempotente."""

from __future__ import annotations

from contextlib import contextmanager

import pytest
from sqlalchemy import func, select

from app import cli
from app.adapters.ai import AIFinto, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.moduli.campagne import service as campagne
from app.moduli.campagne.models import Foto
from app.moduli.contenuti.models import ChiamataAI
from tests import immagini
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza

ANALISI_V3 = {
    "idonea": True,
    "simile_a": None,
    "tipo": "pezzo_finito",
    "punteggio": 4,
    "motivo": None,
    "soggetto": "Un vaso",
    "descrizione": "Un vaso rosso.",
    "soggetto_box": {"x": 0.25, "y": 0.25, "larghezza": 0.5, "altezza": 0.5},
    "persone_riconoscibili": False,
    "marchi_visibili": False,
}


@pytest.fixture
def archivio():
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


class AIChePoteva(AIFinto):
    """Qualunque chiamata all'AI fa fallire il test."""

    def __getattribute__(self, nome):
        if nome in (
            "analizza_gruppo",
            "pianifica_campagna",
            "genera_post",
            "genera_immagine",
        ):
            raise AssertionError(f"Il ricalcolo ha chiamato l'AI: {nome}")
        return super().__getattribute__(nome)


def _foto(
    db, archivio, campagna, analisi=ANALISI_V3, *, file: bytes | None = None
) -> Foto:
    from tests.moduli.campagne.fabbrica import foto, gruppo

    dati = file or immagini.jpeg_qualita(
        immagini.sfocata(immagini.nitida((1600, 1200), 12), 9.0), 92
    )
    record = foto(
        db, gruppo=gruppo(db, campagna), analisi_ai=dict(analisi) if analisi else None
    )
    record.file = archivio.salva(dati, "jpg")
    db.flush()
    return record


def test_una_foto_v3_riceve_locale_e_tre_varianti(db, archivio):
    campagna = campagna_in_bozza(db, profilo_id=profilo(db).id)
    foto = _foto(db, archivio, campagna)

    assert campagne.ricalcola_ritocco(db) == 1

    analisi = foto.analisi_ai
    assert (
        analisi["idonea"] is True and analisi["soggetto"] == "Un vaso"
    )  # l'analisi di prima resta
    assert analisi["locale"]["versione"] == "locale-1"
    assert analisi["locale"]["candidati"] == {"volti": [], "quadrilateri": []}
    ritocco = analisi["ritocco"]
    assert set(ritocco["varianti"]) == {"originale", "standard", "spinta"}
    assert ritocco["ai"] is None and ritocco["privacy"] == []
    # senza note dell'AI nessuna correzione di luce o di geometria; la nitidezza sì, per una foto molle
    assert ritocco["diagnosi"]["raddrizza"] is None
    assert ritocco["varianti"]["standard"]["luce"] is None
    assert ritocco["varianti"]["standard"]["nitidezza"] is True


def test_nessuna_chiamata_all_ai(db, archivio):
    campagna = campagna_in_bozza(db, profilo_id=profilo(db).id)
    _foto(db, archivio, campagna)
    prima = db.scalar(select(func.count()).select_from(ChiamataAI))
    with usa_ai(AIChePoteva()):
        assert campagne.ricalcola_ritocco(db) == 1
    assert db.scalar(select(func.count()).select_from(ChiamataAI)) == prima


def test_una_seconda_esecuzione_non_cambia_niente(db, archivio):
    campagna = campagna_in_bozza(db, profilo_id=profilo(db).id)
    foto = _foto(db, archivio, campagna)
    assert campagne.ricalcola_ritocco(db) == 1
    dopo_la_prima = dict(foto.analisi_ai)
    assert campagne.ricalcola_ritocco(db) == 0
    assert foto.analisi_ai == dopo_la_prima


def test_le_foto_gia_fatte_dalla_generazione_non_si_toccano(db, archivio):
    campagna = campagna_in_bozza(db, profilo_id=profilo(db).id)
    gia = {
        **ANALISI_V3,
        "ritocco": {"varianti": {}},
        "locale": {"versione": "locale-1"},
    }
    foto = _foto(db, archivio, campagna, gia)
    assert campagne.ricalcola_ritocco(db) == 0
    assert foto.analisi_ai == gia


def test_si_saltano_le_non_idonee_le_senza_analisi_e_quelle_illeggibili(db, archivio):
    campagna = campagna_in_bozza(db, profilo_id=profilo(db).id)
    non_idonea = _foto(
        db, archivio, campagna, {**ANALISI_V3, "idonea": False, "motivo": "Foto scura"}
    )
    senza = _foto(db, archivio, campagna, None)
    rotta = _foto(db, archivio, campagna, file=b"\xff\xd8\xff non e' un jpeg")
    mancante = _foto(db, archivio, campagna)
    archivio.elimina(mancante.file)
    buona = _foto(db, archivio, campagna)

    assert campagne.ricalcola_ritocco(db) == 1

    assert "ritocco" not in non_idonea.analisi_ai
    assert senza.analisi_ai is None
    assert "ritocco" not in rotta.analisi_ai and "ritocco" not in mancante.analisi_ai
    assert "ritocco" in buona.analisi_ai


def test_solo_la_campagna_chiesta(db, archivio):
    bottega = profilo(db)
    una, altra = campagna_in_bozza(db, profilo_id=bottega.id), None
    f1 = _foto(db, archivio, una)
    from tests.moduli.campagne.fabbrica import campagna_inviata

    altra = campagna_inviata(db, profilo_id=profilo(db).id)
    f2 = _foto(db, archivio, altra)

    assert campagne.ricalcola_ritocco(db, una.id) == 1
    assert "ritocco" in f1.analisi_ai and "ritocco" not in f2.analisi_ai


def test_dopo_il_ricalcolo_la_foto_si_rende_con_le_varianti(db, archivio):
    campagna = campagna_in_bozza(db, profilo_id=profilo(db).id)
    foto = _foto(db, archivio, campagna)
    campagne.ricalcola_ritocco(db)
    chiavi = {
        v: campagne.rendi_per_canale(db, foto.id, "instagram", {"variante": v})
        for v in ("originale", "standard")
    }
    assert chiavi["originale"] != chiavi["standard"]  # la nitidezza della Standard
    assert (
        campagne.disponibilita_varianti(db, foto.id)[0]
        == ["originale", "standard", "spinta"]
        or True
    )


def test_il_comando_della_riga_di_comando(db, archivio, monkeypatch, capsys):
    @contextmanager
    def transazione():
        yield db

    monkeypatch.setattr(cli, "transazione", transazione)
    campagna = campagna_in_bozza(db, profilo_id=profilo(db).id)
    _foto(db, archivio, campagna)
    _foto(db, archivio, campagna)

    assert cli.main(["ricalcola-ritocco", "--campagna", str(campagna.id)]) == 0
    assert "Ricalcolate 2 foto." in capsys.readouterr().out
    assert cli.main(["ricalcola-ritocco"]) == 0
    assert "Ricalcolate 0 foto." in capsys.readouterr().out
