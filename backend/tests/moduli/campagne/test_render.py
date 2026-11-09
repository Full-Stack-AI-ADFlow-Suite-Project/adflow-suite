"""I render salvati (RT-06, ADR-124): chiave, idempotenza, originale intatto, potatura."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.archivio import ArchivioDisco, ArchivioFinto, usa_archivio
from app.core.errori import DatiNonValidi, NonTrovato
from app.moduli.campagne import service
from app.moduli.campagne.esecutore import Comando, RegoleR42, comando_originale
from app.moduli.campagne.models import Foto
from tests import immagini
from tests.moduli.artigiani.fabbrica import profilo


@pytest.fixture
def archivio():
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


def _foto(db, archivio, nome: str = "a") -> Foto:
    originale = immagini.jpeg_qualita(immagini.nitida((300, 200)), 92)
    record = Foto(
        profilo_id=profilo(db).id,
        file=archivio.salva(originale, "jpg"),
        mime="image/jpeg",
        larghezza=300,
        altezza=200,
        origine="caricata",
        da_usare=False,
        pubblicata_su={},
    )
    db.add(record)
    db.flush()
    return record


def test_rendi_crea_il_file_una_volta_sola(db, archivio):
    foto = _foto(db, archivio)
    comando = comando_originale()
    chiave = service.rendi(db, foto.id, comando)
    assert archivio.esiste_derivato(foto.id, chiave)
    primo = service.leggi_render(foto.id, chiave)
    # una seconda chiamata uguale non riscrive: stessa chiave, stesso istante, un solo file
    istante = archivio.elenca_derivati()[0].scritto_il
    assert service.rendi(db, foto.id, comando) == chiave
    assert [d.chiave for d in archivio.elenca_derivati()] == [chiave]
    assert archivio.elenca_derivati()[0].scritto_il == istante
    assert service.leggi_render(foto.id, chiave) == primo
    assert primo.startswith(b"\xff\xd8\xff")


def test_il_render_e_quello_dell_esecutore(db, archivio):
    from app.moduli.campagne.esecutore import esegui

    foto = _foto(db, archivio)
    comando = comando_originale()
    chiave = service.rendi(db, foto.id, comando)
    assert service.leggi_render(foto.id, chiave) == esegui(
        archivio.leggi(foto.file), comando
    )


def test_chiavi_diverse_per_comandi_diversi(db, archivio):
    foto = _foto(db, archivio)
    a = service.chiave_render(foto.file, comando_originale())
    b = service.chiave_render(foto.file, comando_originale(canale="facebook"))
    c = service.chiave_render(foto.file, Comando(ruota=90))
    d = service.chiave_render(foto.file, comando_originale(), [{"id": "V1"}])
    e = service.chiave_render("altro.jpg", comando_originale())
    assert len({a, b, c, d, e}) == 5
    assert all(len(k) == 64 for k in (a, b, c, d, e))


def test_la_chiave_non_dipende_dall_ordine_delle_zone(archivio):
    z1, z2 = {"id": "V1", "box": [1, 2, 3, 4]}, {"id": "V2", "box": [5, 6, 7, 8]}
    assert service.chiave_render("f.jpg", Comando(), [z1, z2]) == service.chiave_render(
        "f.jpg", Comando(), [z2, z1]
    )


def test_la_chiave_cambia_con_la_versione_dell_esecutore(monkeypatch):
    prima = service.chiave_render("f.jpg", Comando())
    monkeypatch.setattr(service, "VERSIONE_ESECUTORE", "ritocco-2")
    assert service.chiave_render("f.jpg", Comando()) != prima


def test_la_chiave_e_stabile():
    a = service.chiave_render("f.jpg", Comando(finestra=RegoleR42(proporzione="4:5")))
    b = service.chiave_render("f.jpg", Comando(finestra=RegoleR42(proporzione="4:5")))
    assert a == b


def test_l_originale_resta_intatto(db, archivio):
    foto = _foto(db, archivio)
    prima = hashlib.sha256(archivio.leggi(foto.file)).hexdigest()
    service.rendi(db, foto.id, comando_originale())
    service.rendi(db, foto.id, Comando(ruota=90))
    assert hashlib.sha256(archivio.leggi(foto.file)).hexdigest() == prima
    assert archivio.file_salvati == [foto.file]


def test_l_originale_resta_intatto_su_disco(db, tmp_path):
    with usa_archivio(ArchivioDisco(tmp_path)) as disco:
        foto = _foto(db, disco)
        percorso = tmp_path / foto.file
        prima = percorso.read_bytes()
        service.rendi(db, foto.id, comando_originale())
        assert percorso.read_bytes() == prima
        assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
            [foto.file, "derivate"]
        )


def test_foto_o_file_che_non_ci_sono(db, archivio):
    with pytest.raises(NonTrovato):
        service.rendi(db, 999_999, comando_originale())
    foto = _foto(db, archivio)
    archivio.elimina(foto.file)
    with pytest.raises(NonTrovato):
        service.rendi(db, foto.id, comando_originale())


def test_file_non_immagine(db, archivio):
    foto = _foto(db, archivio)
    foto.file = archivio.salva(b"\xff\xd8\xffnon un jpeg vero", "jpg")
    with pytest.raises(DatiNonValidi):
        service.rendi(db, foto.id, comando_originale())
    assert archivio.elenca_derivati() == []


def test_leggere_un_render_che_non_c_e(archivio):
    with pytest.raises(NonTrovato):
        service.leggi_render(1, "a" * 64)
    with pytest.raises(NonTrovato):
        service.leggi_render(1, "../x")


def test_potatura_per_eta_e_render_approvati_protetti(db, archivio):
    foto = _foto(db, archivio)
    adesso = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
    approvato = service.rendi(db, foto.id, comando_originale())
    vecchio = service.rendi(db, foto.id, Comando(ruota=90))
    recente = service.rendi(db, foto.id, Comando(ruota=180))
    quaranta_giorni = (adesso - timedelta(days=40)).timestamp()
    archivio.invecchia_derivato(foto.id, approvato, quaranta_giorni)
    archivio.invecchia_derivato(foto.id, vecchio, quaranta_giorni)
    archivio.invecchia_derivato(
        foto.id, recente, (adesso - timedelta(days=1)).timestamp()
    )

    tolti = service.pota_anteprime(
        protette={approvato}, eta_max=timedelta(days=30), adesso=adesso
    )

    assert tolti == 1
    assert archivio.esiste_derivato(foto.id, approvato)  # §1.2, D2
    assert not archivio.esiste_derivato(foto.id, vecchio)
    assert archivio.esiste_derivato(foto.id, recente)


def test_la_potatura_non_tocca_mai_gli_originali(db, archivio):
    foto = _foto(db, archivio)
    chiave = service.rendi(db, foto.id, comando_originale())
    archivio.invecchia_derivato(foto.id, chiave, 0.0)
    service.pota_anteprime(protette=(), eta_max=timedelta(seconds=1))
    assert archivio.esiste(foto.file)
    assert not archivio.esiste_derivato(foto.id, chiave)
