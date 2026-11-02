"""La modifica a mano di un post è una versione `modifica_operatore`."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.core.errori import DatiNonValidi, NonTrovato, StatoNonValido
from app.moduli.contenuti.models import VersionePost, VersionePostFoto
from app.moduli.contenuti.service import modifica_post
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.campagne.fabbrica import campagna_in_revisione, campagna_sospesa
from tests.moduli.contenuti.fabbrica import post_approvato, post_da_approvare

ADESSO = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)


def _versioni(db, post):
    return db.scalar(
        select(func.count())
        .select_from(VersionePost)
        .where(VersionePost.post_id == post.id)
    )


def test_ca64_nasce_una_versione_con_autore_validata_e_foto_uguali(db):
    operatore = utente(db, "operatore")
    uno = post_da_approvare(db, controllato_da=operatore.id, controllato_il=ADESSO)
    prima = uno.versione_corrente
    nuova = modifica_post(
        db, uno.id, operatore.id, "  Testo nuovo  ", ["#Legno", " pezzounico "], ADESSO
    )
    assert uno.versione_corrente is nuova
    assert (nuova.numero, nuova.tipo_intervento, nuova.autore_id) == (
        2,
        "modifica_operatore",
        operatore.id,
    )
    assert (nuova.testo, nuova.hashtag) == ("Testo nuovo", ["Legno", "pezzounico"])
    assert nuova.errori_validazione == []
    assert (nuova.provider_ai, nuova.modello_ai, nuova.versione_prompt) == (None,) * 3
    assert [(l.posizione, l.foto_id) for l in nuova.legami_foto] == [
        (l.posizione, l.foto_id) for l in prima.legami_foto
    ]
    assert [v.numero for v in uno.versioni] == [1, 2]
    # La precedente resta com'è (R-02).
    assert (prima.testo, prima.autore_id) == ("Testo di prova", None)
    # Cicli invariati e spunta azzerata.
    assert uno.n_rigenerazioni_testo == 0
    assert (uno.controllato_da, uno.controllato_il) == (None, None)


def test_ca64_con_un_blocco_nessuna_versione_422(db):
    operatore = utente(db, "operatore")
    uno = post_da_approvare(db, controllato_da=operatore.id, controllato_il=ADESSO)
    with pytest.raises(DatiNonValidi):
        modifica_post(db, uno.id, operatore.id, "Fatto a mano, gratis!", [], ADESSO)
    assert _versioni(db, uno) == 1
    assert uno.controllato_da == operatore.id


def test_il_testo_vuoto_e_un_blocco(db):
    uno = post_da_approvare(db)
    with pytest.raises(DatiNonValidi):
        modifica_post(db, uno.id, utente(db, "operatore").id, "   ", ["a"], ADESSO)
    assert _versioni(db, uno) == 1


def test_ca64_senza_cambiamenti_nessuna_versione_422(db):
    operatore = utente(db, "operatore")
    uno = post_da_approvare(db)
    with pytest.raises(DatiNonValidi):
        modifica_post(
            db, uno.id, operatore.id, " Testo di prova ", ["#artigianato"], ADESSO
        )
    assert _versioni(db, uno) == 1


def test_cambiare_solo_gli_hashtag_basta(db):
    uno = post_da_approvare(db)
    nuova = modifica_post(
        db, uno.id, utente(db, "operatore").id, "Testo di prova", ["altro"], ADESSO
    )
    assert nuova.hashtag == ["altro"]


def test_un_avviso_si_salva_con_la_versione_e_non_ferma_nulla(db):
    uno = post_da_approvare(db, canale="facebook")
    nuova = modifica_post(db, uno.id, utente(db, "operatore").id, "a" * 501, [], ADESSO)
    assert [e["livello"] for e in nuova.errori_validazione] == ["avviso"]
    assert uno.da_rivedere is False


def test_sblocca_un_post_da_rivedere(db):
    uno = post_da_approvare(db, da_rivedere=True)
    uno.versione_corrente.testo = ""
    modifica_post(db, uno.id, utente(db, "operatore").id, "Testo a posto", [], ADESSO)
    assert uno.da_rivedere is False


def test_ca28_dopo_3_rigenerazioni_la_modifica_resta_ammessa(db):
    uno = post_da_approvare(db, n_rigenerazioni_testo=3)
    modifica_post(db, uno.id, utente(db, "operatore").id, "Testo nuovo", [], ADESSO)
    assert (uno.versione_corrente.numero, uno.n_rigenerazioni_testo) == (2, 3)


def test_ca29_dopo_l_approvazione_entro_15_minuti_409(db):
    uno = post_approvato(db, data_ora=ADESSO + timedelta(minutes=10))
    with pytest.raises(StatoNonValido):
        modifica_post(db, uno.id, utente(db, "operatore").id, "Testo nuovo", [], ADESSO)
    assert _versioni(db, uno) == 1


def test_ca84_dopo_l_approvazione_oltre_15_minuti_nasce_la_versione(db):
    operatore = utente(db, "operatore")
    uno = post_approvato(db, data_ora=ADESSO + timedelta(minutes=16))
    nuova = modifica_post(db, uno.id, operatore.id, "Testo nuovo", ["bottega"], ADESSO)
    assert (nuova.numero, nuova.tipo_intervento, nuova.autore_id) == (
        2,
        "modifica_operatore",
        operatore.id,
    )
    assert uno.stato == "approvato"
    assert _versioni(db, uno) == 2


def test_ca84_anche_in_campagna_sospesa(db):
    uno = post_approvato(
        db,
        campagna_id=campagna_sospesa(db).id,
        data_ora=ADESSO + timedelta(hours=2),
    )
    modifica_post(db, uno.id, utente(db, "operatore").id, "Testo nuovo", [], ADESSO)
    assert _versioni(db, uno) == 2


@pytest.mark.parametrize(
    "stato", ["approvato", "pubblicato", "fallito", "scaduto", "scartato", "annullato"]
)
def test_un_post_non_da_approvare_409(db, stato):
    campagna = campagna_in_revisione(db)
    uno = post_da_approvare(db, campagna_id=campagna.id, stato=stato)
    with pytest.raises(StatoNonValido):
        modifica_post(db, uno.id, utente(db, "operatore").id, "Testo nuovo", [], ADESSO)


def test_con_un_intervento_in_corso_409_ma_non_dopo_10_minuti(db):
    operatore = utente(db, "operatore")
    uno = post_da_approvare(
        db,
        intervento_in_corso="rigenera_totale",
        intervento_dal=ADESSO - timedelta(minutes=9),
    )
    with pytest.raises(StatoNonValido):
        modifica_post(db, uno.id, operatore.id, "Testo nuovo", [], ADESSO)
    uno.intervento_dal = ADESSO - timedelta(minutes=11)
    modifica_post(db, uno.id, operatore.id, "Testo nuovo", [], ADESSO)
    assert uno.versione_corrente.numero == 2


def test_il_validatore_usa_lo_snapshot_della_campagna(db):
    campagna = campagna_in_revisione(db)
    campagna.profilo_snapshot = {
        **campagna.profilo_snapshot,
        "vincoli": "Non parlare di sconti",
    }
    uno = post_da_approvare(db, campagna_id=campagna.id)
    with pytest.raises(DatiNonValidi):
        modifica_post(db, uno.id, utente(db, "operatore").id, "Che sconti!", [], ADESSO)


def test_post_inesistente(db):
    with pytest.raises(NonTrovato):
        modifica_post(db, -1, utente(db, "operatore").id, "Testo", [], ADESSO)


def test_le_foto_della_versione_nuova_sono_righe_proprie(db):
    uno = post_da_approvare(db)
    nuova = modifica_post(
        db, uno.id, utente(db, "operatore").id, "Testo nuovo", [], ADESSO
    )
    legami = db.scalars(
        select(VersionePostFoto).where(VersionePostFoto.versione_id == nuova.id)
    ).all()
    assert len(legami) == 1 and legami[0].versione_id != uno.versioni[0].id
