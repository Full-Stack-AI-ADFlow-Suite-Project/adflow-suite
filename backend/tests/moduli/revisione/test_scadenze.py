"""Test del tick delle scadenze: R-06, R-35, CA-30, CA-68.

``revisione.scadenze(db, adesso)`` è la funzione di plan §6 che il worker
chiama ogni minuto prima di ``pubblica_dovuti()``: qui si prova il suo corpo
con l'istante iniettato, come nel worker vero.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.moduli.artigiani.models import ProfiloBottega
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti
from app.moduli.contenuti.models import ErroreGenerazione
from app.moduli.notifiche.models import Notifica
from app.moduli.revisione import service as revisione
from tests.moduli.campagne.fabbrica import campagna_in_revisione, campagna_inviata
from tests.moduli.contenuti.fabbrica import piano, post_da_approvare

# La campagna di prova va dal 1° al 31 gennaio 2030: 8 post chiesti
# (2 a settimana su un canale), la metà è 4.
ADESSO = datetime(2030, 1, 6, 12, tzinfo=timezone.utc)
POST_PASSATO = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)
POST_FUTURO = datetime(2030, 1, 10, 12, tzinfo=timezone.utc)
PRIMA_DELL_INIZIO = datetime(2029, 12, 20, 12, tzinfo=timezone.utc)


def _da_approvare(db, campagna_id):
    return [
        p
        for p in contenuti.post_della_campagna(db, campagna_id)
        if p.stato == "da_approvare"
    ]


def _notifiche(db, campagna_id):
    return db.scalars(select(Notifica).where(Notifica.campagna_id == campagna_id)).all()


def test_ca30_post_passato_scade_e_la_campagna_resta_aperta(db):
    """Un post con la data passata diventa scaduto; la campagna resta in revisione."""
    campagna = campagna_in_revisione(db)
    piano(db, campagna)
    scaduto = post_da_approvare(db, campagna_id=campagna.id, data_ora=POST_PASSATO)
    for _ in range(4):
        post_da_approvare(db, campagna_id=campagna.id, data_ora=POST_FUTURO)

    revisione.scadenze(db, ADESSO)

    db.refresh(scaduto)
    db.refresh(campagna)
    assert scaduto.stato == "scaduto"
    assert campagna.stato == "in_revisione"
    # Metà esatta dei post chiesti: sotto la metà si scade, a metà no.
    assert len(_da_approvare(db, campagna.id)) == 4
    assert _notifiche(db, campagna.id) == []


def test_ca30_sotto_la_meta_la_campagna_scade_con_i_post(db):
    """Meno della metà dei post chiesti: campagna scaduta, post rimasti scaduti."""
    campagna = campagna_in_revisione(db)
    piano(db, campagna)
    for _ in range(5):
        post_da_approvare(db, campagna_id=campagna.id, data_ora=POST_PASSATO)
    rimasti = [
        post_da_approvare(db, campagna_id=campagna.id, data_ora=POST_FUTURO)
        for _ in range(3)
    ]

    revisione.scadenze(db, ADESSO)

    db.refresh(campagna)
    assert campagna.stato == "scaduta"
    assert campagna.chiusa_il is not None
    assert _da_approvare(db, campagna.id) == []
    for post in rimasti:
        db.refresh(post)
        assert post.stato == "scaduto"

    # L'artigiano riceve la notifica campagna_scaduta (l'email di CA-30).
    bottega = db.get(ProfiloBottega, campagna.profilo_id)
    [notifica] = _notifiche(db, campagna.id)
    assert notifica.tipo == "campagna_scaduta"
    assert notifica.utente_id == bottega.utente_id


def test_ca30_senza_piano_scade_al_giorno_di_inizio(db):
    """Campagna senza piano: scaduta alle 00:00 (Roma) del giorno di inizio."""
    dentro = campagna_inviata(db, inviata_il=ADESSO)
    fuori = campagna_inviata(db, inviata_il=PRIMA_DELL_INIZIO)

    revisione.scadenze(db, PRIMA_DELL_INIZIO)
    db.refresh(fuori)
    assert fuori.stato == "inviata"

    revisione.scadenze(db, ADESSO)
    db.refresh(dentro)
    assert dentro.stato == "scaduta"


def test_ca68_inviata_ferma_da_30_minuti_va_in_generazione_fallita(db):
    """Worker spento durante l'invio: l'errore temporaneo resta accanto a Riprova."""
    campagna = campagna_inviata(
        db, inviata_il=PRIMA_DELL_INIZIO - timedelta(minutes=31)
    )
    viva = campagna_inviata(db, inviata_il=PRIMA_DELL_INIZIO - timedelta(minutes=29))

    revisione.scadenze(db, PRIMA_DELL_INIZIO)
    # Un secondo tick non cambia nulla e non aggiunge errori.
    revisione.scadenze(db, PRIMA_DELL_INIZIO)

    db.refresh(campagna)
    db.refresh(viva)
    assert campagna.stato == "generazione_fallita"
    assert viva.stato == "inviata"
    [errore] = db.scalars(
        select(ErroreGenerazione).where(ErroreGenerazione.campagna_id == campagna.id)
    ).all()
    assert errore.tipo == "temporaneo"
    assert errore.creata_il == PRIMA_DELL_INIZIO


def test_ca68_in_generazione_ferma_da_30_minuti(db):
    """Una generazione senza progressi da 30 minuti si ferma; una viva no."""
    ferma = campagna_inviata(db, inviata_il=PRIMA_DELL_INIZIO - timedelta(minutes=31))
    campagne.cambia_stato(db, ferma, "in_generazione")
    viva = campagna_inviata(db, inviata_il=PRIMA_DELL_INIZIO - timedelta(minutes=31))
    campagne.cambia_stato(db, viva, "in_generazione")
    # La versione scritta 5 minuti fa è un progresso: la campagna non è ferma.
    post = post_da_approvare(db, campagna_id=viva.id)
    [versione] = post.versioni
    versione.creata_il = PRIMA_DELL_INIZIO - timedelta(minutes=5)
    db.flush()

    revisione.scadenze(db, PRIMA_DELL_INIZIO)

    db.refresh(ferma)
    db.refresh(viva)
    assert ferma.stato == "generazione_fallita"
    assert viva.stato == "in_generazione"
    errore = db.scalar(
        select(ErroreGenerazione).where(ErroreGenerazione.campagna_id == ferma.id)
    )
    assert errore.tipo == "temporaneo"


def test_due_tick_di_seguito_il_secondo_non_cambia_nulla(db):
    """Scadenza e notifica sono idempotenti (CA del task)."""
    campagna = campagna_in_revisione(db)
    piano(db, campagna)
    for _ in range(5):
        post_da_approvare(db, campagna_id=campagna.id, data_ora=POST_PASSATO)
    post_da_approvare(db, campagna_id=campagna.id, data_ora=POST_FUTURO)

    revisione.scadenze(db, ADESSO)
    revisione.scadenze(db, ADESSO)

    db.refresh(campagna)
    assert campagna.stato == "scaduta"
    assert len(_notifiche(db, campagna.id)) == 1
