"""T2b-01: apertura dello sprint 2b (tabella, firme e fabbriche)."""
import inspect
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from app.moduli.accesso import service as accesso
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti
from app.moduli.notifiche import domain
from app.moduli.notifiche import service as notifiche
from app.moduli.revisione import service as revisione
from tests.moduli.campagne.fabbrica import (
    campagna_in_revisione,
    campagna_sospesa,
    nota_interna,
)
from tests.moduli.contenuti.fabbrica import post_fallito
from tests.moduli.notifiche.fabbrica import notifica

ORA = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)


def test_la_notifica_nasce_da_inviare_per_email(db):
    nuova = notifica(db)
    db.expire(nuova)
    assert nuova.canale == "email"
    assert nuova.stato_invio == "da_inviare"
    assert nuova.post_id is None
    assert nuova.inviata_il is None
    assert nuova.creata_il is not None


def test_la_notifica_di_un_post_ricorda_il_post(db):
    fallito = post_fallito(db)
    nuova = notifica(db, campagna=None, tipo="post_fallito", post_id=fallito.id)
    db.expire(nuova)
    assert nuova.post_id == fallito.id
    assert (
        db.scalar(
            text("select count(*) from notifica where post_id = :id"),
            {"id": fallito.id},
        )
        == 1
    )


def test_i_tipi_di_notifica_hanno_un_destinatario():
    assert set(domain.TIPI) == set(domain.DESTINATARI)
    assert set(domain.DESTINATARI.values()) == {domain.ARTIGIANO, domain.OPERATORI}
    # CA-55: i quattro eventi che avvisano gli operatori nello sprint 2b.
    for tipo in (
        "campagna_pronta",
        "piano_da_rivedere",
        "generazione_fallita",
        "post_fallito",
    ):
        assert domain.DESTINATARI[tipo] == domain.OPERATORI
    # Respinta e scaduta vanno per email all'artigiano (spec §4).
    for tipo in ("campagna_respinta", "campagna_scaduta"):
        assert domain.DESTINATARI[tipo] == domain.ARTIGIANO
    assert set(domain.TIPI_DI_UN_POST) <= set(domain.TIPI)


@pytest.mark.parametrize(
    ("modulo", "funzione", "parametri"),
    [
        (
            notifiche,
            "crea",
            ["db", "tipo", "campagna_id", "adesso", "artigiano_id", "post_id"],
        ),
        (accesso, "utente", ["db", "utente_id"]),
        (accesso, "operatori", ["db"]),
        (campagne, "campagne_di", ["db", "profilo_id", "stati"]),
        (campagne, "togli_canale", ["db", "campagna", "canale"]),
        (campagne, "ultima_nota", ["db", "campagna_id"]),
        (contenuti, "scarta_post_della_campagna", ["db", "campagna_id"]),
        (contenuti, "scarta_post_del_canale", ["db", "campagna_id", "canale"]),
        (contenuti, "scadi_post", ["db", "campagna_id", "adesso"]),
        (contenuti, "annulla_post", ["db", "campagna_id", "post_ids"]),
        (contenuti, "riprogramma_post", ["db", "post_id", "data_ora", "adesso"]),
        (
            contenuti,
            "segna_controllato",
            ["db", "post_id", "utente_id", "valore", "adesso"],
        ),
        (
            contenuti,
            "modifica_post",
            ["db", "post_id", "utente_id", "testo", "hashtag", "adesso"],
        ),
        (contenuti, "puo_rigenerare", ["db", "post_id", "adesso"]),
        (contenuti, "accendi_intervento", ["db", "post_id", "tipo", "adesso"]),
        (contenuti, "ferma_generazione", ["db", "campagna_id", "adesso"]),
        (revisione, "scadenze", ["db", "adesso"]),
    ],
)
def test_firme_dello_sprint_2b(modulo, funzione, parametri):
    """Le firme di plan §6: chi le scrive e chi le usa parte da queste."""
    firma = inspect.signature(getattr(modulo, funzione))
    assert list(firma.parameters) == parametri


def test_scadenze_per_ora_non_fa_niente(db):
    """Il tick la chiama già: finché T2b-44 non la scrive lascia tutto com'è."""
    record = campagna_in_revisione(db)
    assert revisione.scadenze(db, ORA) is None
    db.expire(record)
    assert record.stato == "in_revisione"


def test_le_fabbriche_dello_sprint_2b(db):
    sospesa = campagna_sospesa(db)
    assert sospesa.stato == "sospesa"
    nota = nota_interna(db, sospesa, nota="Da ricontrollare")
    assert (nota.esito, nota.nota, nota.campagna_id) == (
        "nota",
        "Da ricontrollare",
        sospesa.id,
    )
    fallito = post_fallito(db)
    assert fallito.stato == "fallito"
    assert campagne.campagna(db, fallito.campagna_id).stato == "attiva"
