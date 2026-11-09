"""Lo schema compatto del ritocco: contratto con il catalogo e validatori morbidi (RT-20)."""

from __future__ import annotations

import json
from typing import get_args

import pytest

from app.adapters.ai import schemi
from app.adapters.ai.schemi import (
    AnalisiFoto,
    Nota,
    RispostaAnalisi,
    Ritocco,
    RuoloZona,
    Zona,
    box_centesimi_valido,
    punto_centesimi_valido,
    riquadro_da_centesimi,
)
from app.moduli.campagne import ritocco_catalogo as catalogo

pytest.importorskip("hypothesis")

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402


# --- Il contratto con il catalogo --------------------------------------------------


def test_le_note_dello_schema_sono_quelle_del_catalogo_nello_stesso_ordine():
    assert list(get_args(Nota)) == list(catalogo.NOTE)


def test_i_ruoli_delle_zone_dello_schema_sono_quelli_del_catalogo():
    assert list(get_args(RuoloZona)) == list(catalogo.RUOLI_ZONA)


def test_i_conflitti_dello_schema_sono_quelli_del_catalogo():
    assert set(schemi.NOTE_IN_CONFLITTO) == set(catalogo.NOTE_IN_CONFLITTO)


def test_lo_schema_passato_al_provider_ha_tutti_i_campi_obbligatori():
    schema = RispostaAnalisi.model_json_schema()
    analisi = schema["$defs"]["AnalisiFoto"]
    assert set(analisi["required"]) == set(analisi["properties"])
    ritocco = schema["$defs"]["Ritocco"]
    assert set(ritocco["required"]) == set(ritocco["properties"])
    assert set(schema["$defs"]["Zona"]["required"]) == {"ruolo", "b"}
    # l'enum delle note arriva al modello con tutti i codici
    assert set(ritocco["properties"]["note"]["items"]["enum"]) == set(catalogo.NOTE)


def test_i_campi_tolti_non_ci_sono_piu():
    campi = set(AnalisiFoto.model_fields)
    assert {"persone_riconoscibili", "marchi_visibili"}.isdisjoint(campi)
    assert {"soggetto_box", "ritocco"} <= campi


# --- Riquadri e punti --------------------------------------------------------------


@pytest.mark.parametrize(
    ("valore", "atteso"),
    [
        ([0, 0, 100, 100], [0, 0, 100, 100]),
        ([20, 10, 60, 70], [20, 10, 60, 70]),
        ([20.0, 10.0, 60.0, 70.0], [20, 10, 60, 70]),
        ((5, 5, 10, 10), [5, 5, 10, 10]),
        ([50, 10, 80, 50], None),  # esce a destra
        ([10, 50, 50, 60], None),  # esce in basso
        ([-1, 10, 50, 50], None),
        ([10, 10, 0, 50], None),
        ([101, 0, 1, 1], None),
        ([10, 10, 50], None),
        ([10, 10, 50, 50, 1], None),
        ([10.5, 10, 50, 50], None),
        ([True, 10, 50, 50], None),
        (["10", 10, 50, 50], None),
        ({"x": 0.1}, None),
        ("riquadro", None),
        (None, None),
    ],
)
def test_box_in_centesimi(valore, atteso):
    assert box_centesimi_valido(valore) == atteso


@pytest.mark.parametrize(
    ("valore", "atteso"),
    [
        ([0, 0], [0, 0]),
        ([62, 35], [62, 35]),
        ([100, 100], [100, 100]),
        ([101, 5], None),
        ([-1, 5], None),
        ([5], None),
        ([5, 5, 5], None),
        ([1.5, 2], None),
        ([True, 1], None),
        (None, None),
        ("x", None),
    ],
)
def test_punto_in_centesimi(valore, atteso):
    assert punto_centesimi_valido(valore) == atteso


def test_il_riquadro_torna_nel_formato_di_oggi():
    assert riquadro_da_centesimi([20, 10, 60, 70]) == {
        "x": 0.2,
        "y": 0.1,
        "larghezza": 0.6,
        "altezza": 0.7,
    }
    assert riquadro_da_centesimi([20, 10, 100, 70]) is None


# --- Il ritocco, validato in modo morbido ------------------------------------------


def _ritocco(**campi) -> dict:
    dati = {"note": [], "centro": None, "zone": [], "piana": None, "volti": []}
    dati.update(campi)
    return dati


def test_un_ritocco_buono_passa_com_e():
    dati = _ritocco(
        note=["ambiente", "mossa_lieve"],
        centro=[62, 35],
        zone=[
            {"ruolo": "neutro", "b": [41, 71, 6, 4]},
            {"ruolo": "volto", "b": [83, 40, 4, 5]},
        ],
        piana="Q1",
        volti=["V2 staff", "V3 minore", "V4 no"],
    )
    r = Ritocco.model_validate(dati)
    assert r.model_dump() == dati


def test_note_sconosciute_si_scartano_i_doppioni_pure():
    r = Ritocco.model_validate(
        _ritocco(note=["scura", "inventata", "scura", 3, None, "marchi"])
    )
    assert r.note == ["scura", "marchi"]


@pytest.mark.parametrize(
    ("note", "atteso"),
    [
        (["scura", "chiara"], []),
        (["scura", "chiara", "marchi"], ["marchi"]),
        (["mossa_lieve", "mossa_forte", "storta"], ["storta"]),
        (["calda", "fredda"], []),
        (["verde", "magenta"], []),
        (["calda", "verde"], ["calda", "verde"]),  # assi diversi: non in conflitto
        (["ruota_90", "ruota_180"], []),
        (["ruota_90", "ruota_180", "ruota_270", "lontana"], ["lontana"]),
        (["ruota_270"], ["ruota_270"]),
    ],
)
def test_le_note_in_conflitto_si_scartano_tutte(note, atteso):
    assert Ritocco.model_validate(_ritocco(note=note)).note == atteso


def test_le_note_non_sono_piu_di_otto():
    note = list(catalogo.NOTE)[:5] + [
        "marchi",
        "flash",
        "controluce",
        "ambiente",
        "lontana",
    ]
    assert len(Ritocco.model_validate(_ritocco(note=note)).note) == schemi.MAX_NOTE


@pytest.mark.parametrize("centro", [[101, 5], [5], "x", [1.5, 2], None, {"x": 1}])
def test_centro_non_valido_vale_none(centro):
    assert Ritocco.model_validate(_ritocco(centro=centro)).centro is None


def test_le_zone_non_valide_si_scartano_le_buone_restano():
    zone = [
        {"ruolo": "tieni", "b": [20, 14, 60, 70]},
        {"ruolo": "sconosciuto", "b": [1, 1, 5, 5]},
        {"ruolo": "togli", "b": [90, 90, 20, 20]},
        {"ruolo": "togli", "b": [0, 62, 12, 38]},
        {"b": [1, 1, 5, 5]},
        "zona",
        None,
    ]
    r = Ritocco.model_validate(_ritocco(zone=zone))
    assert [(z.ruolo, z.b) for z in r.zone] == [
        ("tieni", [20, 14, 60, 70]),
        ("togli", [0, 62, 12, 38]),
    ]


def test_le_zone_non_sono_piu_di_otto():
    zone = [{"ruolo": "tieni", "b": [i, i, 5, 5]} for i in range(12)]
    assert len(Ritocco.model_validate(_ritocco(zone=zone)).zone) == schemi.MAX_ZONE


def test_zone_che_non_e_una_lista_vale_vuota():
    assert Ritocco.model_validate(_ritocco(zone="no")).zone == []


@pytest.mark.parametrize("piana", ["Q1", " Q2 "])
def test_superficie_buona(piana):
    assert Ritocco.model_validate(_ritocco(piana=piana)).piana == piana.strip()


@pytest.mark.parametrize("piana", ["q1", "Q", "V1", "Q100", "1", "Q1 Q2", 1, [], ""])
def test_superficie_malformata_vale_none(piana):
    assert Ritocco.model_validate(_ritocco(piana=piana)).piana is None


def test_i_volti_nel_formato_vn_ruolo_gli_altri_si_scartano():
    volti = [
        "V1 staff",
        "V2  minore",
        "V3 no",
        "V4 cliente",
        "v5 staff",
        "V6",
        "staff V7",
        "V8 staff extra",
        7,
        None,
        "V10 staff",
    ]
    assert Ritocco.model_validate(_ritocco(volti=volti)).volti == [
        "V1 staff",
        "V2 minore",
        "V3 no",
        "V10 staff",
    ]


def test_i_volti_non_sono_piu_di_dodici():
    volti = [f"V{i} staff" for i in range(1, 20)]
    assert len(Ritocco.model_validate(_ritocco(volti=volti)).volti) == schemi.MAX_VOLTI


# --- L'analisi di una foto ---------------------------------------------------------


def _voce(**campi) -> dict:
    dati = dict(
        foto_id=1, soggetto="Un vaso", descrizione="Un vaso rosso.", tipo="pezzo_finito",
        idonea=True, motivo=None, punteggio=4, simile_a=None, soggetto_box=[20, 10, 60, 70], ritocco=None,
    )  # fmt: skip
    dati.update(campi)
    return dati


def test_ritocco_none_e_valido():
    assert AnalisiFoto.model_validate(_voce()).ritocco is None


@pytest.mark.parametrize(
    "ritocco",
    [
        "niente",
        42,
        [],
        {},
        {"note": []},  # mancano campi
        {"note": [], "centro": None, "zone": [], "piana": None},  # manca volti
        {"note": "scura", "centro": None, "zone": [], "piana": None, "volti": []}
        and {"zone": 3},
    ],
)
def test_un_ritocco_malformato_non_e_un_errore_vale_none(ritocco):
    assert AnalisiFoto.model_validate(_voce(ritocco=ritocco)).ritocco is None


def test_un_ritocco_con_campi_morbidi_sbagliati_resta_ma_ripulito():
    ritocco = {
        "note": "scura",
        "centro": "x",
        "zone": 3,
        "piana": 9,
        "volti": "V1 staff",
    }
    r = AnalisiFoto.model_validate(_voce(ritocco=ritocco)).ritocco
    assert r is not None
    assert r.model_dump() == _ritocco()


def test_il_soggetto_box_fuori_misura_vale_none_e_l_analisi_resta():
    assert (
        AnalisiFoto.model_validate(_voce(soggetto_box=[50, 10, 80, 50])).soggetto_box
        is None
    )
    assert AnalisiFoto.model_validate(_voce(soggetto_box=None)).soggetto_box is None


def test_una_risposta_intera_dal_json():
    testo = json.dumps(
        {
            "foto": [
                _voce(),
                _voce(foto_id=2, ritocco=_ritocco(note=["scura"], centro=[50, 50])),
            ]
        }
    )
    risposta = RispostaAnalisi.model_validate_json(testo)
    assert [f.foto_id for f in risposta.foto] == [1, 2]
    assert risposta.foto[1].ritocco.note == ["scura"]


# --- Proprietà: nessuna risposta casuale solleva un'eccezione ----------------------

qualunque = st.recursive(
    st.none()
    | st.booleans()
    | st.integers(-1000, 1000)
    | st.floats(allow_nan=False)
    | st.text(max_size=12),
    lambda figli: st.lists(figli, max_size=5)
    | st.dictionaries(st.text(max_size=8), figli, max_size=5),
    max_leaves=12,
)


@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(qualunque, qualunque, qualunque, qualunque, qualunque, qualunque)
def test_ritocco_casuale_non_solleva(note, centro, zone, piana, volti, soggetto_box):
    voce = _voce(
        soggetto_box=soggetto_box,
        ritocco={
            "note": note,
            "centro": centro,
            "zone": zone,
            "piana": piana,
            "volti": volti,
        },
    )
    analisi = AnalisiFoto.model_validate(voce)
    if analisi.ritocco is not None:
        assert len(analisi.ritocco.zone) <= schemi.MAX_ZONE
        assert all(isinstance(n, str) for n in analisi.ritocco.note)
    assert (
        analisi.soggetto_box is None
        or box_centesimi_valido(analisi.soggetto_box) == analisi.soggetto_box
    )


@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(qualunque)
def test_zona_casuale_non_solleva_fuori_dalla_validazione(valore):
    try:
        Zona.model_validate(valore)
    except Exception as errore:  # noqa: BLE001
        assert errore.__class__.__name__ == "ValidationError"
