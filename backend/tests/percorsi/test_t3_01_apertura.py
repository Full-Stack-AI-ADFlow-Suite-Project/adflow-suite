"""T3-01: apertura dello sprint 3 (schema, firme e fabbriche)."""
import inspect
from datetime import date

import pytest
from app import worker
from app.adapters.ai import AIAdapter
from app.adapters.social import SocialAdapter
from app.core.coda import PROMEMORIA
from app.moduli.accesso import service as accesso
from app.moduli.artigiani import domain as domain_artigiani
from app.moduli.artigiani import service as artigiani
from app.moduli.contenuti import domain as domain_contenuti
from app.moduli.contenuti import service as contenuti
from app.moduli.campagne.models import Foto
from app.moduli.contenuti.models import VersioneFoto
from tests.moduli.artigiani.fabbrica import anagrafica, utente
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare, versione_foto


def test_versione_originale_e_legame_foto_del_post(db):
    campagna = campagna_in_revisione(db)
    post = post_da_approvare(db, campagna_id=campagna.id)
    legame = post.versione_corrente.legami_foto[0]
    originale = db.get(VersioneFoto, legame.versione_foto_id)

    assert originale is not None
    assert (originale.foto_id, originale.numero, originale.origine) == (
        legame.foto_id,
        0,
        "originale",
    )
    assert domain_contenuti.ORIGINI_VERSIONE_FOTO == ("originale", "ritocco_ai")
    assert post.n_ritocchi_foto == 0


def test_fabbrica_versione_foto_rende_un_originale_unico(db):
    campagna = campagna_in_revisione(db)
    post = post_da_approvare(db, campagna_id=campagna.id)
    legame = post.versione_corrente.legami_foto[0]
    originale = db.get(VersioneFoto, legame.versione_foto_id)
    immagine = db.get(Foto, originale.foto_id)
    assert versione_foto(db, immagine) is originale


def test_anagrafica_artigiano_e_valori_iscrizione(db):
    artigiano = utente(db, "artigiano")
    record = anagrafica(db, utente_id=artigiano.id)
    db.expire(record)

    assert record.stato_iscrizione == "attiva"
    assert record.iscritto_il == date(2030, 1, 5)
    assert record.codice.startswith("ART-")
    assert domain_artigiani.STATI_ISCRIZIONE == ("attiva", "sospesa")


@pytest.mark.parametrize(
    ("modulo", "funzione", "parametri"),
    [
        (accesso, "password_provvisoria", ["db", "utente_id"]),
        (artigiani, "account_social", ["db", "profilo_id", "piattaforma"]),
        (artigiani, "anagrafica_di", ["db", "utente_id"]),
        (contenuti, "puo_ritoccare", ["db", "post_id", "adesso"]),
        (
            contenuti,
            "scegli_foto",
            ["db", "post_id", "versione_foto_id", "utente_id", "adesso"],
        ),
        (
            contenuti,
            "cambia_foto",
            ["db", "post_id", "foto_id", "utente_id", "adesso"],
        ),
        (contenuti, "sposta_post", ["db", "post_id", "data_ora", "adesso"]),
        (worker, "promemoria", ["timestamp"]),
        (
            AIAdapter,
            "ritocca_immagine",
            ["self", "immagine", "mime", "nota"],
        ),
        (SocialAdapter, "collega_account", ["self", "piattaforma"]),
    ],
)
def test_firme_dello_sprint_3(modulo, funzione, parametri):
    assert list(inspect.signature(getattr(modulo, funzione)).parameters) == parametri


def test_job_promemoria_ha_il_nome_del_contratto():
    assert PROMEMORIA == "promemoria"
    assert worker.promemoria(0) is None
