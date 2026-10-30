"""Limiti e controllo del piano (spec R-05, R-08, R-21, R-28).

- CA-17 (limiti): 14 giorni, 3 post/sett., 2 canali, 5 foto idonee e diverse
  → 6 post chiesti per canale, 5 con una foto e 1 immagine AI.
- CA-80 (limiti): 10 foto idonee, 6 post chiesti → le 6 di punteggio più alto.
- Un test per ogni regola del controllo, più i casi limite.
"""

import json
from copy import deepcopy
from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.core.orologio import ROMA
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import domain, piano
from app.moduli.contenuti.piano import (
    controlla_piano,
    foto_disponibili,
    limiti_per_canale,
)
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza, campagna_inviata, foto

INIZIO = date(2030, 1, 7)
FINE = date(2030, 1, 20)  # 14 giorni
ADESSO = datetime(2030, 1, 1, 9, tzinfo=timezone.utc)
MARGINE = 15
IDONEA = {"idonea": True, "simile_a": None}
DUE_CANALI = ("facebook", "instagram")


def _foto(id: int, *, idonea=True, simile_a=None, analizzata=True, punteggio=None):
    analisi = {"idonea": idonea, "simile_a": simile_a} if analizzata else None
    if analisi is not None and punteggio is not None:
        analisi["punteggio"] = punteggio
    return SimpleNamespace(id=id, analisi_ai=analisi)


def _gruppo(id: int, foto: list, *, origine: str = "caricate"):
    return SimpleNamespace(id=id, origine=origine, foto=foto)


def _gruppo_di(n: int, *, id: int = 1, da: int = 1):
    """Un gruppo con ``n`` foto idonee e diverse, con gli id da ``da`` in poi."""
    return _gruppo(id, [_foto(numero) for numero in range(da, da + n)])


def _quando(giorno: int, ora: int = 10, minuti: int = 0) -> str:
    """Data e ora del giorno ``giorno`` della campagna (1 = inizio), a Roma."""
    giorno_di_uscita = INIZIO + timedelta(days=giorno - 1)
    return datetime.combine(
        giorno_di_uscita, time(ora, minuti), tzinfo=ROMA
    ).isoformat()


def _post(canale: str, foto=(), *, giorno: int = 1, **campi) -> dict:
    foto = list(foto)
    dati = dict(
        canale=canale,
        formato="carosello" if len(foto) > 1 else "singola",
        foto=foto,
        riempitivo=None if foto else "immagine_ai",
        data_ora=_quando(giorno),
    )
    dati.update(campi)
    return dati


def _uscita(numero: int, post: list, *, gruppo_id: int | None = 1, **campi) -> dict:
    dati = dict(numero=numero, tema=f"Tema {numero}", gruppo_id=gruppo_id, post=post)
    dati.update(campi)
    return dati


def _piano(*uscite: dict) -> dict:
    return {"strategia": "Strategia di prova", "uscite": list(uscite)}


def _voce(foto_id: int, *, mai_uscita: bool = True, gruppo_id: int = 9, **campi):
    """Una foto d'archivio, come la dà ``campagne.service.foto_di_archivio()``."""
    return SimpleNamespace(
        foto=_foto(foto_id, **campi),
        gruppo=_gruppo(gruppo_id, []),
        mai_uscita=mai_uscita,
    )


def _piano_valido(limiti: dict, gruppo_id: int = 1) -> dict:
    """Una foto per post finché ce ne sono, poi le immagini AI; un'uscita al giorno."""
    chiesti = max(limite["post_chiesti"] for limite in limiti.values())
    uscite = []
    for indice in range(chiesti):
        post = []
        con_foto = False
        for canale, limite in limiti.items():
            foto = limite["foto_disponibili"][indice : indice + 1]
            con_foto = con_foto or bool(foto)
            post.append(_post(canale, foto, giorno=indice + 1))
        uscite.append(
            _uscita(indice + 1, post, gruppo_id=gruppo_id if con_foto else None)
        )
    return _piano(*uscite)


def _limiti(n_foto: int, *, canali=("facebook", "instagram"), a_settimana: int = 3):
    """Limiti e gruppi di una campagna di 14 giorni con ``n_foto`` foto idonee."""
    gruppi = [_gruppo_di(n_foto)]
    return limiti_per_canale(canali, a_settimana, INIZIO, FINE, gruppi), gruppi


def _limiti_larghi(n_foto: int, *, canali=("facebook", "instagram")):
    """Limiti con tutte le ``n_foto`` foto disponibili, anche oltre i post chiesti.

    La generazione non li dà mai (R-05): servono a provare le regole dei
    caroselli, congelati, e del massimo di foto per post.
    """
    gruppi = [_gruppo_di(n_foto)]
    limiti = limiti_per_canale(canali, 3, INIZIO, FINE, gruppi)
    for limite in limiti.values():
        limite["foto_disponibili"] = foto_disponibili(gruppi)
        limite["riempitivi"] = max(0, limite["post_chiesti"] - n_foto)
    return limiti, gruppi


def _controlla(contenuto, limiti, gruppi, *, adesso=ADESSO, archivio=None):
    return controlla_piano(
        contenuto,
        limiti=limiti,
        gruppi=gruppi,
        inizio=INIZIO,
        fine=FINE,
        adesso=adesso,
        margine_minuti=MARGINE,
        archivio=archivio,
    )


def _regole(violazioni: list) -> list[str]:
    return [violazione["regola"] for violazione in violazioni]


# --- Limiti -----------------------------------------------------------------


def test_ca17_limiti_sei_post_chiesti_cinque_foto_e_un_immagine_ai(db):
    """CA-17, parte dei limiti: i dati veri della campagna danno 6, 5 e 1."""
    bottega = profilo(db, canali=["facebook", "instagram"], frequenza="f3_4")
    campagna = campagna_inviata(db, profilo_id=bottega.id, inizio=INIZIO, fine=FINE)
    mazzo = campagne.gruppi_della_campagna(db, campagna.id)[0]
    foto(db, gruppo=mazzo)  # la quinta: la fabbrica ne crea 4
    for una in campagne.foto_della_campagna(db, campagna.id):
        campagne.aggiorna_foto(db, una.id, dict(IDONEA), 0)

    gruppi = campagne.gruppi_della_campagna(db, campagna.id)
    limiti = limiti_per_canale(
        campagna.canali,
        artigiani.post_a_settimana(campagna.frequenza),
        campagna.inizio,
        campagna.fine,
        gruppi,
    )

    assert set(limiti) == {"facebook", "instagram"}
    for limite in limiti.values():
        assert limite["post_chiesti"] == 6
        assert len(limite["foto_disponibili"]) == 5
        assert limite["riempitivi"] == 1

    # 6 uscite, 6 post per canale: 5 con una foto e 1 immagine AI, nessuna ripetuta.
    contenuto = _piano_valido(limiti, gruppo_id=mazzo.id)
    assert len(contenuto["uscite"]) == 6
    assert _controlla(contenuto, limiti, gruppi) == []


@pytest.mark.parametrize(
    ("a_settimana", "giorni", "attesi"),
    [(2, 7, 2), (3, 10, 4), (5, 92, 65)],  # durata minima, per difetto, massima
)
def test_limiti_per_canale_con_i_post_chiesti_di_campagne(a_settimana, giorni, attesi):
    """La formula di R-05 è una sola, in ``campagne.service.post_chiesti()`` (#44)."""
    fine = INIZIO + timedelta(days=giorni - 1)
    limiti = limiti_per_canale(["facebook"], a_settimana, INIZIO, fine, [])
    assert limiti["facebook"]["post_chiesti"] == attesi
    assert attesi == campagne.post_chiesti(a_settimana, INIZIO, fine)


def test_limiti_uguali_ai_post_chiesti_del_dettaglio_della_campagna(
    client, utente_di_prova, db
):
    """L'artigiano legge nel dettaglio gli stessi post che il piano dovrà avere."""
    utente_di_prova("operatore")
    bottega = profilo(db, canali=["facebook", "instagram"], frequenza="f5_piu")
    fine = INIZIO + timedelta(days=9)
    campagna = campagna_in_bozza(db, profilo_id=bottega.id, inizio=INIZIO, fine=fine)

    risposta = client.get(f"/api/campagne/{campagna.id}")

    limiti = limiti_per_canale(
        campagna.canali,
        artigiani.post_a_settimana(bottega.frequenza),
        campagna.inizio,
        campagna.fine,
        [],
    )
    assert risposta.status_code == 200
    assert risposta.json()["post_chiesti_per_canale"] == {
        canale: limite["post_chiesti"] for canale, limite in limiti.items()
    }
    assert limiti["instagram"]["post_chiesti"] == 7  # 5 × 10 ÷ 7, per difetto


def test_foto_disponibili_idonee_e_senza_doppioni_sommate_sui_gruppi():
    gruppi = [
        _gruppo(
            1,
            [
                _foto(1),
                _foto(2, idonea=False),
                _foto(3, simile_a=1),
                _foto(4, analizzata=False),
            ],
        ),
        _gruppo(2, [_foto(5), _foto(6)]),
        _gruppo(3, [_foto(7)], origine="create_ai"),
    ]
    assert foto_disponibili(gruppi) == [1, 5, 6]


def test_foto_disponibili_senza_gruppi_sono_nessuna():
    assert foto_disponibili([]) == []


def test_limiti_per_canale_riempitivi_solo_se_le_foto_non_bastano():
    poche, _ = _limiti(4)
    assert poche["instagram"] == {
        "post_chiesti": 6,
        "foto_disponibili": [1, 2, 3, 4],
        "foto_riempitivo": [],
        "riempitivi": 2,
    }
    assert poche["facebook"] == poche["instagram"]

    giuste, _ = _limiti(6)
    assert giuste["facebook"]["riempitivi"] == 0
    tante, _ = _limiti(9)
    assert tante["facebook"]["riempitivi"] == 0


def test_ca80_limiti_le_foto_migliori_per_punteggio_fino_ai_post_chiesti():
    """10 foto idonee e diverse, 6 post chiesti: le 6 di punteggio più alto."""
    punteggi = [3, 5, 1, 4, 2, 5, 4, 1, 3, 2]
    foto_del_gruppo = [_foto(n, punteggio=p) for n, p in enumerate(punteggi, start=1)]
    gruppi = [_gruppo(1, foto_del_gruppo)]

    limiti = limiti_per_canale(DUE_CANALI, 3, INIZIO, FINE, gruppi)

    for limite in limiti.values():
        assert limite["post_chiesti"] == 6
        # punteggio 5: foto 2 e 6; 4: foto 4 e 7; 3: foto 1 e 9 (a parità, l'id più basso)
        assert limite["foto_disponibili"] == [2, 6, 4, 7, 1, 9]
        assert limite["riempitivi"] == 0
    assert piano.foto_preselezionate(gruppi, 6) == [2, 6, 4, 7, 1, 9]


def test_preselezione_a_parita_di_punteggio_vale_l_id_e_senza_punteggio_si_va_in_coda():
    gruppi = [
        _gruppo(1, [_foto(4), _foto(3, punteggio=2), _foto(1, punteggio=2)]),
        _gruppo(2, [_foto(2, punteggio=0), _foto(5, punteggio=True)]),
    ]
    # il punteggio 0 vale più di nessun punteggio; `True` non è un punteggio
    assert piano.foto_preselezionate(gruppi, 5) == [1, 3, 2, 4, 5]
    assert piano.foto_preselezionate(gruppi, 2) == [1, 3]
    assert piano.foto_preselezionate(gruppi, 0) == []


def test_preselezione_lascia_fuori_le_foto_non_idonee_che_contano_come_mancanti():
    foto_del_gruppo = [
        _foto(1, punteggio=5),
        _foto(2, punteggio=5, idonea=False),
        _foto(3, punteggio=5, simile_a=1),
        _foto(4, punteggio=5, analizzata=False),
        _foto(5, punteggio=1),
    ]
    limiti = limiti_per_canale(
        ["facebook"], 3, INIZIO, FINE, [_gruppo(1, foto_del_gruppo)]
    )
    assert limiti["facebook"]["foto_disponibili"] == [1, 5]
    assert limiti["facebook"]["riempitivi"] == 4


def test_limiti_per_canale_senza_un_canale_tolto():
    """Un canale tolto non si passa: i limiti sono solo dei canali rimasti."""
    limiti, _ = _limiti(5, canali=("instagram",))
    assert list(limiti) == ["instagram"]


def test_limiti_sono_dizionari_semplici():
    limiti, _ = _limiti(5)
    assert json.loads(json.dumps(limiti)) == limiti


def test_ca76_limiti_foto_d_archivio_disponibili_solo_dove_non_sono_mai_uscite():
    """CA-76, parte dei limiti: i limiti cambiano da un canale all'altro (R-27)."""
    gruppi = [_gruppo_di(3)]
    archivio = {
        "facebook": [_voce(10), _voce(11, mai_uscita=False)],
        "instagram": [_voce(10), _voce(11), _voce(12)],
    }

    limiti = limiti_per_canale(DUE_CANALI, 3, INIZIO, FINE, gruppi, archivio)

    # su Facebook la 11 è già uscita: vale solo come riempitivo `archivio`
    assert limiti["facebook"] == {
        "post_chiesti": 6,
        "foto_disponibili": [1, 2, 3, 10],
        "foto_riempitivo": [11],
        "riempitivi": 2,
    }
    assert limiti["instagram"] == {
        "post_chiesti": 6,
        "foto_disponibili": [1, 2, 3, 10, 11, 12],
        "foto_riempitivo": [],
        "riempitivi": 0,
    }
    assert json.loads(json.dumps(limiti)) == limiti


def test_limiti_foto_d_archivio_non_idonee_doppioni_e_senza_analisi_restano_fuori():
    archivio = {
        "instagram": [
            _voce(10, idonea=False),
            _voce(11, simile_a=12),
            _voce(12),
            _voce(13, analizzata=False),
            _voce(14, mai_uscita=False, simile_a=15),
            _voce(15, mai_uscita=False),
        ]
    }

    limiti = limiti_per_canale(["instagram"], 3, INIZIO, FINE, [], archivio)

    assert limiti["instagram"]["foto_disponibili"] == [12]
    assert limiti["instagram"]["foto_riempitivo"] == [15]


def test_limiti_senza_archivio_per_un_canale():
    """Un canale che l'archivio non nomina ha solo le foto della campagna."""
    archivio = {"facebook": [_voce(10)]}
    limiti = limiti_per_canale(DUE_CANALI, 3, INIZIO, FINE, [_gruppo_di(2)], archivio)
    assert limiti["instagram"]["foto_disponibili"] == [1, 2]
    assert limiti["facebook"]["foto_disponibili"] == [1, 2, 10]


def test_limiti_senza_archivio_non_hanno_foto_per_i_riempitivi():
    """Archivio congelato (ADR-114): chi genera non lo passa."""
    limiti, _ = _limiti(4)
    for limite in limiti.values():
        assert limite["foto_riempitivo"] == []


# --- Controllo del piano ------------------------------------------------------


@pytest.mark.parametrize("n_foto", [0, 3, 5, 6, 9])
def test_piano_valido_non_ha_violazioni(n_foto):
    limiti, gruppi = _limiti(n_foto)
    assert _controlla(_piano_valido(limiti), limiti, gruppi) == []


def test_piano_valido_con_un_carosello_dove_non_ci_sono_riempitivi():
    """CA-52, parte del controllo (carosello congelato): più foto in un post."""
    limiti, gruppi = _limiti_larghi(8)
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][0]["post"] = [
        _post("facebook", [1, 7, 8]),
        _post("instagram", [1, 7]),
    ]
    assert _controlla(contenuto, limiti, gruppi) == []


def test_il_controllo_non_cambia_il_piano():
    limiti, gruppi = _limiti(5)
    contenuto = _piano_valido(limiti)
    prima = deepcopy(contenuto)
    _controlla(contenuto, limiti, gruppi)
    assert contenuto == prima


def test_regola_post_per_canale_con_un_post_in_meno():
    limiti, gruppi = _limiti(6)
    contenuto = _piano_valido(limiti)
    ultima = contenuto["uscite"][-1]
    ultima["post"] = [p for p in ultima["post"] if p["canale"] != "instagram"]

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert violazioni == [
        {
            "regola": "post_per_canale",
            "canale": "instagram",
            "messaggio": "Su instagram i post devono essere 6: sono 5.",
        }
    ]


def test_regola_post_per_canale_con_un_post_in_piu():
    limiti, gruppi = _limiti_larghi(9)
    contenuto = _piano_valido(limiti)
    contenuto["uscite"].append(_uscita(7, [_post("facebook", [7], giorno=7)]))

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert _regole(violazioni) == ["post_per_canale"]
    assert violazioni[0]["canale"] == "facebook"


def test_regola_post_per_canale_con_un_canale_che_la_campagna_non_ha():
    """Vale anche per un canale tolto: il piano non lo deve più usare."""
    limiti, gruppi = _limiti(6, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][0]["post"].append(_post("facebook", [1]))

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert _regole(violazioni) == ["post_per_canale"]
    assert violazioni[0]["canale"] == "facebook"


def test_ca101_nessun_tetto_alle_immagini_ai_piu_di_quelle_che_mancano():
    """CA-101, R-28: 5 foto e 6 post, una foto non usata e 2 immagini AI: il piano è valido."""
    limiti, gruppi = _limiti(5, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][4] = _uscita(5, [_post("instagram", giorno=5)], gruppo_id=None)

    assert _controlla(contenuto, limiti, gruppi) == []


def test_nessun_tetto_alle_immagini_ai_dove_le_foto_bastano():
    limiti, gruppi = _limiti(6, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][5] = _uscita(6, [_post("instagram", giorno=6)], gruppo_id=None)

    assert _controlla(contenuto, limiti, gruppi) == []


def test_un_piano_tutto_con_immagini_ai_e_valido():
    limiti, gruppi = _limiti(6)
    contenuto = _piano(
        *(
            _uscita(
                numero,
                [_post(c, giorno=numero) for c in ("facebook", "instagram")],
                gruppo_id=None,
            )
            for numero in range(1, 7)
        )
    )

    assert _controlla(contenuto, limiti, gruppi) == []


def test_un_post_senza_foto_e_senza_immagine_ai_resta_non_valido():
    limiti, gruppi = _limiti(5, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][5]["post"][0]["riempitivo"] = None

    assert _regole(_controlla(contenuto, limiti, gruppi)) == ["piano_malformato"]


def test_regola_nessun_carosello_su_un_canale_con_riempitivi():
    """CA-57, parte del controllo."""
    limiti, gruppi = _limiti(5, canali=("instagram",))
    contenuto = _piano(
        _uscita(1, [_post("instagram", [1, 2], giorno=1)]),
        _uscita(2, [_post("instagram", [3], giorno=2)]),
        _uscita(3, [_post("instagram", [4], giorno=3)]),
        _uscita(4, [_post("instagram", [5], giorno=4)]),
        _uscita(5, [_post("instagram", giorno=5)], gruppo_id=None),
        _uscita(6, [_post("instagram", giorno=6)], gruppo_id=None),
    )

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert "carosello_con_riempitivi" in _regole(violazioni)
    carosello = next(v for v in violazioni if v["regola"] == "carosello_con_riempitivi")
    assert carosello["canale"] == "instagram"
    assert carosello["messaggio"].startswith("Uscita 1")


def test_regola_foto_ripetuta_sullo_stesso_canale():
    limiti, gruppi = _limiti(6, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][5]["post"][0]["foto"] = [1]

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert violazioni == [
        {
            "regola": "foto_ripetuta",
            "canale": "instagram",
            "messaggio": "Su instagram la foto 1 compare 2 volte.",
        }
    ]


def test_regola_foto_ripetuta_nello_stesso_carosello():
    limiti, gruppi = _limiti_larghi(8, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][0]["post"] = [_post("instagram", [1, 7, 7])]

    assert _regole(_controlla(contenuto, limiti, gruppi)) == ["foto_ripetuta"]


def test_la_stessa_foto_su_due_canali_non_e_ripetuta():
    limiti, gruppi = _limiti(6)
    contenuto = _piano_valido(limiti)
    assert contenuto["uscite"][0]["post"][0]["foto"] == [1]
    assert contenuto["uscite"][0]["post"][1]["foto"] == [1]
    assert _controlla(contenuto, limiti, gruppi) == []


@pytest.mark.parametrize(
    "estranea",
    [
        _foto(50, idonea=False),  # non idonea (R-18)
        _foto(50, simile_a=1),  # doppione
        _foto(50, analizzata=False),  # non analizzata
        None,  # di un'altra campagna: il gruppo non la conosce
    ],
)
def test_regola_foto_non_disponibile(estranea):
    gruppi = [_gruppo_di(6)]
    if estranea is not None:
        gruppi[0].foto.append(estranea)
    limiti = limiti_per_canale(["instagram"], 3, INIZIO, FINE, gruppi)
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][5]["post"][0]["foto"] = [50]

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert violazioni == [
        {
            "regola": "foto_non_disponibile",
            "canale": "instagram",
            "messaggio": "Su instagram la foto 50 non è tra le foto disponibili.",
        }
    ]


@pytest.mark.parametrize(
    ("data_ora", "fuori"),
    [
        (datetime(2030, 1, 6, 23, 59, tzinfo=ROMA), True),  # il giorno prima
        (datetime(2030, 1, 7, 0, 0, tzinfo=ROMA), False),  # primo minuto
        (datetime(2030, 1, 20, 23, 59, tzinfo=ROMA), False),  # ultimo minuto
        (datetime(2030, 1, 21, 0, 0, tzinfo=ROMA), True),  # il giorno dopo
        # Il giorno si legge a Roma: le 23:30 UTC del 20 sono già il 21.
        (datetime(2030, 1, 20, 23, 30, tzinfo=timezone.utc), True),
        (datetime(2030, 1, 6, 23, 30, tzinfo=timezone.utc), False),
    ],
)
def test_regola_data_fuori_dal_periodo(data_ora, fuori):
    limiti, gruppi = _limiti(6, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][0]["post"][0]["data_ora"] = data_ora.isoformat()

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert _regole(violazioni) == (["data_fuori_periodo"] if fuori else [])
    if fuori:
        assert violazioni[0]["canale"] == "instagram"
        assert violazioni[0]["messaggio"].startswith("Uscita 1, post instagram")


@pytest.mark.parametrize(
    ("minuti", "nel_passato"),
    [(-60, True), (0, True), (14, True), (15, False), (16, False)],
)
def test_regola_data_nel_passato(minuti, nel_passato):
    """R-08: data e ora almeno 15 minuti dopo adesso."""
    adesso = datetime(2030, 1, 10, 12, tzinfo=timezone.utc)  # a campagna iniziata
    limiti, gruppi = _limiti(6, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    for indice, uscita in enumerate(contenuto["uscite"]):
        uscita["post"][0]["data_ora"] = _quando(9 + indice)
    contenuto["uscite"][0]["post"][0]["data_ora"] = (
        adesso + timedelta(minutes=minuti)
    ).isoformat()

    violazioni = _controlla(contenuto, limiti, gruppi, adesso=adesso)

    assert _regole(violazioni) == (["data_nel_passato"] if nel_passato else [])


def test_data_prima_del_periodo_e_nel_passato_sono_due_regole():
    adesso = datetime(2030, 1, 10, 12, tzinfo=timezone.utc)
    limiti, gruppi = _limiti(6, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    for indice, uscita in enumerate(contenuto["uscite"]):
        uscita["post"][0]["data_ora"] = _quando(9 + indice)
    contenuto["uscite"][0]["post"][0]["data_ora"] = datetime(
        2030, 1, 3, 10, tzinfo=ROMA
    ).isoformat()

    violazioni = _controlla(contenuto, limiti, gruppi, adesso=adesso)

    assert _regole(violazioni) == ["data_fuori_periodo", "data_nel_passato"]


def test_una_stella_gia_salvata_non_e_piu_una_regola():
    """ADR-114, A11: `foto.da_usare` resta nel database, il controllo non lo legge."""
    con_stella = _foto(8)
    con_stella.da_usare = True
    gruppi = [_gruppo(1, [_foto(n) for n in range(1, 8)] + [con_stella])]
    limiti = limiti_per_canale(["facebook", "instagram"], 3, INIZIO, FINE, gruppi)
    contenuto = _piano_valido(limiti)  # usa le foto da 1 a 6

    assert _controlla(contenuto, limiti, gruppi) == []
    assert "foto_con_stella" not in piano.REGOLE


@pytest.mark.parametrize("canale", sorted(domain.SCHEDE_CANALE))
def test_regola_massimo_di_foto_per_post(canale):
    """R-21: al massimo 10 foto per post, su ogni canale."""
    assert domain.SCHEDE_CANALE[canale]["max_foto"] == 10
    limiti, gruppi = _limiti_larghi(20, canali=(canale,))
    contenuto = _piano_valido(limiti)

    contenuto["uscite"][0]["post"] = [_post(canale, [1] + list(range(7, 16)))]
    assert len(contenuto["uscite"][0]["post"][0]["foto"]) == 10
    assert _controlla(contenuto, limiti, gruppi) == []

    contenuto["uscite"][0]["post"] = [_post(canale, [1] + list(range(7, 17)))]
    violazioni = _controlla(contenuto, limiti, gruppi)
    assert _regole(violazioni) == ["troppe_foto"]
    assert violazioni[0]["canale"] == canale


def test_ca80_una_foto_non_preselezionata_non_e_disponibile():
    """Le foto oltre i post chiesti restano non usate: il piano non le può usare."""
    punteggi = [5, 4, 3, 2, 1, 1, 1, 1]
    gruppi = [_gruppo(1, [_foto(n, punteggio=p) for n, p in enumerate(punteggi, 1)])]
    limiti = limiti_per_canale(["instagram"], 3, INIZIO, FINE, gruppi)
    assert limiti["instagram"]["foto_disponibili"] == [1, 2, 3, 4, 5, 6]
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][5]["post"][0]["foto"] = [8]

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert violazioni == [
        {
            "regola": "foto_non_disponibile",
            "canale": "instagram",
            "messaggio": "Su instagram la foto 8 non è tra le foto disponibili.",
        }
    ]


def test_ca57_il_piano_senza_foto_e_tutto_di_immagini_ai():
    limiti, gruppi = _limiti(0)
    contenuto = _piano_valido(limiti)
    post = [p for uscita in contenuto["uscite"] for p in uscita["post"]]
    assert len(post) == 12
    assert {p["riempitivo"] for p in post} == {"immagine_ai"}
    assert {p["formato"] for p in post} == {"singola"}
    assert all(p["foto"] == [] for p in post)
    assert _controlla(contenuto, limiti, gruppi) == []


@pytest.mark.parametrize("riempitivo", ["archivio", "cartolina"])
def test_archivio_e_cartolina_non_sono_riempitivi_del_piano(riempitivo):
    """ADR-114: restano valori ammessi nel database, il piano non li chiede."""
    assert piano.RIEMPITIVI_DEL_PIANO == ("immagine_ai",)
    assert riempitivo in domain.TIPI_RIEMPITIVO
    limiti, gruppi = _limiti(5, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][5]["post"][0]["riempitivo"] = riempitivo

    assert set(_regole(_controlla(contenuto, limiti, gruppi))) == {"piano_malformato"}


def _cambia_post(**campi):
    def cambia(contenuto: dict) -> None:
        contenuto["uscite"][0]["post"][0].update(campi)

    return cambia


def _cambia_uscita(**campi):
    def cambia(contenuto: dict) -> None:
        contenuto["uscite"][0].update(campi)

    return cambia


def _due_post_sullo_stesso_canale(contenuto: dict) -> None:
    contenuto["uscite"][0]["post"].append(_post("instagram", [9]))


MALFORMATI = {
    "non è un oggetto": lambda contenuto: None,
    "senza strategia": lambda contenuto: contenuto.pop("strategia"),
    "strategia vuota": lambda contenuto: contenuto.update(strategia="  "),
    "senza uscite": lambda contenuto: contenuto.pop("uscite"),
    "uscite non in elenco": lambda contenuto: contenuto.update(uscite={}),
    "uscita non oggetto": lambda contenuto: contenuto["uscite"].append("uscita"),
    "uscita senza numero": _cambia_uscita(numero=None),
    "numero non intero": _cambia_uscita(numero="1"),
    "numero booleano": _cambia_uscita(numero=True),
    "numero ripetuto": _cambia_uscita(numero=2),
    "uscita senza tema": _cambia_uscita(tema=""),
    "gruppo sconosciuto": _cambia_uscita(gruppo_id=999),
    "gruppo create_ai": _cambia_uscita(gruppo_id=2),
    "gruppo non intero": _cambia_uscita(gruppo_id=[1]),
    "uscita senza post": _cambia_uscita(post=[]),
    "post non in elenco": _cambia_uscita(post=None),
    "post non oggetto": _cambia_uscita(post=["post"]),
    "due post sullo stesso canale": _due_post_sullo_stesso_canale,
    "post senza canale": _cambia_post(canale=None),
    "formato sconosciuto": _cambia_post(formato="storia"),
    "archivio non è un riempitivo": _cambia_post(riempitivo="archivio", foto=[1]),
    "cartolina non è un riempitivo": _cambia_post(riempitivo="cartolina", foto=[]),
    "riempitivo sconosciuto": _cambia_post(riempitivo="meme", foto=[]),
    "immagine AI con una foto": _cambia_post(riempitivo="immagine_ai"),
    "immagine AI con due foto": _cambia_post(riempitivo="immagine_ai", foto=[1, 9]),
    "immagine AI carosello": _cambia_post(
        riempitivo="immagine_ai", foto=[], formato="carosello"
    ),
    "post senza foto né riempitivo": _cambia_post(foto=[]),
    "singola con due foto": _cambia_post(foto=[1, 9]),
    "carosello con una foto": _cambia_post(formato="carosello"),
    "foto non in elenco": _cambia_post(foto=1),
    "foto non intere": _cambia_post(foto=["1"]),
    "foto booleane": _cambia_post(foto=[True]),
    "senza data": _cambia_post(data_ora=None),
    "data che non è una data": _cambia_post(data_ora="lunedì mattina"),
    "data senza fuso": _cambia_post(data_ora="2030-01-07T10:00:00"),
}


@pytest.mark.parametrize("difetto", sorted(MALFORMATI))
def test_regola_piano_malformato(difetto):
    """Un piano malformato esce con i soli difetti di forma, senza eccezioni."""
    gruppi = [_gruppo_di(9), _gruppo(2, [], origine="create_ai")]
    limiti = limiti_per_canale(["instagram"], 3, INIZIO, FINE, gruppi)
    contenuto = _piano_valido(limiti)
    assert _controlla(contenuto, limiti, gruppi) == []

    if difetto == "non è un oggetto":
        contenuto = ["uscite"]
    else:
        MALFORMATI[difetto](contenuto)
    violazioni = _controlla(contenuto, limiti, gruppi)

    assert violazioni, difetto
    assert set(_regole(violazioni)) == {"piano_malformato"}
    assert all(v["canale"] is None and v["messaggio"] for v in violazioni)


def test_piano_senza_uscite_non_ha_i_post_chiesti():
    """Un elenco vuoto ha la forma giusta: lo ferma il conto dei post."""
    limiti, gruppi = _limiti(6, canali=("instagram",))
    contenuto = {"strategia": "Strategia di prova", "uscite": []}
    assert _regole(_controlla(contenuto, limiti, gruppi)) == ["post_per_canale"]


def test_ogni_regola_ha_un_nome_e_le_violazioni_si_salvano_come_json():
    limiti, gruppi = _limiti(5)
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][0]["post"][0]["foto"] = [77]
    contenuto["uscite"][1]["post"][1]["data_ora"] = _quando(40)

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert _regole(violazioni) == ["foto_non_disponibile", "data_fuori_periodo"]
    assert set(_regole(violazioni)) <= set(piano.REGOLE)
    assert json.loads(json.dumps(violazioni)) == violazioni


def test_ca106_la_scena_non_e_una_regola_del_piano():
    """CA-106: una scena mancante o malformata non è una violazione."""
    limiti, gruppi = _limiti(5, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][4] = _uscita(5, [_post("instagram", giorno=5)], gruppo_id=None)

    # Senza la chiave `scena`.
    assert _controlla(contenuto, limiti, gruppi) == []

    # Con una scena malformata.
    contenuto["uscite"][4]["scena"] = {"soggetto": 42, "inquadratura": "boh"}
    assert _controlla(contenuto, limiti, gruppi) == []
