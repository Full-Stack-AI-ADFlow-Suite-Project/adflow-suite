"""T2b-31: scarto, scadenza, annullamento, riprogrammazione, spunta e arresto della generazione."""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.errori import DatiNonValidi, NonTrovato, StatoNonValido
from app.moduli.contenuti.service import (
    annulla_post,
    ferma_generazione,
    riprogramma_post,
    scadi_post,
    scarta_post_del_canale,
    scarta_post_della_campagna,
    segna_controllato,
    ultimo_errore,
)
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_in_revisione,
    campagna_inviata,
    campagna_sospesa,
)
from tests.moduli.contenuti.fabbrica import (
    post_approvato,
    post_da_approvare,
    post_fallito,
)

ADESSO = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)
STATI = (
    "da_approvare",
    "approvato",
    "pubblicato",
    "fallito",
    "scaduto",
    "scartato",
    "annullato",
)


def _stati(*post):
    return [uno.stato for uno in post]


# --- scarta_post_della_campagna ---------------------------------------------------


def test_scarta_post_della_campagna_scarta_i_da_approvare_in_ordine_di_data(db):
    campagna = campagna_in_revisione(db)
    tardi = post_da_approvare(
        db, campagna_id=campagna.id, data_ora=ADESSO + timedelta(days=2)
    )
    presto = post_da_approvare(db, campagna_id=campagna.id, data_ora=ADESSO)
    assert scarta_post_della_campagna(db, campagna.id) == [presto, tardi]
    assert _stati(presto, tardi) == ["scartato", "scartato"]


def test_scarta_post_della_campagna_lascia_gli_altri_e_le_altre_campagne(db):
    campagna = campagna_in_revisione(db)
    altra = campagna_in_revisione(db)
    approvato = post_da_approvare(db, campagna_id=campagna.id, stato="approvato")
    scaduto = post_da_approvare(db, campagna_id=campagna.id, stato="scaduto")
    di_altri = post_da_approvare(db, campagna_id=altra.id)
    assert scarta_post_della_campagna(db, campagna.id) == []
    assert _stati(approvato, scaduto, di_altri) == [
        "approvato",
        "scaduto",
        "da_approvare",
    ]


# --- scarta_post_del_canale -------------------------------------------------------


def test_scarta_post_del_canale_scarta_solo_quel_canale(db):
    campagna = campagna_in_revisione(db)
    instagram = post_da_approvare(db, campagna_id=campagna.id, canale="instagram")
    facebook = post_da_approvare(db, campagna_id=campagna.id, canale="facebook")
    assert scarta_post_del_canale(db, campagna.id, "facebook") == [facebook]
    assert _stati(instagram, facebook) == ["da_approvare", "scartato"]


def test_scarta_post_del_canale_non_tocca_i_post_gia_approvati(db):
    campagna = campagna_in_revisione(db)
    approvato = post_da_approvare(
        db, campagna_id=campagna.id, canale="facebook", stato="approvato"
    )
    assert scarta_post_del_canale(db, campagna.id, "facebook") == []
    assert approvato.stato == "approvato"


# --- scadi_post -------------------------------------------------------------------


def test_scadi_post_scade_solo_i_da_approvare_con_la_data_passata(db):
    campagna = campagna_in_revisione(db)
    passato = post_da_approvare(
        db, campagna_id=campagna.id, data_ora=ADESSO - timedelta(minutes=1)
    )
    adesso_preciso = post_da_approvare(db, campagna_id=campagna.id, data_ora=ADESSO)
    futuro = post_da_approvare(
        db, campagna_id=campagna.id, data_ora=ADESSO + timedelta(days=1)
    )
    approvato = post_da_approvare(
        db,
        campagna_id=campagna.id,
        data_ora=ADESSO - timedelta(days=1),
        stato="approvato",
    )
    assert scadi_post(db, campagna.id, ADESSO) == [passato]
    assert _stati(passato, adesso_preciso, futuro, approvato) == [
        "scaduto",
        "da_approvare",
        "da_approvare",
        "approvato",
    ]


def test_scadi_post_due_volte_di_seguito_la_seconda_non_cambia_nulla(db):
    campagna = campagna_in_revisione(db)
    post_da_approvare(db, campagna_id=campagna.id, data_ora=ADESSO - timedelta(hours=1))
    assert len(scadi_post(db, campagna.id, ADESSO)) == 1
    assert scadi_post(db, campagna.id, ADESSO) == []


# --- annulla_post -----------------------------------------------------------------


def test_annulla_post_senza_elenco_annulla_tutti_gli_approvati(db):
    campagna = campagna_attiva(db)
    primo = post_approvato(db, campagna_id=campagna.id)
    secondo = post_approvato(db, campagna_id=campagna.id)
    pubblicato = post_approvato(db, campagna_id=campagna.id, stato="pubblicato")
    assert annulla_post(db, campagna.id) == [primo, secondo]
    assert _stati(primo, secondo, pubblicato) == [
        "annullato",
        "annullato",
        "pubblicato",
    ]


def test_annulla_post_con_elenco_annulla_solo_quelli(db):
    campagna = campagna_sospesa(db)
    scelto = post_approvato(db, campagna_id=campagna.id)
    resta = post_approvato(db, campagna_id=campagna.id)
    assert annulla_post(db, campagna.id, [scelto.id]) == [scelto]
    assert _stati(scelto, resta) == ["annullato", "approvato"]
    assert annulla_post(db, campagna.id, []) == []


@pytest.mark.parametrize("stato", [s for s in STATI if s != "approvato"])
def test_annulla_post_non_tocca_un_post_non_approvato(db, stato):
    """Transizione vietata: solo un post `approvato` può diventare `annullato`."""
    campagna = campagna_attiva(db)
    uno = post_approvato(db, campagna_id=campagna.id, stato=stato)
    assert annulla_post(db, campagna.id, [uno.id]) == []
    assert uno.stato == stato


# --- riprogramma_post -------------------------------------------------------------


def test_riprogramma_post_ca67_dentro_il_periodo_torna_approvato(db):
    uno = post_fallito(db)
    uno.controllato_da = utente(db, "operatore").id
    uno.controllato_il = ADESSO
    nuova = datetime(2030, 1, 10, 9, tzinfo=timezone.utc)
    assert riprogramma_post(db, uno.id, nuova, ADESSO) is uno
    assert (uno.stato, uno.data_ora) == ("approvato", nuova)
    assert (uno.controllato_da, uno.controllato_il) == (None, None)


def test_riprogramma_post_in_campagna_sospesa(db):
    campagna = campagna_sospesa(db)
    uno = post_approvato(db, campagna_id=campagna.id, stato="fallito")
    riprogramma_post(db, uno.id, datetime(2030, 1, 10, 9, tzinfo=timezone.utc), ADESSO)
    assert uno.stato == "approvato"


@pytest.mark.parametrize("stato", [s for s in STATI if s != "fallito"])
def test_riprogramma_post_non_fallito_409(db, stato):
    """Transizione vietata: solo un post `fallito` torna `approvato`."""
    uno = post_approvato(db, stato=stato)
    with pytest.raises(StatoNonValido):
        riprogramma_post(
            db, uno.id, datetime(2030, 1, 10, 9, tzinfo=timezone.utc), ADESSO
        )
    assert uno.stato == stato


def test_riprogramma_post_di_una_campagna_non_attiva_ne_sospesa_409(db):
    campagna = campagna_in_revisione(db)
    uno = post_da_approvare(db, campagna_id=campagna.id, stato="fallito")
    with pytest.raises(StatoNonValido):
        riprogramma_post(
            db, uno.id, datetime(2030, 1, 10, 9, tzinfo=timezone.utc), ADESSO
        )


@pytest.mark.parametrize(
    "nuova",
    [
        datetime(2030, 1, 4, 9, tzinfo=timezone.utc),  # nel passato
        datetime(2030, 1, 5, 12, 14, tzinfo=timezone.utc),  # a meno di 15 minuti
        datetime(2029, 12, 31, 12, tzinfo=timezone.utc),  # prima dell'inizio
        datetime(2030, 2, 1, 12, tzinfo=timezone.utc),  # dopo la fine
        datetime(2030, 1, 10, 9),  # senza fuso orario
    ],
)
def test_riprogramma_post_data_non_ammessa_422(db, nuova):
    uno = post_fallito(db)
    prima = uno.data_ora
    with pytest.raises(DatiNonValidi):
        riprogramma_post(db, uno.id, nuova, ADESSO)
    assert (uno.stato, uno.data_ora) == ("fallito", prima)


def test_riprogramma_post_ammette_il_margine_esatto_e_l_ultimo_giorno(db):
    uno = post_fallito(db)
    riprogramma_post(db, uno.id, ADESSO + timedelta(minutes=15), ADESSO)
    assert uno.stato == "approvato"
    ultimo = post_fallito(db)
    # 22:30 UTC del 31 gennaio sono le 23:30 a Roma: ancora l'ultimo giorno.
    riprogramma_post(
        db, ultimo.id, datetime(2030, 1, 31, 22, 30, tzinfo=timezone.utc), ADESSO
    )
    assert ultimo.stato == "approvato"


def test_riprogramma_post_il_giorno_vale_a_roma_non_in_utc(db):
    uno = post_fallito(db)
    # 23:30 UTC del 31 gennaio sono le 00:30 del 1° febbraio a Roma: fuori.
    with pytest.raises(DatiNonValidi):
        riprogramma_post(
            db, uno.id, datetime(2030, 1, 31, 23, 30, tzinfo=timezone.utc), ADESSO
        )


def test_riprogramma_post_inesistente(db):
    with pytest.raises(NonTrovato):
        riprogramma_post(db, -1, ADESSO + timedelta(days=1), ADESSO)


# --- segna_controllato ------------------------------------------------------------


def test_segna_controllato_ca65_salva_chi_e_quando_e_si_toglie(db):
    operatore = utente(db, "operatore")
    uno = post_da_approvare(db)
    assert segna_controllato(db, uno.id, operatore.id, True, ADESSO) is uno
    assert (uno.controllato_da, uno.controllato_il) == (operatore.id, ADESSO)
    segna_controllato(db, uno.id, operatore.id, False, ADESSO)
    assert (uno.controllato_da, uno.controllato_il) == (None, None)


def test_segna_controllato_ca65_su_un_post_da_rivedere_409(db):
    operatore = utente(db, "operatore")
    uno = post_da_approvare(db, da_rivedere=True)
    with pytest.raises(StatoNonValido):
        segna_controllato(db, uno.id, operatore.id, True, ADESSO)
    assert uno.controllato_da is None


def test_segna_controllato_toglie_la_spunta_anche_a_un_post_da_rivedere(db):
    operatore = utente(db, "operatore")
    uno = post_da_approvare(
        db,
        da_rivedere=True,
        controllato_da=operatore.id,
        controllato_il=ADESSO,
    )
    segna_controllato(db, uno.id, operatore.id, False, ADESSO)
    assert uno.controllato_da is None


def test_segna_controllato_ca29_in_campagna_attiva_409(db):
    operatore = utente(db, "operatore")
    uno = post_approvato(db)
    with pytest.raises(StatoNonValido):
        segna_controllato(db, uno.id, operatore.id, True, ADESSO)


@pytest.mark.parametrize("stato", [s for s in STATI if s != "da_approvare"])
def test_segna_controllato_post_non_da_approvare_409(db, stato):
    operatore = utente(db, "operatore")
    campagna = campagna_in_revisione(db)
    uno = post_da_approvare(db, campagna_id=campagna.id, stato=stato)
    with pytest.raises(StatoNonValido):
        segna_controllato(db, uno.id, operatore.id, True, ADESSO)


def test_segna_controllato_con_un_intervento_in_corso_409_ma_non_dopo_10_minuti(db):
    operatore = utente(db, "operatore")
    uno = post_da_approvare(
        db,
        intervento_in_corso="rigenera_totale",
        intervento_dal=ADESSO - timedelta(minutes=9),
    )
    with pytest.raises(StatoNonValido):
        segna_controllato(db, uno.id, operatore.id, True, ADESSO)
    uno.intervento_dal = ADESSO - timedelta(minutes=11)
    segna_controllato(db, uno.id, operatore.id, True, ADESSO)
    assert uno.controllato_da == operatore.id


def test_segna_controllato_post_inesistente(db):
    with pytest.raises(NonTrovato):
        segna_controllato(db, -1, utente(db, "operatore").id, True, ADESSO)


# --- ferma_generazione ------------------------------------------------------------


@pytest.mark.parametrize(
    ("stato", "tappa"), [("inviata", "avvio"), ("in_generazione", "analisi")]
)
def test_ferma_generazione_ca68_porta_a_generazione_fallita_con_errore_temporaneo(
    db, stato, tappa
):
    campagna = campagna_inviata(db)
    campagna.stato = stato
    ferma_generazione(db, campagna.id, ADESSO)
    assert campagna.stato == "generazione_fallita"
    errore = ultimo_errore(db, campagna.id)
    assert (errore.tipo, errore.tappa, errore.creata_il) == (
        "temporaneo",
        tappa,
        ADESSO,
    )
    assert errore.messaggio


@pytest.mark.parametrize(
    "stato",
    ["bozza", "generazione_fallita", "in_revisione", "attiva", "conclusa", "scaduta"],
)
def test_ferma_generazione_fuori_da_inviata_e_in_generazione_409(db, stato):
    campagna = campagna_inviata(db)
    campagna.stato = stato
    with pytest.raises(StatoNonValido):
        ferma_generazione(db, campagna.id, ADESSO)
    assert campagna.stato == stato
    assert ultimo_errore(db, campagna.id) is None


def test_ferma_generazione_campagna_inesistente(db):
    with pytest.raises(NonTrovato):
        ferma_generazione(db, -1, ADESSO)
