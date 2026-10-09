"""T1-33: validatore a regole, a due livelli (spec R-09, R-21).

Un test per regola e per canale, con il suo livello: i blocchi (testo vuoto,
limiti della piattaforma, parole vietate, cose da non dire, prezzi o premi) e
gli avvisi (limiti editoriali della scheda del canale).
"""

import json
from datetime import date, datetime, timezone

import pytest

from app.adapters.ai import AIFinto, CampagnaAI, PostAI
from app.moduli.contenuti import domain, validatore
from app.moduli.contenuti.validatore import termini_da_non_dire, valida_testo

CANALI = sorted(domain.SCHEDE_CANALE)
# I numeri di R-21, scritti qui una seconda volta apposta.
NUMERI = {
    "facebook": dict(max_caratteri=500, max_hashtag=3, limite=5000, limite_tag=30),
    "instagram": dict(max_caratteri=600, max_hashtag=5, limite=2200, limite_tag=30),
}
SNAPSHOT = {
    "nome": "Ceramiche Bianchi",
    "storia": "Bottega di famiglia: tre generazioni al tornio.",
    "gamma": "Piatti, vasi e servizi da tavola in maiolica decorata.",
    "vincoli": "Non parlare di sconti; non citare altri marchi.",
    "valori": ["artigianalita", "tradizione"],
    "foto_policy": {"persone": "con_consenso"},
}
TESTO = "Un vaso appena uscito dal forno, dipinto a mano nella nostra bottega."
HASHTAG = ["ceramica", "fattoamano"]


def _valida(testo=TESTO, hashtag=HASHTAG, canale="instagram", snapshot=SNAPSHOT):
    return valida_testo(testo, hashtag, canale, snapshot)


def _regole(errori: list) -> list[tuple[str, str]]:
    return [(errore["regola"], errore["livello"]) for errore in errori]


def _lungo(caratteri: int) -> str:
    return ("parola " * caratteri)[:caratteri]


@pytest.mark.parametrize("canale", CANALI)
def test_testo_buono_non_ha_blocchi_ne_avvisi(canale):
    assert _valida(canale=canale) == []


def test_le_schede_hanno_i_numeri_di_r21():
    for canale, numeri in NUMERI.items():
        scheda = domain.SCHEDE_CANALE[canale]
        assert scheda["max_caratteri"] == numeri["max_caratteri"]
        assert scheda["max_hashtag"] == numeri["max_hashtag"]
        assert scheda["limite_caratteri"] == numeri["limite"]
        assert scheda["limite_hashtag"] == numeri["limite_tag"]


def test_ogni_regola_ha_il_suo_livello():
    assert validatore.REGOLE == {
        "testo_vuoto": "blocco",
        "limite_caratteri": "blocco",
        "limite_hashtag": "blocco",
        "parole_vietate": "blocco",
        "da_non_dire": "blocco",
        "prezzi_o_premi": "blocco",
        "max_caratteri": "avviso",
        "max_hashtag": "avviso",
    }
    assert set(validatore.REGOLE.values()) == set(domain.LIVELLI_VALIDATORE)


def test_canale_senza_scheda_non_si_valida():
    with pytest.raises(ValueError, match="tiktok"):
        _valida(canale="tiktok")


def test_senza_snapshot_valgono_le_regole_che_non_lo_leggono():
    assert valida_testo(TESTO, HASHTAG, "instagram", None) == []
    assert _regole(valida_testo("", [], "instagram", None)) == [
        ("testo_vuoto", "blocco")
    ]


# --- Blocchi ------------------------------------------------------------------


@pytest.mark.parametrize("canale", CANALI)
@pytest.mark.parametrize("testo", ["", "   ", "\n\t"])
def test_blocco_testo_vuoto(canale, testo):
    errori = _valida(testo=testo, canale=canale)

    assert _regole(errori) == [("testo_vuoto", "blocco")]
    assert errori[0]["messaggio"] == "Il testo è vuoto."


@pytest.mark.parametrize("canale", CANALI)
def test_blocco_limite_di_caratteri_della_piattaforma(canale):
    limite = NUMERI[canale]["limite"]

    al_limite = _valida(testo=_lungo(limite), hashtag=[], canale=canale)
    assert _regole(al_limite) == [("max_caratteri", "avviso")]

    oltre = _valida(testo=_lungo(limite + 1), hashtag=[], canale=canale)
    assert _regole(oltre) == [("limite_caratteri", "blocco")]
    assert str(limite) in oltre[0]["messaggio"]


@pytest.mark.parametrize("canale", CANALI)
def test_blocco_limite_di_caratteri_conta_anche_gli_hashtag(canale):
    """Sulla piattaforma esce il testo con gli hashtag: " #ceramica" sono 10."""
    limite = NUMERI[canale]["limite"]

    giusto = _valida(testo=_lungo(limite - 10), hashtag=["ceramica"], canale=canale)
    assert ("limite_caratteri", "blocco") not in _regole(giusto)

    oltre = _valida(testo=_lungo(limite - 9), hashtag=["ceramica"], canale=canale)
    assert ("limite_caratteri", "blocco") in _regole(oltre)
    assert ("max_caratteri", "avviso") not in _regole(oltre)


@pytest.mark.parametrize("canale", CANALI)
def test_blocco_limite_di_hashtag_della_piattaforma(canale):
    limite = NUMERI[canale]["limite_tag"]
    tanti = [f"tag{numero}" for numero in range(limite + 1)]

    assert _regole(_valida(hashtag=tanti[:limite], canale=canale)) == [
        ("max_hashtag", "avviso")
    ]
    oltre = _valida(hashtag=tanti, canale=canale)
    assert _regole(oltre) == [("limite_hashtag", "blocco")]
    assert str(limite) in oltre[0]["messaggio"]


@pytest.mark.parametrize("canale", CANALI)
@pytest.mark.parametrize(
    ("testo", "trovata"),
    [
        ("Spedizione gratis per tutti.", "gratis"),
        ("Un risultato garantito.", "garantito"),
        ("Qualità garantita da tre generazioni.", "garantita"),
        ("Uno smalto miracoloso.", "miracoloso"),
        ("Prezzi imbattibili in bottega.", "imbattibili"),
        ("Il migliore vaso dell'Umbria.", "il migliore"),
        ("Siamo il NUMERO UNO della maiolica.", "numero uno"),
    ],
)
def test_blocco_parole_vietate(canale, testo, trovata):
    errori = _valida(testo=testo, canale=canale)

    assert _regole(errori) == [("parole_vietate", "blocco")]
    assert f"«{trovata}»" in errori[0]["messaggio"]


def test_blocco_parole_vietate_anche_negli_hashtag():
    errori = _valida(hashtag=["ceramica", "gratis"])
    assert _regole(errori) == [("parole_vietate", "blocco")]


@pytest.mark.parametrize(
    "testo",
    [
        "La nostra garanzia è il lavoro fatto a mano.",  # non è "garantito"
        "Migliorare ogni giorno, un pezzo alla volta.",  # non è "il migliore"
        "Il numero di pezzi è limitato: uno per forma.",  # non è "numero uno"
        "Gratitudine per chi passa a trovarci.",  # non è "gratis"
    ],
)
def test_le_parole_vietate_sono_parole_intere(testo):
    assert _valida(testo=testo) == []


@pytest.mark.parametrize("canale", CANALI)
@pytest.mark.parametrize(
    ("testo", "trovato"),
    [
        ("Questa settimana uno sconto speciale.", "sconto"),
        ("Tanti SCONTI in bottega.", "sconti"),
        ("Meglio di altri marchi.", "altri marchi"),
    ],
)
def test_blocco_cose_da_non_dire_del_profilo(canale, testo, trovato):
    """ "Non parlare di sconti; non citare altri marchi." nella fotografia del profilo."""
    errori = _valida(testo=testo, canale=canale)

    assert _regole(errori) == [("da_non_dire", "blocco")]
    assert f"«{trovato}»" in errori[0]["messaggio"]


def test_cose_da_non_dire_anche_negli_hashtag():
    assert _regole(_valida(hashtag=["sconti"])) == [("da_non_dire", "blocco")]


def test_cose_da_non_dire_vengono_dallo_snapshot_non_da_un_elenco_fisso():
    senza_vincoli = dict(SNAPSHOT, vincoli=None)
    assert _valida(testo="Uno sconto speciale.", snapshot=senza_vincoli) == []


def test_cose_da_non_dire_non_ferma_parole_diverse():
    """ "Scontro" e "scontato" non sono "sconti": meglio un blocco in meno."""
    assert _valida(testo="Lo scontro tra argilla e fuoco non è mai scontato.") == []


@pytest.mark.parametrize(
    ("vincoli", "termini"),
    [
        ("Non parlare di sconti; non citare altri marchi.", ["sconti", "altri marchi"]),
        ("Non parlare di dimensioni", ["dimensioni"]),
        ("Non parlare dell'oro\nMai la politica", ["oro", "politica"]),
        ("Evitare di parlare di religione, niente calcio.", ["religione", "calcio"]),
        ("NON DIRE PREZZI. No promozioni", ["prezzi", "promozioni"]),
        ("Non citare i concorrenti; non citare i concorrenti", ["concorrenti"]),
        # Solo le frasi che dicono che cosa non dire, e solo se corte.
        ("Usare sempre il lei. Eleganza.", []),
        ("Non parlare di cose che riguardano la vita privata", []),
        ("Nostra tradizione. Notte bianca.", []),
        ("", []),
        (None, []),
    ],
)
def test_termini_da_non_dire_letti_dai_vincoli(vincoli, termini):
    assert termini_da_non_dire(vincoli) == termini


@pytest.mark.parametrize("canale", CANALI)
@pytest.mark.parametrize(
    ("testo", "scritto"),
    [
        ("Il vaso grande a 120 euro.", "120 euro"),
        ("Solo €45 per il servizio da tè.", "€45"),
        ("Piatti da 19,90 € l'uno.", "19,90 €"),
        ("Un pezzo da 1.200 EUR.", "1.200 eur"),
    ],
)
def test_blocco_prezzo_che_non_e_nei_dati_della_bottega(canale, testo, scritto):
    errori = _valida(testo=testo, canale=canale)

    assert _regole(errori) == [("prezzi_o_premi", "blocco")]
    assert f"«{scritto}»" in errori[0]["messaggio"]


def test_un_prezzo_che_e_nei_dati_della_bottega_passa():
    con_prezzi = dict(SNAPSHOT, gamma="Vasi da 120 € e piatti da 19,90 euro.")

    assert _valida(testo="Il vaso grande a 120 euro.", snapshot=con_prezzi) == []
    assert _valida(testo="Piatti a € 19,90.", snapshot=con_prezzi) == []
    assert _regole(_valida(testo="Il vaso a 150 euro.", snapshot=con_prezzi)) == [
        ("prezzi_o_premi", "blocco")
    ]


@pytest.mark.parametrize(
    "testo",
    [
        "Al tornio da 28 anni, in 3 generazioni.",
        "100% fatto a mano.",
        "Vi aspettiamo dalle 9 alle 18 in via Roma 12.",
    ],
)
def test_un_numero_senza_euro_non_e_un_prezzo(testo):
    assert _valida(testo=testo) == []


@pytest.mark.parametrize("canale", CANALI)
@pytest.mark.parametrize(
    ("testo", "trovato"),
    [
        ("Bottega premiata per la sua maiolica.", "premiata"),
        ("Abbiamo ricevuto il premio dell'anno.", "premio"),
        ("Medaglia d'oro alla fiera.", "medaglia"),
        ("Vincitori del concorso regionale.", "vincitori"),
        ("Un riconoscimento che ci onora.", "riconoscimento"),
    ],
)
def test_blocco_premio_che_non_e_nei_dati_della_bottega(canale, testo, trovato):
    errori = _valida(testo=testo, canale=canale)

    assert _regole(errori) == [("prezzi_o_premi", "blocco")]
    assert f"«{trovato}»" in errori[0]["messaggio"]


def test_un_premio_che_e_nei_dati_della_bottega_passa():
    premiata = dict(SNAPSHOT, storia="Premiata nel 2019 alla fiera di Faenza.")

    assert _valida(testo="Una bottega premiata.", snapshot=premiata) == []
    assert _regole(_valida(testo="Medaglia d'oro.", snapshot=premiata)) == [
        ("prezzi_o_premi", "blocco")
    ]


def test_premi_il_pulsante_non_e_un_premio():
    assert _valida(testo="Premi sul link e scopri la collezione.") == []


# --- Avvisi -------------------------------------------------------------------


@pytest.mark.parametrize("canale", CANALI)
def test_avviso_limite_editoriale_di_caratteri(canale):
    massimo = NUMERI[canale]["max_caratteri"]

    assert _valida(testo=_lungo(massimo), canale=canale) == []

    oltre = _valida(testo=_lungo(massimo + 1), canale=canale)
    assert _regole(oltre) == [("max_caratteri", "avviso")]
    assert str(massimo) in oltre[0]["messaggio"]


@pytest.mark.parametrize("canale", CANALI)
def test_avviso_limite_editoriale_di_hashtag(canale):
    massimo = NUMERI[canale]["max_hashtag"]
    tanti = [f"tag{numero}" for numero in range(massimo + 1)]

    assert _valida(hashtag=tanti[:massimo], canale=canale) == []

    oltre = _valida(hashtag=tanti, canale=canale)
    assert _regole(oltre) == [("max_hashtag", "avviso")]
    assert str(massimo) in oltre[0]["messaggio"]


def test_i_limiti_editoriali_cambiano_con_il_canale():
    """550 caratteri e 4 hashtag: avvisi su Facebook, niente su Instagram."""
    testo, hashtag = _lungo(550), ["uno", "due", "tre", "quattro"]

    assert _regole(_valida(testo=testo, hashtag=hashtag, canale="facebook")) == [
        ("max_caratteri", "avviso"),
        ("max_hashtag", "avviso"),
    ]
    assert _valida(testo=testo, hashtag=hashtag, canale="instagram") == []


# --- Insieme ------------------------------------------------------------------


def test_blocchi_e_avvisi_insieme_e_salvabili_come_json():
    """CA-18, parte del validatore: con un blocco il post è da rivedere."""
    testo = "Sconto garantito: il vaso a 99 euro. " + _lungo(600)
    errori = _valida(testo=testo, hashtag=["a", "b", "c", "d", "e", "f"])

    assert _regole(errori) == [
        ("parole_vietate", "blocco"),
        ("da_non_dire", "blocco"),
        ("prezzi_o_premi", "blocco"),
        ("max_caratteri", "avviso"),
        ("max_hashtag", "avviso"),
    ]
    assert all(set(errore) == {"livello", "regola", "messaggio"} for errore in errori)
    assert json.loads(json.dumps(errori)) == errori


def test_il_testo_del_provider_finto_passa_il_validatore():
    """Il testo di `AIFinto` (T1-31) non ha blocchi né avvisi, su ogni canale."""
    campagna = CampagnaAI(
        titolo="Prova", inizio=date(2030, 1, 7), fine=date(2030, 1, 20)
    )
    for canale in CANALI:
        post = PostAI(
            canale=canale,
            tema="Dietro ogni pezzo c'è una storia",
            formato="singola",
            data_ora=datetime(2030, 1, 8, 9, tzinfo=timezone.utc),
        )
        scritto = AIFinto().genera_post(
            SNAPSHOT, campagna, post, domain.SCHEDE_CANALE[canale]
        )
        assert valida_testo(scritto.testo, scritto.hashtag, canale, SNAPSHOT) == []
