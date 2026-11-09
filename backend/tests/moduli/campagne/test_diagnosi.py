"""La diagnosi a doppia chiave (RT-24): una riga di test per ogni riga della tabella 10.7."""

from __future__ import annotations

import pytest

from app.moduli.campagne import ritocco_catalogo as catalogo
from app.moduli.campagne.diagnosi import diagnosi

pytest.importorskip("hypothesis")

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402


def _ai(**campi) -> dict:
    dati = {"note": [], "centro": None, "zone": [], "piana": None, "volti": []}
    dati.update(campi)
    return dati


def _locale(fasce=None, volti=(), quadrilateri=(), **misure) -> dict:
    return {
        "versione": "locale-1",
        "misure": {"angolo_linee": None, "caduta_bordi": 0.0, **misure},
        "fasce": dict(fasce or {}),
        "exif": {
            "flash": None,
            "iso": None,
            "zoom_digitale": None,
            "fotocamera": True,
            "software": None,
        },
        "candidati": {"volti": list(volti), "quadrilateri": list(quadrilateri)},
    }


def _scarti(d) -> list[tuple[str, str]]:
    return [(s["correzione"], s["motivo"]) for s in d["scarti"]]


def _volto(codice, x=0.1, y=0.3, w=0.06, h=0.05):
    return {
        "id": codice,
        "box": {"x": x, "y": y, "larghezza": w, "altezza": h},
        "affidabilita": 0.8,
    }


QUADRO = {
    "id": "Q1",
    "angoli": [[0.1, 0.1], [0.9, 0.12], [0.88, 0.9], [0.12, 0.88]],
    "box": {"x": 0.1, "y": 0.1, "larghezza": 0.8, "altezza": 0.8},
    "area": 0.6,
}


# --- Esposizione + -----------------------------------------------------------------


def test_esposizione_su_ai_si_misura_si():
    d = diagnosi(_ai(note=["scura"]), _locale({"esposizione": "scura"}))
    assert d["luce"]["esposizione"] == "su" and d["scarti"] == []


def test_esposizione_su_solo_l_ai_e_uno_scarto():
    d = diagnosi(_ai(note=["scura"]), _locale())
    assert d["luce"]["esposizione"] is None
    assert ("esposizione_su", "ai_si_misura_no") in _scarti(d)


def test_esposizione_su_solo_la_misura_e_uno_scarto():
    d = diagnosi(_ai(), _locale({"esposizione": "scura"}))
    assert d["luce"]["esposizione"] is None
    assert ("esposizione_su", "misura_si_ai_no") in _scarti(
        d
    )  # la vineria buia per scelta


# --- Esposizione − -----------------------------------------------------------------


def test_esposizione_giu_ai_si_misura_si_con_poche_luci_bruciate():
    d = diagnosi(
        _ai(note=["chiara"]),
        _locale({"esposizione": "chiara", "luci_bruciate": "poche"}),
    )
    assert d["luce"]["esposizione"] == "giu"


def test_esposizione_giu_non_con_molte_luci_bruciate():
    d = diagnosi(
        _ai(note=["chiara"]),
        _locale({"esposizione": "chiara", "luci_bruciate": "molte"}),
    )
    assert d["luce"]["esposizione"] is None
    assert ("esposizione_giu", "ai_si_misura_no") in _scarti(d)


def test_esposizione_giu_solo_l_ai():
    d = diagnosi(_ai(note=["chiara"]), _locale())
    assert d["luce"]["esposizione"] is None and (
        "esposizione_giu",
        "ai_si_misura_no",
    ) in _scarti(d)


# --- Bianco ------------------------------------------------------------------------


def test_bianco_con_dominante_ai_e_misura_concordi_e_una_zona_neutra():
    d = diagnosi(
        _ai(note=["calda"], zone=[{"ruolo": "neutro", "b": [41, 71, 6, 4]}]),
        _locale({"dominante": "calda"}),
    )
    assert d["luce"]["bianco"] == {
        "dominante": "calda",
        "neutro": [41, 71, 6, 4],
        "senza_neutro": False,
    }
    assert d["neutro"] == [41, 71, 6, 4]


def test_bianco_senza_zona_neutra_lo_dice():
    d = diagnosi(_ai(note=["fredda"]), _locale({"dominante": "fredda"}))
    assert (
        d["luce"]["bianco"]["senza_neutro"] is True
        and d["luce"]["bianco"]["neutro"] is None
    )


def test_bianco_se_la_misura_dice_un_altra_dominante_e_uno_scarto():
    d = diagnosi(_ai(note=["calda"]), _locale({"dominante": "fredda"}))
    assert d["luce"]["bianco"] is None and ("bianco", "ai_si_misura_no") in _scarti(d)


def test_bianco_solo_la_misura():
    d = diagnosi(_ai(), _locale({"dominante": "verde"}))
    assert d["luce"]["bianco"] is None and ("bianco", "misura_si_ai_no") in _scarti(d)


# --- Ombre -------------------------------------------------------------------------


@pytest.mark.parametrize("fascia", ["poche", "molte"])
def test_ombre_controluce_e_ombre_chiuse(fascia):
    d = diagnosi(_ai(note=["controluce"]), _locale({"ombre_chiuse": fascia}))
    assert d["luce"]["ombre"] is True


def test_ombre_solo_l_ai_e_solo_la_misura():
    assert ("ombre", "ai_si_misura_no") in _scarti(
        diagnosi(_ai(note=["controluce"]), _locale())
    )
    d = diagnosi(_ai(), _locale({"ombre_chiuse": "molte"}))
    assert d["luce"]["ombre"] is False and ("ombre", "misura_si_ai_no") in _scarti(d)


# --- Flash -------------------------------------------------------------------------


def test_flash_con_la_caduta_ai_bordi():
    assert (
        diagnosi(_ai(note=["flash"]), _locale(caduta_bordi=0.3))["luce"]["flash"]
        is True
    )


def test_flash_senza_caduta_e_uno_scarto():
    d = diagnosi(_ai(note=["flash"]), _locale(caduta_bordi=0.02))
    assert d["luce"]["flash"] is False and ("flash", "ai_si_misura_no") in _scarti(d)


def test_flash_solo_la_misura():
    d = diagnosi(_ai(), _locale(caduta_bordi=0.3))
    assert d["luce"]["flash"] is False and ("flash", "misura_si_ai_no") in _scarti(d)


# --- Rotazione ---------------------------------------------------------------------


@pytest.mark.parametrize("angolo", [0.5, 3.0, -4.2, 8.0])
def test_rotazione_storta_e_angolo_misurato_tra_mezzo_grado_e_otto(angolo):
    d = diagnosi(_ai(note=["storta"]), _locale(angolo_linee=angolo))
    assert d["raddrizza"] == {"tipo": "rotazione", "gradi": angolo}


@pytest.mark.parametrize("angolo", [0.2, 9.0, -20.0, None])
def test_rotazione_angolo_fuori_misura_e_uno_scarto(angolo):
    d = diagnosi(_ai(note=["storta"]), _locale(angolo_linee=angolo))
    assert d["raddrizza"] is None and ("rotazione", "ai_si_misura_no") in _scarti(d)


def test_rotazione_solo_la_misura():
    d = diagnosi(_ai(), _locale(angolo_linee=3.0))
    assert d["raddrizza"] is None and ("rotazione", "misura_si_ai_no") in _scarti(d)


# --- Prospettiva -------------------------------------------------------------------


def test_prospettiva_con_il_candidato_trovato():
    d = diagnosi(_ai(piana="Q1"), _locale(quadrilateri=[QUADRO]))
    assert d["raddrizza"]["tipo"] == "prospettiva" and d["raddrizza"]["codice"] == "Q1"
    assert d["raddrizza"]["angoli"] == QUADRO["angoli"]


def test_prospettiva_codice_che_non_esiste_e_uno_scarto():
    d = diagnosi(_ai(piana="Q2"), _locale(quadrilateri=[QUADRO]))
    assert d["raddrizza"] is None and (
        "prospettiva",
        "piana_senza_candidato",
    ) in _scarti(d)


def test_prospettiva_senza_locale_e_uno_scarto():
    d = diagnosi(_ai(piana="Q1"), None)
    assert d["raddrizza"] is None


def test_la_prospettiva_vince_sulla_rotazione():
    d = diagnosi(
        _ai(note=["storta"], piana="Q1"),
        _locale(quadrilateri=[QUADRO], angolo_linee=3.0),
    )
    assert d["raddrizza"]["tipo"] == "prospettiva"
    assert ("rotazione", "assorbita_dalla_prospettiva") in _scarti(d)


# --- Nitidezza ---------------------------------------------------------------------


def test_nitidezza_per_una_foto_molle_non_mossa_e_poco_compressa():
    assert diagnosi(_ai(), _locale({"nitidezza": "bassa"}))["nitidezza"] is True
    assert (
        diagnosi(_ai(), _locale({"nitidezza": "bassa", "compressione": "lieve"}))[
            "nitidezza"
        ]
        is True
    )


@pytest.mark.parametrize(
    ("ai_note", "fasce"),
    [
        ([], {}),  # già nitida
        ([], {"nitidezza": "bassa", "compressione": "forte"}),
        (["mossa_forte"], {"nitidezza": "bassa"}),
    ],
)
def test_nitidezza_spenta(ai_note, fasce):
    assert diagnosi(_ai(note=ai_note), _locale(fasce))["nitidezza"] is False


def test_nitidezza_spenta_con_lo_zoom_digitale():
    locale = _locale({"nitidezza": "bassa"})
    locale["exif"]["zoom_digitale"] = 2.0
    assert diagnosi(_ai(), locale)["nitidezza"] is False


# --- Inquadratura e note senza misura ---------------------------------------------


@pytest.mark.parametrize("nota", ["lontana", "decentrata"])
def test_avvicinamento(nota):
    assert diagnosi(_ai(note=[nota]), _locale())["avvicina"] is True


def test_ambiente_avvicina_ma_con_un_tetto():
    d = diagnosi(_ai(note=["ambiente"]), _locale())
    assert d["avvicina"] is True and d["ambiente"] is True


def test_non_tagliare_spegne_avvicinamento_e_intrusi():
    d = diagnosi(
        _ai(
            note=["lontana", "non_tagliare"],
            zone=[{"ruolo": "togli", "b": [0, 62, 12, 38]}],
        ),
        _locale(),
    )
    assert d["avvicina"] is False and d["non_tagliare"] is True and d["togli"] == []


def test_zone_tieni_togli_e_centro_passano():
    d = diagnosi(
        _ai(
            centro=[62, 35],
            zone=[
                {"ruolo": "tieni", "b": [20, 14, 60, 70]},
                {"ruolo": "togli", "b": [0, 62, 12, 38]},
            ],
        ),
        _locale(),
    )
    assert (d["centro"], d["tieni"], d["togli"]) == (
        [62, 35],
        [[20, 14, 60, 70]],
        [[0, 62, 12, 38]],
    )


@pytest.mark.parametrize("nota", ["ruota_90", "ruota_180", "ruota_270"])
def test_rotazione_di_novanta_gradi_solo_dall_ai(nota):
    assert diagnosi(_ai(note=[nota]), _locale())["ruota"] == int(nota.split("_")[1])


def test_senza_note_di_rotazione_ruota_e_zero():
    assert diagnosi(_ai(note=["scura"]), _locale())["ruota"] == 0


@pytest.mark.parametrize("nota", ["screenshot", "grafica"])
def test_screenshot_e_grafica_solo_originale(nota):
    d = diagnosi(
        _ai(note=[nota, "scura", "lontana"]),
        _locale({"esposizione": "scura"}, angolo_linee=3.0),
    )
    assert d["solo_originale"] is True
    assert (
        d["luce"]["esposizione"] is None
        and d["avvicina"] is False
        and d["raddrizza"] is None
    )
    assert nota in d["avvisi"] and ("correzioni", "solo_originale") in _scarti(d)


@pytest.mark.parametrize(
    ("nota", "avviso"),
    [
        ("riflessi_bordi", "riflessi_ai_bordi"),
        ("riflessi_soggetto", "riflessi_sul_soggetto"),
        ("mossa_lieve", "foto_mossa_lieve"),
        ("mossa_forte", "foto_mossa_forte"),
        ("foto_di_foto", "foto_di_foto"),
        ("marchi", "marchi_di_altre_aziende"),
    ],
)
def test_le_note_che_sono_solo_avvisi(nota, avviso):
    d = diagnosi(_ai(note=[nota]), _locale())
    assert avviso in d["avvisi"]
    assert d["luce"] == {
        "esposizione": None,
        "bianco": None,
        "ombre": False,
        "flash": False,
    }
    assert d["avvicina"] is False and d["raddrizza"] is None


def test_compressione_forte_e_un_avviso():
    assert (
        "compressione_forte"
        in diagnosi(_ai(), _locale({"compressione": "forte"}))["avvisi"]
    )


def test_una_foto_pulita_non_ha_correzioni_ne_scarti():
    d = diagnosi(None, _locale())
    assert d["luce"] == {
        "esposizione": None,
        "bianco": None,
        "ombre": False,
        "flash": False,
    }
    assert (d["avvicina"], d["raddrizza"], d["nitidezza"], d["ruota"], d["privacy"], d["avvisi"], d["scarti"]) == (
        False, None, False, 0, [], [], [],
    )  # fmt: skip
    assert d["versione"] == catalogo.VERSIONE_DIAGNOSI


# --- Privacy -----------------------------------------------------------------------


def test_i_volti_non_citati_valgono_cliente_e_si_propone_la_zona():
    d = diagnosi(_ai(), _locale(volti=[_volto("V1"), _volto("V2", x=0.6)]))
    assert [(z["id"], z["origine"], z["ruolo"]) for z in d["privacy"]] == [
        ("z1", "V1", "cliente"),
        ("z2", "V2", "cliente"),
    ]
    assert d["privacy"][0]["b"] == [10, 30, 6, 5]


def test_staff_e_non_volto_sono_esclusi_il_minore_resta():
    d = diagnosi(
        _ai(volti=["V1 staff", "V2 no", "V3 minore"]),
        _locale(volti=[_volto("V1"), _volto("V2", x=0.3), _volto("V3", x=0.6)]),
    )
    assert [(z["origine"], z["ruolo"]) for z in d["privacy"]] == [("V3", "minore")]


def test_le_zone_volto_e_le_scritte_private_si_aggiungono():
    d = diagnosi(
        _ai(
            zone=[
                {"ruolo": "volto", "b": [83, 40, 4, 5]},
                {"ruolo": "nome", "b": [30, 60, 10, 4]},
                {"ruolo": "indirizzo", "b": [30, 70, 10, 4]},
                {"ruolo": "targa", "b": [50, 80, 8, 3]},
                {"ruolo": "dati", "b": [60, 10, 20, 8]},
                {"ruolo": "tieni", "b": [1, 1, 5, 5]},
            ]
        ),
        _locale(),
    )
    assert [(z["origine"], z["ruolo"]) for z in d["privacy"]] == [
        ("ai", "volto"), ("ai", "nome"), ("ai", "indirizzo"), ("ai", "targa"), ("ai", "dati"),
    ]  # fmt: skip
    assert [z["id"] for z in d["privacy"]] == ["z1", "z2", "z3", "z4", "z5"]


def test_un_volto_dell_ai_sullo_stesso_posto_di_un_candidato_non_si_ripete():
    d = diagnosi(
        _ai(zone=[{"ruolo": "volto", "b": [10, 30, 6, 5]}]),
        _locale(volti=[_volto("V1")]),
    )
    assert [z["origine"] for z in d["privacy"]] == ["V1"]


def test_la_privacy_si_propone_anche_senza_correzioni_e_per_uno_screenshot():
    d = diagnosi(
        _ai(note=["screenshot"], zone=[{"ruolo": "dati", "b": [60, 10, 20, 8]}]),
        _locale(),
    )
    assert d["solo_originale"] is True and [z["ruolo"] for z in d["privacy"]] == [
        "dati"
    ]


# --- Senza AI o senza misure -------------------------------------------------------


def test_senza_misure_nessuna_correzione_e_gli_scarti_lo_dicono():
    d = diagnosi(_ai(note=["scura", "storta", "flash", "controluce"]), None)
    assert d["luce"]["esposizione"] is None and d["raddrizza"] is None
    assert {m for _, m in _scarti(d)} == {"senza_misure"}


def test_senza_ai_nessuna_correzione():
    d = diagnosi(
        None, _locale({"esposizione": "scura", "dominante": "calda"}, angolo_linee=3.0)
    )
    assert d["luce"]["esposizione"] is None and d["raddrizza"] is None
    assert {m for _, m in _scarti(d)} == {"misura_si_ai_no"}


def test_e_json():
    import json

    d = diagnosi(
        _ai(
            note=["scura", "storta"],
            zone=[{"ruolo": "volto", "b": [1, 2, 3, 4]}],
            piana="Q1",
        ),
        _locale(
            {"esposizione": "scura"},
            angolo_linee=2.0,
            quadrilateri=[QUADRO],
            volti=[_volto("V1")],
        ),
    )
    assert json.loads(json.dumps(d)) == d


# --- Proprietà ---------------------------------------------------------------------

qualunque = st.recursive(
    st.none()
    | st.booleans()
    | st.integers(-1000, 1000)
    | st.floats(allow_nan=False)
    | st.text(max_size=10),
    lambda figli: st.lists(figli, max_size=4)
    | st.dictionaries(st.text(max_size=8), figli, max_size=4),
    max_leaves=10,
)


@settings(max_examples=300, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(qualunque, qualunque)
def test_nessuna_eccezione_con_risposte_e_misure_qualsiasi(ai, locale):
    d = diagnosi(ai, locale)
    assert d["versione"] == catalogo.VERSIONE_DIAGNOSI
    assert isinstance(d["scarti"], list) and isinstance(d["privacy"], list)


note = st.lists(st.sampled_from(list(catalogo.NOTE)), max_size=6, unique=True)
fasce_casuali = st.fixed_dictionaries(
    {},
    optional={
        "nitidezza": st.sampled_from(["bassa"]),
        "esposizione": st.sampled_from(["scura", "chiara"]),
        "luci_bruciate": st.sampled_from(["poche", "molte"]),
        "ombre_chiuse": st.sampled_from(["poche", "molte"]),
        "dominante": st.sampled_from(["calda", "fredda", "verde", "magenta"]),
        "compressione": st.sampled_from(["forte", "lieve"]),
    },
)


@settings(max_examples=300, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(note, fasce_casuali, st.one_of(st.none(), st.floats(-30, 30)), st.floats(0, 1))
def test_proprieta_una_sola_chiave_non_corregge_mai(note, fasce, angolo, caduta):
    d = diagnosi(
        _ai(note=note), _locale(fasce, angolo_linee=angolo, caduta_bordi=caduta)
    )
    luce = d["luce"]
    if luce["esposizione"] == "su":
        assert "scura" in note and fasce.get("esposizione") == "scura"
    if luce["esposizione"] == "giu":
        assert "chiara" in note and fasce.get("esposizione") == "chiara"
    if luce["bianco"]:
        assert (
            luce["bianco"]["dominante"] in note
            and fasce.get("dominante") == luce["bianco"]["dominante"]
        )
    if luce["ombre"]:
        assert "controluce" in note and fasce.get("ombre_chiuse")
    if luce["flash"]:
        assert "flash" in note and caduta >= catalogo.DIAGNOSI_FLASH_CADUTA_MIN
    if d["raddrizza"] and d["raddrizza"]["tipo"] == "rotazione":
        assert "storta" in note and catalogo.ROTAZIONE_MIN_GRADI <= abs(angolo) <= 8.0
    if d["solo_originale"]:
        assert (
            d["raddrizza"] is None and not d["avvicina"] and luce["esposizione"] is None
        )
