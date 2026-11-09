"""La preparazione dell'analisi: una decodifica, contesto e `locale` (RT-19)."""

from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.moduli.campagne import analisi_locale, preanalisi
from app.moduli.campagne import service as campagne
from app.moduli.campagne.models import Foto
from tests import immagini
from tests.moduli.artigiani.fabbrica import profilo


@pytest.fixture
def archivio():
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


def _foto(db, archivio, dati: bytes | None, *, file: str | None = None) -> Foto:
    record = Foto(
        profilo_id=profilo(db).id,
        file=file or archivio.salva(dati, "jpg"),
        mime="image/jpeg",
        larghezza=1600,
        altezza=1200,
        origine="caricata",
        da_usare=False,
        pubblicata_su={},
    )
    db.add(record)
    db.flush()
    return record


def _pulita(dimensioni=(1600, 1200)) -> bytes:
    scena = immagini.gradiente(dimensioni, (60, 70, 80), (180, 190, 200))
    return immagini.jpeg_qualita(
        Image.blend(scena, immagini.nitida(dimensioni, 4), 0.5), 95
    )


def _scura_e_molle(dimensioni=(1600, 1200)) -> bytes:
    molle = immagini.sfocata(immagini.nitida(dimensioni, 12), 3.0)
    scura = Image.blend(molle, Image.new("RGB", dimensioni, (0, 0, 0)), 0.88)
    return immagini.jpeg_qualita(scura, 95)


def test_una_sola_decodifica_per_foto(db, archivio, monkeypatch):
    foto = [_foto(db, archivio, _pulita()) for _ in range(3)]
    chiamate: list[int] = []
    originale = analisi_locale.apri_in_srgb

    def spia(dati, *args, **kwargs):
        chiamate.append(1)
        return originale(dati, *args, **kwargs)

    monkeypatch.setattr(analisi_locale, "apri_in_srgb", spia)
    preparate = campagne.prepara_analisi(db, [f.id for f in foto])
    assert len(chiamate) == 3
    assert set(preparate) == {f.id for f in foto}


def test_la_copia_per_l_ai_e_un_jpeg_srgb_da_1024(db, archivio):
    p3 = immagini.tinta_unita((220, 60, 40), (3000, 2000))
    dati = immagini.jpeg_con_exif(p3, profilo=immagini.profilo_icc("p3"))
    (preparata,) = campagne.prepara_analisi(db, [_foto(db, archivio, dati).id]).values()
    copia = immagini.apri(preparata["immagine"])
    assert copia.format == "JPEG" and max(copia.size) == 1024
    medio = np.asarray(copia).reshape(-1, 3).mean(axis=0)
    assert medio == pytest.approx((239, 35, 17), abs=4)  # il pomodoro in sRGB (RT-02)


def test_una_foto_pulita_ha_il_contesto_vuoto(db, archivio):
    (preparata,) = campagne.prepara_analisi(
        db, [_foto(db, archivio, _pulita()).id]
    ).values()
    assert preparata["contesto"] == ""
    assert preparata["locale"] is not None and preparata["locale"]["fasce"] == {}


def test_il_contesto_dice_solo_le_fasce_non_normali(db, archivio):
    (preparata,) = campagne.prepara_analisi(
        db, [_foto(db, archivio, _scura_e_molle()).id]
    ).values()
    contesto = preparata["contesto"]
    assert "scura" in contesto and "nitidezza bassa" in contesto
    assert "\n" not in contesto and "Foto" not in contesto
    assert "chiara" not in contesto and "luci bruciate" not in contesto


def test_il_contesto_resta_sotto_gli_ottanta_caratteri_in_media(db, archivio):
    campioni = [
        _pulita(),
        _scura_e_molle(),
        immagini.jpeg_qualita(
            immagini.gradiente((1600, 1200), (200, 150, 100), (255, 220, 180)), 40
        ),
        immagini.jpeg_qualita(Image.new("RGB", (1600, 1200), (10, 10, 10)), 90),
        immagini.jpeg_con_exif(
            immagini.sfocata(immagini.nitida((1600, 1200), 10), 4), flash=1
        ),
        _pulita(),
        _pulita(),
    ]
    preparate = campagne.prepara_analisi(
        db, [_foto(db, archivio, d).id for d in campioni]
    )
    lunghezze = [len(p["contesto"]) for p in preparate.values()]
    assert max(lunghezze) > 0
    assert sum(lunghezze) / len(lunghezze) < 80


def test_il_contesto_cita_flash_e_candidati(db, archivio, monkeypatch):
    monkeypatch.setattr(
        preanalisi,
        "candidati",
        lambda img: {
            "volti": [
                {"id": "V1", "box": {}, "affidabilita": 0.9},
                {"id": "V2", "box": {}, "affidabilita": 0.8},
            ],
            "quadrilateri": [{"id": "Q1", "angoli": [], "box": {}, "area": 0.4}],
        },
    )
    dati = immagini.jpeg_con_exif(
        immagini.sfocata(immagini.nitida((1600, 1200), 10), 4), flash=1
    )
    (preparata,) = campagne.prepara_analisi(db, [_foto(db, archivio, dati).id]).values()
    assert "flash" in preparata["contesto"]
    assert preparata["contesto"].endswith("candidati V1 V2 Q1")


def test_il_locale_ha_la_forma_della_nota(db, archivio):
    dati = immagini.jpeg_con_exif(
        immagini.gradiente((2000, 1000), (60, 70, 80), (180, 190, 200)),
        orientamento=6,
        flash=0,
        profilo=immagini.profilo_icc("p3"),
    )
    (preparata,) = campagne.prepara_analisi(db, [_foto(db, archivio, dati).id]).values()
    locale = preparata["locale"]
    assert locale["versione"] == "locale-1"
    assert set(locale) == {
        "versione",
        "formato",
        "colore",
        "exif",
        "misure",
        "fasce",
        "candidati",
    }
    assert locale["formato"] == {
        "larghezza": 1000,
        "altezza": 2000,
        "rapporto": 0.5,
        "orientamento_exif": 6,
    }
    assert locale["colore"]["convertito_srgb"] is True
    assert (
        "p3" in locale["colore"]["profilo"].lower()
        or "display" in locale["colore"]["profilo"].lower()
    )
    assert locale["exif"]["flash"] is False and locale["exif"]["fotocamera"] is True
    assert set(locale["candidati"]) == {"volti", "quadrilateri"}
    assert {
        "nitidezza",
        "luminanza_mediana",
        "luci_bruciate",
        "ombre_chiuse",
        "dominante_ab",
        "caduta_bordi",
        "angolo_linee",
        "qualita_jpeg",
    } <= set(locale["misure"])
    # è JSON: si salva in analisi_ai
    import json

    assert json.loads(json.dumps(locale)) == locale


def test_senza_profilo_nessuna_conversione(db, archivio):
    (preparata,) = campagne.prepara_analisi(
        db, [_foto(db, archivio, _pulita()).id]
    ).values()
    assert preparata["locale"]["colore"] == {"profilo": None, "convertito_srgb": False}


def test_un_errore_su_una_foto_non_ferma_le_altre(db, archivio):
    buona = _foto(db, archivio, _pulita())
    rotta = _foto(db, archivio, b"\xff\xd8\xff non e' un jpeg")
    mancante = _foto(db, archivio, None, file="non-esiste.jpg")
    preparate = campagne.prepara_analisi(db, [rotta.id, buona.id, mancante.id, 999_999])
    assert preparate[buona.id]["immagine"] is not None
    for id_ in (rotta.id, mancante.id, 999_999):
        assert preparate[id_] == {"immagine": None, "contesto": "", "locale": None}


def test_se_la_pre_analisi_fallisce_la_foto_va_all_ai_senza_contesto(
    db, archivio, monkeypatch
):
    a, b = _foto(db, archivio, _scura_e_molle()), _foto(db, archivio, _scura_e_molle())
    originale = preanalisi.misura
    chiamate = []

    def a_volte(img, dati=None):
        chiamate.append(1)
        if len(chiamate) == 1:
            raise RuntimeError("misura impazzita")
        return originale(img, dati)

    monkeypatch.setattr(preanalisi, "misura", a_volte)
    preparate = campagne.prepara_analisi(db, [a.id, b.id])
    assert preparate[a.id]["immagine"] is not None  # va comunque all'AI
    assert preparate[a.id]["contesto"] == "" and preparate[a.id]["locale"] is None
    assert preparate[b.id]["contesto"] != "" and preparate[b.id]["locale"] is not None


def test_i_segni_si_disegnano_solo_se_accesi(db, archivio, monkeypatch):
    monkeypatch.setattr(
        preanalisi,
        "candidati",
        lambda img: {
            "volti": [
                {
                    "id": "V1",
                    "box": {"x": 0.3, "y": 0.3, "larghezza": 0.2, "altezza": 0.3},
                    "affidabilita": 0.9,
                }
            ],
            "quadrilateri": [],
        },
    )
    foto = _foto(db, archivio, _pulita())

    def immagine(segni: bool) -> np.ndarray:
        monkeypatch.setattr(
            analisi_locale,
            "leggi_impostazioni",
            lambda: SimpleNamespace(ritocco_segni=segni),
        )
        return np.asarray(
            immagini.apri(campagne.prepara_analisi(db, [foto.id])[foto.id]["immagine"])
        ).astype(int)

    spenti, accesi = immagine(False), immagine(True)
    assert np.abs(spenti - accesi).sum() > 0
    colore = np.array(preanalisi.COLORE_SEGNI)
    vicino = (np.abs(accesi - colore).sum(axis=2) < 90).sum()
    assert vicino > 50 and (np.abs(spenti - colore).sum(axis=2) < 90).sum() < vicino


def test_la_copia_per_l_ai_di_prima_c_e_ancora(db, archivio):
    foto = _foto(db, archivio, _pulita())
    copia = campagne.copia_per_ai(db, foto.id)
    assert max(Image.open(BytesIO(copia)).size) == 1024
