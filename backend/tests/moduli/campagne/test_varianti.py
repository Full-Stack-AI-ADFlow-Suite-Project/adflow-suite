"""Le tre varianti come comandi (RT-25)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.errori import DatiNonValidi
from app.moduli.campagne import analisi_locale, diagnosi as diag_mod, varianti as var
from app.moduli.campagne import ritocco_catalogo as catalogo
from app.moduli.campagne import service as campagne
from app.moduli.campagne.colore import apri_in_srgb
from app.moduli.campagne.esecutore import Comando, RegoleR42, esegui
from app.moduli.campagne.finestra import Finestra
from app.moduli.campagne.models import Foto
from tests import immagini
from tests.moduli.artigiani.fabbrica import profilo

pytest.importorskip("hypothesis")

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402


def _foto(w=3000, h=2000, soggetto=None) -> SimpleNamespace:
    analisi = {"soggetto_box": soggetto} if soggetto else {}
    return SimpleNamespace(larghezza=w, altezza=h, analisi_ai=analisi, id=1)


def _diag(ai=None, locale=None) -> dict:
    return diag_mod.diagnosi(ai, locale)


def _locale(fasce=None, quadrilateri=(), **misure) -> dict:
    return {
        "misure": {"angolo_linee": None, "caduta_bordi": 0.0, **misure},
        "fasce": dict(fasce or {}),
        "exif": {"zoom_digitale": None},
        "candidati": {"volti": [], "quadrilateri": list(quadrilateri)},
    }


def _ai(**campi) -> dict:
    return {"note": [], "centro": None, "zone": [], "piana": None, "volti": [], **campi}


QUADRO = {
    "id": "Q1",
    "angoli": [[0.1, 0.1], [0.9, 0.12], [0.88, 0.9], [0.12, 0.88]],
    "box": {"x": 0.1, "y": 0.1, "larghezza": 0.8, "altezza": 0.8},
    "area": 0.6,
}


# --- Foto buona --------------------------------------------------------------------


def test_foto_buona_standard_uguale_a_originale_e_spinta_uguale_a_standard():
    comandi = var.varianti(_foto(), _diag(None, _locale()))
    assert comandi["standard"] == comandi["originale"] == comandi["spinta"]
    assert var.uguali(comandi) == {"standard": True, "spinta": True}


def test_la_variante_originale_e_quella_di_r42_e_porta_il_soggetto():
    box = {"x": 0.2, "y": 0.1, "larghezza": 0.5, "altezza": 0.6}
    originale = var.varianti(_foto(soggetto=box), _diag())["originale"]
    assert originale.finestra == RegoleR42(canale="instagram", soggetto_box=box)
    assert (
        originale.luce is None
        and not originale.nitidezza
        and originale.raddrizza is None
    )


# --- Luce --------------------------------------------------------------------------


def test_foto_buia_con_doppia_chiave_corregge_standard_e_spinta_non_l_originale():
    diag = _diag(_ai(note=["scura"]), _locale({"esposizione": "scura"}))
    comandi = var.varianti(_foto(), diag)
    assert comandi["originale"].luce is None
    assert comandi["standard"].luce["esposizione"] == {
        "verso": "su",
        "tetto": catalogo.STANDARD.esposizione_tetto_stop,
        "obiettivo": catalogo.ESPOSIZIONE_OBIETTIVO_L,
    }
    assert (
        comandi["spinta"].luce["esposizione"]["tetto"]
        == catalogo.SPINTA.esposizione_tetto_stop
    )
    assert var.uguali(comandi) == {"standard": False, "spinta": False}


def test_la_spinta_aggiunge_flash_ombre_e_il_bianco_senza_riferimento():
    diag = _diag(
        _ai(note=["controluce", "flash", "calda"]),
        _locale({"ombre_chiuse": "molte", "dominante": "calda"}, caduta_bordi=0.3),
    )
    standard, spinta = (
        var.varianti(_foto(), diag)[n].luce for n in ("standard", "spinta")
    )
    assert standard == {
        "ombre": catalogo.STANDARD.ombre_dose
    }  # flash e bianco senza neutro: spenti
    assert spinta == {
        "bianco": {
            "soggetto": True,
            "tetto": catalogo.SPINTA.bianco_senza_neutro_tetto,
        },
        "ombre": catalogo.SPINTA.ombre_dose,
        "flash": catalogo.SPINTA.flash_dose,
    }


def test_il_bianco_con_zona_neutra_c_e_in_standard():
    diag = _diag(
        _ai(note=["calda"], zone=[{"ruolo": "neutro", "b": [41, 71, 6, 4]}]),
        _locale({"dominante": "calda"}),
    )
    bianco = var.varianti(_foto(), diag)["standard"].luce["bianco"]
    assert bianco == {
        "neutro": {"x": 0.41, "y": 0.71, "larghezza": 0.06, "altezza": 0.04},
        "tetto": catalogo.STANDARD.bianco_tetto_canale,
    }


def test_il_soggetto_e_la_regione_di_misura_della_luce():
    box = {"x": 0.2, "y": 0.1, "larghezza": 0.5, "altezza": 0.6}
    diag = _diag(_ai(note=["scura"]), _locale({"esposizione": "scura"}))
    assert var.varianti(_foto(soggetto=box), diag)["standard"].luce["soggetto"] == box


def test_nitidezza_con_la_dose_della_variante():
    diag = _diag(_ai(), _locale({"nitidezza": "bassa"}))
    standard, spinta = (var.varianti(_foto(), diag)[n] for n in ("standard", "spinta"))
    assert standard.nitidezza and spinta.nitidezza
    assert (standard.nitidezza_dose, spinta.nitidezza_dose) == (
        catalogo.STANDARD.nitidezza_dose,
        catalogo.SPINTA.nitidezza_dose,
    )


# --- Geometria ---------------------------------------------------------------------


def test_superficie_q1_raddrizza_standard_e_spinta():
    diag = _diag(_ai(piana="Q1"), _locale(quadrilateri=[QUADRO]))
    comandi = var.varianti(_foto(), diag)
    assert comandi["originale"].raddrizza is None
    assert comandi["standard"].raddrizza["tipo"] == "prospettiva"
    assert (
        comandi["standard"].raddrizza["max"]
        == catalogo.STANDARD.prospettiva_deformazione_max
    )


def test_la_prospettiva_troppo_deformata_per_la_standard_resta_alla_spinta():
    forte = {
        **QUADRO,
        "angoli": [[0.2, 0.1], [0.8, 0.1], [0.95, 0.9], [0.05, 0.9]],
    }  # ~0,37 di deformazione
    diag = _diag(_ai(piana="Q1"), _locale(quadrilateri=[forte]))
    comandi = var.varianti(_foto(), diag)
    assert comandi["standard"].raddrizza is None
    assert comandi["spinta"].raddrizza is None  # oltre il 15% anche per la spinta


def test_la_prospettiva_media_la_regge_solo_la_spinta():
    media = {
        **QUADRO,
        "angoli": [[0.1, 0.1], [0.9, 0.1], [0.97, 0.9], [0.03, 0.9]],
    }  # ~0,1 di deformazione
    diag = _diag(_ai(piana="Q1"), _locale(quadrilateri=[media]))
    comandi = var.varianti(_foto(), diag)
    assert comandi["standard"].raddrizza is None
    assert comandi["spinta"].raddrizza["tipo"] == "prospettiva"


def test_rotazione_fine_dentro_il_tetto_della_variante():
    tre = var.varianti(_foto(), _diag(_ai(note=["storta"]), _locale(angolo_linee=3.0)))
    assert tre["standard"].raddrizza == {"tipo": "rotazione", "gradi": 3.0, "max": 5.0}
    sette = var.varianti(
        _foto(), _diag(_ai(note=["storta"]), _locale(angolo_linee=7.0))
    )
    assert sette["standard"].raddrizza is None  # oltre 5° la standard non tocca
    assert sette["spinta"].raddrizza == {"tipo": "rotazione", "gradi": 7.0, "max": 8.0}


def test_la_rotazione_di_novanta_gradi_c_e_in_tutte_e_tre():
    comandi = var.varianti(_foto(), _diag(_ai(note=["ruota_90"]), _locale()))
    assert {n: c.ruota for n, c in comandi.items()} == {
        "originale": 90,
        "standard": 90,
        "spinta": 90,
    }
    assert (
        comandi["standard"] == comandi["originale"]
    )  # nient'altro: la Standard è l'Originale


# --- Finestra ----------------------------------------------------------------------


def test_avvicinamento_stringe_la_finestra_della_standard_e_ancora_di_piu_la_spinta():
    box = {"x": 0.45, "y": 0.45, "larghezza": 0.08, "altezza": 0.1}
    diag = _diag(_ai(note=["lontana"]), _locale())
    comandi = var.varianti(_foto(4000, 3000, box), diag)
    assert isinstance(comandi["originale"].finestra, RegoleR42)
    standard, spinta = (comandi[n].finestra for n in ("standard", "spinta"))
    assert isinstance(standard, Finestra) and standard.b[2] < 1.0
    assert spinta.b[2] < standard.b[2]


def test_la_finestra_e_nella_foto_dopo_la_rotazione_di_90():
    """Una foto larga girata di 90° diventa alta: il soggetto che era a sinistra sta in alto."""
    box = {"x": 0.05, "y": 0.4, "larghezza": 0.06, "altezza": 0.15}
    diag = _diag(_ai(note=["ruota_90", "lontana"]), _locale())
    finestra = var.varianti(_foto(6000, 4000, box), diag)["standard"].finestra
    assert finestra.b[1] < 0.3  # in cima, dopo la rotazione oraria


def test_dimensioni_del_locale_hanno_la_precedenza_su_quelle_della_foto():
    box = {"x": 0.45, "y": 0.45, "larghezza": 0.08, "altezza": 0.1}
    diag = _diag(_ai(note=["lontana"]), _locale())
    sbagliata = _foto(800, 600, box)  # troppo piccola: nessun avvicinamento
    piccole = var.varianti(sbagliata, diag)
    assert piccole["standard"] == piccole["originale"]  # nessun avvicinamento possibile
    esito = var.varianti(
        sbagliata, diag, {"formato": {"larghezza": 4000, "altezza": 3000}}
    )
    assert esito["standard"].finestra.b[2] < 1.0


def test_screenshot_e_grafica_sono_tutte_e_tre_l_originale():
    diag = _diag(
        _ai(note=["screenshot", "scura", "lontana"]), _locale({"esposizione": "scura"})
    )
    comandi = var.varianti(_foto(), diag)
    assert comandi["standard"] == comandi["spinta"] == comandi["originale"]
    assert comandi["standard"].luce is None


# --- Salvataggio e lettura ---------------------------------------------------------


def test_il_comando_si_salva_e_si_rilegge_uguale():
    diag = _diag(
        _ai(
            note=["scura", "storta", "lontana"],
            zone=[{"ruolo": "tieni", "b": [20, 14, 60, 70]}],
        ),
        _locale({"esposizione": "scura", "nitidezza": "bassa"}, angolo_linee=3.0),
    )
    comandi = var.varianti(
        _foto(4000, 3000, {"x": 0.4, "y": 0.4, "larghezza": 0.15, "altezza": 0.2}), diag
    )
    for comando in comandi.values():
        dato = json.loads(json.dumps(comando.a_dict()))
        assert Comando.da_dict(dato) == comando


@pytest.mark.parametrize(
    "dato",
    [
        {},
        {"versione": "x"},
        {"versione": "x", "ruota": 45},
        {"versione": "x", "ruota": 0, "finestra": {"b": [0]}},
    ],
)
def test_un_comando_salvato_malformato_e_un_errore_di_dati(dato):
    with pytest.raises(DatiNonValidi):
        Comando.da_dict(dato)


def test_ritocco_di_foto_e_un_json_completo():
    diag = _diag(_ai(note=["scura"]), _locale({"esposizione": "scura"}))
    ritocco = var.ritocco_di_foto(_foto(), diag)
    assert json.loads(json.dumps(ritocco)) == ritocco
    assert set(ritocco) == {
        "versione_esecutore",
        "versione_diagnosi",
        "varianti",
        "uguali",
        "privacy",
        "avvisi",
        "scarti",
        "diagnosi",
    }
    assert set(ritocco["varianti"]) == {"originale", "standard", "spinta"}
    assert ritocco["versione_esecutore"] == catalogo.VERSIONE_RITOCCO


def test_disponibilita_senza_varianti_salvate_solo_originale_e_standard_uguale():
    assert var.disponibilita(_foto()) == (["originale", "standard"], ["standard"])


def test_disponibilita_la_spinta_si_spegne_se_uguale_alla_standard():
    foto = _foto()
    foto.analisi_ai["ritocco"] = var.ritocco_di_foto(
        foto, _diag(_ai(note=["scura"]), _locale({"esposizione": "scura"}))
    )
    assert var.disponibilita(foto) == (["originale", "standard", "spinta"], [])
    foto.analisi_ai["ritocco"] = var.ritocco_di_foto(foto, _diag(None, _locale()))
    assert var.disponibilita(foto) == (
        ["originale", "standard"],
        ["standard", "spinta"],
    )


def test_comando_per_variante():
    foto = _foto()
    assert var.comando_per_variante(foto, "facebook", "spinta").finestra == RegoleR42(
        canale="facebook"
    )
    foto.analisi_ai["ritocco"] = var.ritocco_di_foto(
        foto, _diag(_ai(note=["scura"]), _locale({"esposizione": "scura"}))
    )
    assert (
        var.comando_per_variante(foto, "instagram", "standard").luce["esposizione"][
            "tetto"
        ]
        == 0.5
    )
    assert (
        var.comando_per_variante(foto, "instagram", None).luce is not None
    )  # senza scelta, la Standard
    assert (
        var.comando_per_variante(foto, "facebook", "originale").finestra.canale
        == "facebook"
    )
    with pytest.raises(DatiNonValidi):
        var.comando_per_variante(foto, "instagram", "ottima")


# --- Regressione: le foto buone escono invariate -----------------------------------


def _locale_vero(dati: bytes):
    copia = apri_in_srgb(dati, lato_max=2048)
    locale, _, _ = analisi_locale.analisi_locale(dati, copia)
    return locale


def _buone():
    return [
        immagini.gradiente((1800, 1350), (70, 80, 90), (190, 180, 170), verticale=True),
        immagini.gradiente((2000, 1000), (90, 100, 80), (200, 190, 180)),
        immagini.con_dominante(
            immagini.gradiente((1600, 1600), (80, 80, 80), (180, 180, 180)), (4, 2, 0)
        ),
    ]


@pytest.mark.parametrize("indice", range(3))
def test_le_foto_buone_escono_dalla_standard_con_delta_e_sotto_uno_e_lo_stesso_rapporto(
    indice,
):
    img = _buone()[indice]
    dati = immagini.jpeg_qualita(
        Image.blend(img, immagini.nitida(img.size, 4), 0.45), 95
    )
    locale = _locale_vero(dati)
    diag = diag_mod.diagnosi(None, locale)  # nessuna segnalazione dell'AI
    foto = _foto(*img.size)
    comandi = var.varianti(foto, diag, locale)
    originale = immagini.apri(esegui(dati, comandi["originale"]))
    standard = immagini.apri(esegui(dati, comandi["standard"]))
    assert standard.size == originale.size
    assert immagini.delta_e(originale, standard) < 1.0


# --- Proprietà: i comandi sono sempre eseguibili ----------------------------------

note = st.lists(st.sampled_from(list(catalogo.NOTE)), max_size=5, unique=True)
fasce_casuali = st.fixed_dictionaries(
    {},
    optional={
        "nitidezza": st.just("bassa"),
        "esposizione": st.sampled_from(["scura", "chiara"]),
        "luci_bruciate": st.sampled_from(["poche", "molte"]),
        "ombre_chiuse": st.sampled_from(["poche", "molte"]),
        "dominante": st.sampled_from(["calda", "fredda", "verde", "magenta"]),
    },
)
riquadro = st.tuples(
    st.integers(0, 90), st.integers(0, 90), st.integers(1, 40), st.integers(1, 40)
)


@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    st.integers(300, 900),
    st.integers(300, 900),
    note,
    fasce_casuali,
    st.one_of(st.none(), st.floats(-9.0, 9.0)),
    st.lists(riquadro, max_size=2),
    st.lists(riquadro, max_size=2),
    st.one_of(st.none(), riquadro),
    st.booleans(),
)
def test_proprieta_i_comandi_sono_sempre_eseguibili(
    w, h, note, fasce, angolo, tieni, togli, soggetto, con_quadro
):
    zone = [
        {"ruolo": "tieni", "b": list(b)}
        for b in tieni
        if b[0] + b[2] <= 100 and b[1] + b[3] <= 100
    ]
    zone += [
        {"ruolo": "togli", "b": list(b)}
        for b in togli
        if b[0] + b[2] <= 100 and b[1] + b[3] <= 100
    ]
    ai = _ai(note=note, zone=zone, piana="Q1" if con_quadro else None)
    diag = _diag(
        ai,
        _locale(
            fasce, [QUADRO] if con_quadro else [], angolo_linee=angolo, caduta_bordi=0.2
        ),
    )
    box = None
    if (
        soggetto
        and soggetto[0] + soggetto[2] <= 100
        and soggetto[1] + soggetto[3] <= 100
    ):
        box = {
            "x": soggetto[0] / 100,
            "y": soggetto[1] / 100,
            "larghezza": soggetto[2] / 100,
            "altezza": soggetto[3] / 100,
        }
    dati = immagini.jpeg_qualita(
        immagini.gradiente((w, h), (10, 20, 30), (210, 190, 170)), 85
    )
    for comando in var.varianti(_foto(w, h, box), diag).values():
        uscita = immagini.apri(esegui(dati, comando))
        assert min(uscita.size) == 1080
        assert 0.8 - 0.02 <= uscita.width / uscita.height <= 1.91 + 0.02


# --- Il render usa la variante scelta ----------------------------------------------


@pytest.fixture
def archivio():
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


def _foto_vera(db, archivio, analisi=None) -> Foto:
    scura = immagini.gradiente((1600, 1200), (5, 5, 8), (70, 60, 55), verticale=True)
    record = Foto(
        profilo_id=profilo(db).id,
        file=archivio.salva(immagini.jpeg_qualita(scura, 95), "jpg"),
        mime="image/jpeg",
        larghezza=1600,
        altezza=1200,
        origine="caricata",
        da_usare=False,
        pubblicata_su={},
        analisi_ai=analisi,
    )
    db.add(record)
    db.flush()
    return record


def test_rendi_per_canale_usa_la_variante_scelta(db, archivio):
    foto = _foto_vera(db, archivio)
    foto.analisi_ai = {
        "ritocco": var.ritocco_di_foto(
            foto, _diag(_ai(note=["scura"]), _locale({"esposizione": "scura"})), None
        )
    }
    db.flush()
    chiavi = {
        v: campagne.rendi_per_canale(db, foto.id, "instagram", {"variante": v})
        for v in ("originale", "standard", "spinta")
    }
    assert len(set(chiavi.values())) == 3
    media = lambda v: np.asarray(
        immagini.apri(campagne.leggi_render(foto.id, chiavi[v]))
    ).mean()  # noqa: E731
    assert media("originale") < media("standard") < media("spinta")
    assert (
        campagne.rendi_per_canale(db, foto.id, "instagram", None) == chiavi["standard"]
    )


def test_rendi_per_canale_senza_varianti_salvate_e_l_originale(db, archivio):
    foto = _foto_vera(db, archivio)
    assert campagne.rendi_per_canale(
        db, foto.id, "instagram", {"variante": "spinta"}
    ) == campagne.rendi_per_canale(db, foto.id, "instagram", {"variante": "originale"})


def test_le_zone_di_privacy_si_oscurano_se_accese(db, archivio):
    foto = _foto_vera(db, archivio)
    foto.analisi_ai = {
        "ritocco": {
            "varianti": {},
            "privacy": [
                {"id": "z1", "origine": "ai", "ruolo": "targa", "b": [10, 10, 40, 40]}
            ],
        }
    }
    db.flush()
    senza = campagne.rendi_per_canale(
        db, foto.id, "instagram", {"variante": "originale"}
    )
    tutte = campagne.rendi_per_canale(
        db, foto.id, "instagram", {"variante": "originale", "privacy": True}
    )
    una = campagne.rendi_per_canale(
        db, foto.id, "instagram", {"variante": "originale", "privacy": ["z1"]}
    )
    altra = campagne.rendi_per_canale(
        db, foto.id, "instagram", {"variante": "originale", "privacy": ["z9"]}
    )
    assert tutte == una and tutte != senza and altra == senza
