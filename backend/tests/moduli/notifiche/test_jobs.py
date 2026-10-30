"""Il job ``invia_notifica`` compone e manda l'email della notifica."""

import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from io import BytesIO

import pytest
from PIL import Image

from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.adapters.email import EmailFinto, usa_email
from app.moduli.accesso.models import Utente
from app.moduli.notifiche import domain, jobs, service, testi
from app.moduli.notifiche.models import Notifica
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.notifiche.fabbrica import notifica

ORA = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)


@pytest.fixture
def email():
    finto = EmailFinto()
    with usa_email(finto):
        yield finto


@pytest.fixture
def archivio():
    finto = ArchivioFinto()
    with usa_archivio(finto):
        yield finto


@pytest.fixture(autouse=True)
def transazioni_di_prova(db, monkeypatch):
    """Il job apre le sue transazioni sulla sessione del test, a un'ora fissa."""

    @contextmanager
    def transazione():
        with db.begin_nested():
            yield db

    monkeypatch.setattr(jobs, "transazione", transazione)
    monkeypatch.setattr(jobs, "adesso", lambda: ORA)


def _foto_jpeg(larghezza=1200, altezza=800):
    buffer = BytesIO()
    Image.new("RGB", (larghezza, altezza), color="red").save(buffer, format="JPEG")
    return buffer.getvalue()


def _respinta(db, archivio):
    """Notifica ``campagna_respinta`` a un artigiano, con 2 foto nell'archivio."""
    artigiano = utente(db, "artigiano", nome="Anna")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    for _ in range(2):
        archivio.salva(_foto_jpeg(), ".jpg")
    nomi = archivio.file_salvati
    riga = notifica(
        db,
        campagna=campagna,
        utente=artigiano,
        tipo="campagna_respinta",
    )
    contenuto = {
        "titolo": campagna.titolo,
        "motivo": "foto",
        "nota": "Le foto del laboratorio sono troppo buie.",
        "foto": [{"nome": n, "mime": "image/jpeg"} for n in nomi],
    }
    return riga, contenuto, artigiano


@pytest.mark.parametrize("tipo", domain.TIPI)
def test_ogni_tipo_ha_un_testo_email(tipo):
    oggetto, corpo = testi.componi(
        tipo,
        {
            "titolo": "Campagna di prova",
            "motivo": "foto",
            "nota": "Rifare le foto.",
            "foto": [{"nome": "foto.jpg", "mime": "image/jpeg"}],
        },
        "Nome di prova",
    )

    assert oggetto
    assert "Campagna di prova" in oggetto
    assert "Nome di prova" in corpo
    assert "Campagna di prova" in corpo


def test_invio_manda_email_e_marca_inviata(db, email, archivio):
    riga = notifica(db)
    contenuto = {"titolo": "Campagna Luglio"}

    service.invia(db, riga.id, contenuto, ORA)

    (mandata,) = email.inviate
    assert mandata.oggetto == f"Campagna pronta: {contenuto['titolo']}"
    assert riga.stato_invio == domain.INVIATA and riga.inviata_il == ORA


def test_ca25_email_respinta_con_motivo_nota_e_miniature(db, email, archivio):
    riga, contenuto, artigiano = _respinta(db, archivio)

    service.invia(db, riga.id, contenuto, ORA)

    (mandata,) = email.inviate
    assert mandata.destinatario == artigiano.email
    assert "respinta" in mandata.oggetto.lower()
    assert "foto da rifare" in mandata.corpo
    assert contenuto["nota"] in mandata.corpo
    assert [a.nome for a in mandata.allegati] == [
        "miniatura-1.jpg",
        "miniatura-2.jpg",
    ]
    assert all(a.mime == "image/jpeg" for a in mandata.allegati)
    for allegato in mandata.allegati:
        with Image.open(BytesIO(allegato.contenuto)) as immagine:
            assert immagine.size == (320, 213)


def test_ca30_email_della_scaduta(db, email, archivio):
    artigiano = utente(db, "artigiano")
    riga = notifica(db, utente=artigiano, tipo="campagna_scaduta")

    service.invia(db, riga.id, {"titolo": "Campagna Natale"}, ORA)

    (mandata,) = email.inviate
    assert mandata.destinatario == artigiano.email
    assert "scaduta" in mandata.oggetto.lower()
    assert "Campagna Natale" in mandata.corpo


def test_crea_inoltra_il_contenuto_al_job(db, coda):
    artigiano = utente(db, "artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    contenuto = {"titolo": campagna.titolo, "motivo": "altro", "nota": "N"}

    nuove = service.crea(
        db,
        "campagna_respinta",
        campagna.id,
        ORA,
        artigiano_id=artigiano.id,
        contenuto=contenuto,
    )

    job = list(coda.jobs.values())[0]
    assert job["args"] == {"notifica_id": nuove[0].id, "contenuto": contenuto}


def test_crea_senza_contenuto_lascia_gli_args_come_prima(db, coda):
    utente(db, "operatore")
    campagna = campagna_in_revisione(db)

    nuove = service.crea(db, "campagna_pronta", campagna.id, ORA)

    (job,) = list(coda.jobs.values())
    assert job["args"] == {"notifica_id": nuove[0].id}


def test_notifica_gia_inviata_non_riparte(db, email):
    riga = notifica(db)
    riga.stato_invio = domain.INVIATA
    db.flush()

    service.invia(db, riga.id, {"titolo": "T"}, ORA)

    assert email.inviate == []


def test_esegui_invio_riprova_fino_al_terzo_poi_fallita(db, email):
    email.fallimenti = 99
    riga = notifica(db)

    assert jobs.esegui_invio(riga.id, None, 1) is True
    assert jobs.esegui_invio(riga.id, None, 2) is True
    assert jobs.esegui_invio(riga.id, None, 3) is False

    db.expire(riga)
    assert db.get(Notifica, riga.id).stato_invio == domain.FALLITA
    assert email.inviate == []


def test_esegui_invio_riesce_al_secondo_tentativo(db, email):
    email.fallimenti = 1
    riga = notifica(db)

    assert jobs.esegui_invio(riga.id, {"titolo": "T"}, 1) is True
    assert jobs.esegui_invio(riga.id, {"titolo": "T"}, 2) is False

    db.expire(riga)
    assert db.get(Notifica, riga.id).stato_invio == domain.INVIATA
    assert len(email.inviate) == 1


def test_nessun_dato_personale_nei_log(db, email, caplog):
    email.fallimenti = 1
    riga = notifica(db)

    with caplog.at_level(logging.ERROR, logger="app.moduli.notifiche.jobs"):
        jobs.esegui_invio(riga.id, {"titolo": "T"}, 1)

    persona = db.get(Utente, riga.utente_id)
    assert persona.email not in caplog.text
    assert persona.nome not in caplog.text
