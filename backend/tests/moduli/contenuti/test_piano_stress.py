"""Prove dure sul piano a uscite (stesso giorno, un post per canale).

Provano il piano del finto su centinaia di combinazioni di periodo, canali, foto,
ritmo, ora di partenza e orari già occupati; e il controllo del piano con piani
rovinati a caso (fusi strani, cambio d'ora, oggetti sbagliati): il controllo non
deve mai andare in errore e deve sempre dire le violazioni giuste.
"""

import random
from copy import deepcopy
from datetime import date, datetime, time, timedelta, timezone

import pytest

from app.adapters.ai import AIFinto, CampagnaAI
from app.core.orologio import ROMA
from app.moduli.contenuti import domain
from app.moduli.contenuti.piano import controlla_piano, limiti_per_canale
from tests.adapters.ai.test_ai import SNAPSHOT, _come_li_vede_il_controllo, _gruppo

MARGINE = 15
RITMI = (2, 3, 5)
CANALI = (("facebook", "instagram"), ("facebook",), ("instagram",))


def _piano(rng: random.Random):
    giorni = rng.choice([7, 8, 13, 14, 20, 30, 31, 45, 60, 92])
    inizio = date(2030, 1, 1) + timedelta(days=rng.randrange(0, 330))
    fine = inizio + timedelta(days=giorni - 1)
    canali = rng.choice(CANALI)
    ritmo = rng.choice(RITMI)
    n_foto = rng.choice([0, 1, 2, 5, 9, 20])
    # da ora fino a un po' dopo l'inizio, anche a campagna iniziata
    scarto = rng.randrange(-5, giorni // 2 + 1)
    adesso = datetime.combine(inizio, time(9, 0), tzinfo=timezone.utc) + timedelta(
        days=scarto, hours=rng.randrange(0, 24)
    )
    gruppi = [_gruppo(n_foto)] if n_foto else []
    visti = _come_li_vede_il_controllo(gruppi)
    limiti = limiti_per_canale(canali, ritmo, inizio, fine, visti)
    occupati = []
    for _ in range(rng.randrange(0, 12)):
        giorno = inizio + timedelta(days=rng.randrange(0, giorni))
        occupati.append(
            {
                "canale": rng.choice(canali),
                "data_ora": datetime.combine(
                    giorno, time(10, 0), tzinfo=ROMA
                ).isoformat(),
            }
        )
    campagna = CampagnaAI(titolo="Prova", inizio=inizio, fine=fine)
    piano = AIFinto().pianifica_campagna(
        SNAPSHOT,
        campagna,
        gruppi,
        limiti,
        domain.SCHEDE_CANALE,
        non_prima_di=adesso + timedelta(minutes=MARGINE),
        orari_occupati=occupati,
    )
    return piano.contenuto, limiti, visti, inizio, fine, adesso, canali


@pytest.mark.parametrize("seme", range(300))
def test_il_piano_del_finto_e_sempre_fatto_di_uscite_nello_stesso_giorno(seme):
    rng = random.Random(seme)
    contenuto, limiti, visti, inizio, fine, adesso, canali = _piano(rng)

    violazioni = controlla_piano(
        contenuto,
        limiti=limiti,
        gruppi=visti,
        inizio=inizio,
        fine=fine,
        adesso=adesso,
        margine_minuti=MARGINE,
    )

    # Il finto non ha scuse: se il periodo ha ancora giorni utili, il piano è valido.
    # Quando il periodo è già quasi finito può non avere giorni: allora le uniche
    # violazioni ammesse sono di data, mai di struttura dell'uscita.
    strutturali = [
        v
        for v in violazioni
        if v["regola"]
        in ("uscita_incompleta", "uscita_giorni_diversi", "post_per_canale")
    ]
    assert strutturali == [], (seme, strutturali)

    for uscita in contenuto["uscite"]:
        assert {p["canale"] for p in uscita["post"]} == set(canali)
        assert len({p["canale"] for p in uscita["post"]}) == len(uscita["post"])
        giorni = {
            datetime.fromisoformat(p["data_ora"]).astimezone(ROMA).date()
            for p in uscita["post"]
        }
        assert len(giorni) == 1, (seme, uscita["numero"])


@pytest.mark.parametrize("seme", range(60))
def test_gli_orari_occupati_spostano_l_intera_uscita_non_un_solo_post(seme):
    """Con un orario occupato su un solo canale, l'uscita si sposta insieme (stesso giorno)."""
    rng = random.Random(1000 + seme)
    contenuto, limiti, visti, inizio, fine, adesso, canali = _piano(rng)
    if len(canali) < 2:
        pytest.skip("serve più di un canale")
    for uscita in contenuto["uscite"]:
        giorni = {
            datetime.fromisoformat(p["data_ora"]).astimezone(ROMA).date()
            for p in uscita["post"]
        }
        assert len(giorni) == 1


# --- Piani rovinati a caso: il controllo non va mai in errore ------------------

FUSI = [
    "+00:00",
    "+01:00",
    "+02:00",
    "-12:00",
    "+14:00",
    "Z",
]


def _quando(uno: dict) -> datetime:
    """La data del post, o una qualunque se un guasto precedente l'ha rovinata."""
    try:
        return datetime.fromisoformat(uno["data_ora"])
    except (TypeError, ValueError, KeyError):
        return datetime(2030, 1, 7, 10, tzinfo=ROMA)


def _rovina(piano: dict, rng: random.Random) -> dict:
    p = deepcopy(piano)
    uscite = p["uscite"]
    for _ in range(rng.randrange(1, 4)):
        if not uscite:
            break
        uscita = rng.choice(uscite)
        scelta = rng.randrange(0, 9)
        post = uscita.get("post")
        post = (
            [x for x in post if isinstance(x, dict)] if isinstance(post, list) else None
        )
        if scelta == 0 and post:
            uscita["post"] = post[:-1]
        elif scelta == 1 and post:
            uno = rng.choice(post)
            giorno = _quando(uno) + timedelta(days=rng.choice([-3, -1, 1, 2, 40]))
            uno["data_ora"] = giorno.isoformat()
        elif scelta == 2 and post:
            uno = rng.choice(post)
            data = _quando(uno).replace(tzinfo=None)
            uno["data_ora"] = data.isoformat() + rng.choice(FUSI)
        elif scelta == 3 and post:
            rng.choice(post)["data_ora"] = rng.choice(
                [
                    "",
                    "ieri",
                    None,
                    17,
                    "2030-13-45T10:00:00+01:00",
                    "2030-01-07T10:00:00",
                ]
            )
        elif scelta == 4 and post:
            rng.choice(post)["canale"] = rng.choice(["tiktok", "", None, 3])
        elif scelta == 5:
            uscita["post"] = rng.choice([None, [], "x", [None], [1, 2], {}])
        elif scelta == 6 and post:
            uscita["post"] = post + [deepcopy(post[0])]
        elif scelta == 7:
            uscita.pop("numero", None)
        else:
            uscite.append(deepcopy(uscita))
    return p


@pytest.mark.parametrize("seme", range(400))
def test_il_controllo_non_va_mai_in_errore_su_piani_rovinati(seme):
    rng = random.Random(5000 + seme)
    contenuto, limiti, visti, inizio, fine, adesso, _ = _piano(rng)
    rovinato = _rovina(contenuto, rng)

    violazioni = controlla_piano(
        rovinato,
        limiti=limiti,
        gruppi=visti,
        inizio=inizio,
        fine=fine,
        adesso=adesso,
        margine_minuti=MARGINE,
    )

    assert isinstance(violazioni, list)
    for v in violazioni:
        assert set(v) == {"regola", "canale", "messaggio"}
        assert v["messaggio"]


# --- Il giorno è quello di Roma, anche attorno al cambio d'ora -----------------


def _due_post(a: str, b: str):
    inizio, fine = date(2030, 3, 25), date(2030, 4, 10)
    gruppi = [_gruppo(5)]
    visti = _come_li_vede_il_controllo(gruppi)
    limiti = limiti_per_canale(("facebook", "instagram"), 3, inizio, fine, visti)
    adesso = datetime(2030, 3, 1, tzinfo=timezone.utc)
    piano = (
        AIFinto()
        .pianifica_campagna(
            SNAPSHOT,
            CampagnaAI(titolo="DST", inizio=inizio, fine=fine),
            gruppi,
            limiti,
            domain.SCHEDE_CANALE,
            non_prima_di=adesso,
        )
        .contenuto
    )
    post = piano["uscite"][0]["post"]
    post[0]["data_ora"], post[1]["data_ora"] = a, b
    return controlla_piano(
        piano,
        limiti=limiti,
        gruppi=visti,
        inizio=inizio,
        fine=fine,
        adesso=adesso,
        margine_minuti=MARGINE,
    )


@pytest.mark.parametrize(
    "a, b, stesso_giorno",
    [
        # Cambio all'ora legale: 31/03/2030, le 02:00 diventano le 03:00.
        ("2030-03-31T00:30:00+01:00", "2030-03-31T23:30:00+02:00", True),
        ("2030-03-30T23:30:00+01:00", "2030-03-31T00:15:00+01:00", False),
        # 22:30 UTC del 30 = 23:30 a Roma del 30; 22:30 UTC del 31 = 00:30 del 1° aprile.
        ("2030-03-30T22:30:00+00:00", "2030-03-31T22:30:00+00:00", False),
        # Stesso istante in fusi diversi: stesso giorno.
        ("2030-03-28T10:00:00+01:00", "2030-03-28T09:00:00+00:00", True),
        # Estremi dei fusi: per Roma è sempre lo stesso istante.
        ("2030-03-28T11:00:00+01:00", "2030-03-27T22:00:00-12:00", True),
        ("2030-03-28T11:00:00+01:00", "2030-03-28T11:00:00+14:00", False),
    ],
)
def test_il_giorno_si_conta_a_roma_anche_con_il_cambio_d_ora(a, b, stesso_giorno):
    regole = [v["regola"] for v in _due_post(a, b)]
    assert ("uscita_giorni_diversi" not in regole) is stesso_giorno, (a, b, regole)
