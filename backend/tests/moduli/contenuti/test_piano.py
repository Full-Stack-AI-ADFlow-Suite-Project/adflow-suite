"""T1-32: limiti e controllo del piano (spec R-05, R-08, R-20, R-21, R-23, R-28).

- CA-17 (limiti): 14 giorni, 3 post/sett., 2 canali, 5 foto idonee e diverse
  → 6 post chiesti per canale, 5 con una foto e 1 cartolina.
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
    foto_con_stella,
    foto_disponibili,
    limiti_per_canale,
    piano_debole,
    post_chiesti,
)
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza, campagna_inviata, foto

INIZIO = date(2030, 1, 7)
FINE = date(2030, 1, 20)  # 14 giorni
ADESSO = datetime(2030, 1, 1, 9, tzinfo=timezone.utc)
MARGINE = 15
IDONEA = {"idonea": True, "simile_a": None}


def _foto(id: int, *, idonea=True, simile_a=None, stella=False, analizzata=True):
    analisi = {"idonea": idonea, "simile_a": simile_a} if analizzata else None
    return SimpleNamespace(id=id, da_usare=stella, analisi_ai=analisi)


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
        riempitivo=None if foto else "cartolina",
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


def _piano_valido(limiti: dict, gruppo_id: int = 1) -> dict:
    """Una foto per post finché ce ne sono, poi cartoline; un'uscita al giorno."""
    chiesti = max(limite["post_chiesti"] for limite in limiti.values())
    uscite = []
    for indice in range(chiesti):
        post = []
        con_foto = False
        for canale, limite in limiti.items():
            disponibili = limite["foto_disponibili"]
            foto = disponibili[indice : indice + 1]
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


def _controlla(contenuto, limiti, gruppi, *, adesso=ADESSO):
    return controlla_piano(
        contenuto,
        limiti=limiti,
        gruppi=gruppi,
        inizio=INIZIO,
        fine=FINE,
        adesso=adesso,
        margine_minuti=MARGINE,
    )


def _regole(violazioni: list) -> list[str]:
    return [violazione["regola"] for violazione in violazioni]


# --- Limiti -----------------------------------------------------------------


def test_ca17_limiti_sei_post_chiesti_cinque_foto_e_una_cartolina(db):
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
    assert piano_debole(limiti, gruppi) is False

    # 6 uscite, 6 post per canale: 5 con una foto e 1 cartolina, nessuna ripetuta.
    contenuto = _piano_valido(limiti, gruppo_id=mazzo.id)
    assert len(contenuto["uscite"]) == 6
    assert _controlla(contenuto, limiti, gruppi) == []


@pytest.mark.parametrize(
    ("a_settimana", "giorni", "attesi"),
    [
        (2, 7, 2),  # durata minima (R-08)
        (3, 7, 3),
        (5, 7, 5),
        (3, 8, 3),  # 24 ÷ 7, per difetto
        (3, 10, 4),  # 30 ÷ 7, per difetto
        (3, 14, 6),  # CA-17
        (2, 92, 26),  # durata massima (R-08): 184 ÷ 7
        (5, 92, 65),  # 460 ÷ 7
    ],
)
def test_post_chiesti_per_difetto(a_settimana, giorni, attesi):
    fine = INIZIO + timedelta(days=giorni - 1)
    assert post_chiesti(a_settimana, INIZIO, fine) == attesi


def test_post_chiesti_con_periodo_rovesciato_sono_zero():
    assert post_chiesti(3, FINE, INIZIO) == 0


@pytest.mark.parametrize(
    ("frequenza", "giorni"),
    [("f1_2", 7), ("f3_4", 14), ("f5_piu", 10), ("f5_piu", 92), (None, 30)],
)
def test_post_chiesti_uguali_a_quelli_del_dettaglio_della_campagna(
    client, utente_di_prova, db, frequenza, giorni
):
    """La formula di R-05 vive anche nel dettaglio della campagna: devono coincidere."""
    utente_di_prova("operatore")
    bottega = profilo(db, canali=["facebook", "instagram"], frequenza=frequenza)
    fine = INIZIO + timedelta(days=giorni - 1)
    campagna = campagna_in_bozza(db, profilo_id=bottega.id, inizio=INIZIO, fine=fine)

    risposta = client.get(f"/api/campagne/{campagna.id}")

    assert risposta.status_code == 200
    attesi = post_chiesti(artigiani.post_a_settimana(frequenza), INIZIO, fine)
    assert risposta.json()["post_chiesti_per_canale"] == {
        "facebook": attesi,
        "instagram": attesi,
    }


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


def test_foto_con_stella_solo_se_idonee():
    gruppi = [
        _gruppo(
            1,
            [
                _foto(1, stella=True),
                _foto(2, stella=True, idonea=False),
                _foto(3),
                _foto(4, stella=True, analizzata=False),
            ],
        )
    ]
    assert foto_con_stella(gruppi) == [1]


def test_limiti_per_canale_riempitivi_solo_se_le_foto_non_bastano():
    poche, _ = _limiti(4)
    assert poche["instagram"] == {
        "post_chiesti": 6,
        "foto_disponibili": [1, 2, 3, 4],
        "riempitivi": 2,
    }
    assert poche["facebook"] == poche["instagram"]

    giuste, _ = _limiti(6)
    assert giuste["facebook"]["riempitivi"] == 0
    tante, _ = _limiti(9)
    assert tante["facebook"]["riempitivi"] == 0


def test_limiti_per_canale_senza_un_canale_tolto():
    """Un canale tolto non si passa: i limiti sono solo dei canali rimasti."""
    limiti, _ = _limiti(5, canali=("instagram",))
    assert list(limiti) == ["instagram"]


def test_limiti_sono_dizionari_semplici():
    limiti, _ = _limiti(5)
    assert json.loads(json.dumps(limiti)) == limiti


@pytest.mark.parametrize(
    ("n_foto", "debole"),
    [
        (0, True),  # nessuna foto
        (2, True),  # 2 su 6: sotto la metà
        (3, False),  # 3 su 6: la metà esatta non è debole
        (6, False),
    ],
)
def test_piano_debole_con_foto_sotto_la_meta_dei_post_chiesti(n_foto, debole):
    """CA-49, parte dei limiti."""
    limiti, _ = _limiti(n_foto)
    # il gruppo senza idonee si prova a parte: qui conta solo la metà
    gruppi = [_gruppo(1, [_foto(99)])]
    assert piano_debole(limiti, gruppi) is debole


def test_piano_debole_con_meta_dispari():
    """5 post chiesti: 2 foto sono sotto la metà, 3 no."""
    gruppi = [_gruppo_di(2)]
    limiti = limiti_per_canale(["instagram"], 5, INIZIO, INIZIO + timedelta(6), gruppi)
    assert limiti["instagram"]["post_chiesti"] == 5
    assert piano_debole(limiti, gruppi) is True

    gruppi = [_gruppo_di(3)]
    limiti = limiti_per_canale(["instagram"], 5, INIZIO, INIZIO + timedelta(6), gruppi)
    assert piano_debole(limiti, gruppi) is False


def test_piano_debole_con_un_gruppo_caricate_senza_foto_idonee():
    gruppi = [
        _gruppo_di(8),
        _gruppo(2, [_foto(20, idonea=False), _foto(21, analizzata=False)]),
    ]
    limiti = limiti_per_canale(["facebook"], 3, INIZIO, FINE, gruppi)
    assert limiti["facebook"]["riempitivi"] == 0
    assert piano_debole(limiti, gruppi) is True


def test_piano_non_debole_con_un_gruppo_di_doppioni_idonei():
    """R-20 guarda le foto idonee del gruppo, non i doppioni."""
    gruppi = [_gruppo_di(8), _gruppo(2, [_foto(20, simile_a=1)])]
    limiti = limiti_per_canale(["facebook"], 3, INIZIO, FINE, gruppi)
    assert piano_debole(limiti, gruppi) is False


def test_piano_non_debole_per_un_gruppo_create_ai():
    """Un gruppo `create_ai` non ha foto: la generazione lo ignora (R-19)."""
    gruppi = [_gruppo_di(8), _gruppo(2, [], origine="create_ai")]
    limiti = limiti_per_canale(["facebook"], 3, INIZIO, FINE, gruppi)
    assert piano_debole(limiti, gruppi) is False


# --- Controllo del piano ------------------------------------------------------


@pytest.mark.parametrize("n_foto", [0, 3, 5, 6, 9])
def test_piano_valido_non_ha_violazioni(n_foto):
    limiti, gruppi = _limiti(n_foto)
    assert _controlla(_piano_valido(limiti), limiti, gruppi) == []


def test_piano_valido_con_un_carosello_dove_non_ci_sono_riempitivi():
    """CA-52, parte del controllo: più foto in un post, la stessa su due canali."""
    limiti, gruppi = _limiti(8)
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
    limiti, gruppi = _limiti(9)
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


def test_regola_riempitivi_piu_di_quelli_che_mancano():
    """5 foto e 6 post: 4 foto e 2 cartoline non vanno, ne manca una sola."""
    limiti, gruppi = _limiti(5, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][4] = _uscita(5, [_post("instagram", giorno=5)], gruppo_id=None)

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert _regole(violazioni) == ["riempitivi"]
    assert violazioni[0]["canale"] == "instagram"
    assert "devono essere 1" in violazioni[0]["messaggio"]


def test_regola_riempitivi_dove_le_foto_bastano():
    limiti, gruppi = _limiti(6, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][5] = _uscita(6, [_post("instagram", giorno=6)], gruppo_id=None)

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert _regole(violazioni) == ["riempitivi"]
    assert "devono essere 0" in violazioni[0]["messaggio"]


def test_regola_riempitivi_si_conta_canale_per_canale():
    limiti, gruppi = _limiti(6)
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][5]["post"][1] = _post("instagram", giorno=6)

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert [(v["regola"], v["canale"]) for v in violazioni] == [
        ("riempitivi", "instagram")
    ]


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
    limiti, gruppi = _limiti(8, canali=("instagram",))
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


def test_regola_foto_con_la_stella_fuori_dal_piano():
    """CA-51, parte del controllo: la foto con la stella, se idonea, è nel piano."""
    gruppi = [_gruppo(1, [_foto(n) for n in range(1, 8)] + [_foto(8, stella=True)])]
    limiti = limiti_per_canale(["facebook", "instagram"], 3, INIZIO, FINE, gruppi)
    contenuto = _piano_valido(limiti)  # usa le foto da 1 a 6

    violazioni = _controlla(contenuto, limiti, gruppi)

    assert violazioni == [
        {
            "regola": "foto_con_stella",
            "canale": None,
            "messaggio": "La foto 8 ha la stella e non è in nessun post.",
        }
    ]

    # basta un post del piano, su un canale qualsiasi
    contenuto["uscite"][0]["post"][0]["foto"] = [8]
    assert _controlla(contenuto, limiti, gruppi) == []


def test_una_foto_con_la_stella_non_idonea_resta_fuori_dal_piano():
    gruppi = [
        _gruppo(
            1,
            [_foto(n) for n in range(1, 7)] + [_foto(8, stella=True, idonea=False)],
        )
    ]
    limiti = limiti_per_canale(["instagram"], 3, INIZIO, FINE, gruppi)
    assert _controlla(_piano_valido(limiti), limiti, gruppi) == []


@pytest.mark.parametrize("canale", sorted(domain.SCHEDE_CANALE))
def test_regola_massimo_di_foto_per_post(canale):
    """R-21: al massimo 10 foto per post, su ogni canale."""
    assert domain.SCHEDE_CANALE[canale]["max_foto"] == 10
    limiti, gruppi = _limiti(20, canali=(canale,))
    contenuto = _piano_valido(limiti)

    contenuto["uscite"][0]["post"] = [_post(canale, [1] + list(range(7, 16)))]
    assert len(contenuto["uscite"][0]["post"][0]["foto"]) == 10
    assert _controlla(contenuto, limiti, gruppi) == []

    contenuto["uscite"][0]["post"] = [_post(canale, [1] + list(range(7, 17)))]
    violazioni = _controlla(contenuto, limiti, gruppi)
    assert _regole(violazioni) == ["troppe_foto"]
    assert violazioni[0]["canale"] == canale


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
    "riempitivo non dello sprint 1": _cambia_post(riempitivo="archivio", foto=[]),
    "riempitivo sconosciuto": _cambia_post(riempitivo="meme", foto=[]),
    "cartolina con una foto": _cambia_post(riempitivo="cartolina"),
    "cartolina carosello": _cambia_post(
        riempitivo="cartolina", foto=[], formato="carosello"
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
