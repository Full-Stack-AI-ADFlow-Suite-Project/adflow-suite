"""T1-31: adattatore AI e provider finto, senza nessuna chiamata di rete.

- Il piano del provider finto passa il controllo di T1-32.
- Un test per tipo di errore di R-35, su ogni operazione.
"""

import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import app.adapters.ai as modulo_ai
from app.adapters.ai import (
    TIPI_ERRORE,
    AIFinto,
    CampagnaAI,
    ErroreAI,
    FotoAI,
    GruppoAI,
    PostAI,
    imposta_ai,
    ottieni_ai,
    usa_ai,
)
from app.adapters.ai.finto import OPERAZIONI
from app.core.config import leggi_impostazioni
from app.core.orologio import ROMA
from app.moduli.contenuti import domain
from app.moduli.contenuti.piano import controlla_piano, limiti_per_canale

INIZIO = date(2030, 1, 7)
FINE = date(2030, 1, 20)  # 14 giorni: con 3 post a settimana, 6 post chiesti
ADESSO = datetime(2030, 1, 1, 9, tzinfo=timezone.utc)
MARGINE = 15
SNAPSHOT = {"nome": "Bottega di prova", "citta": "Roma", "da_non_dire": []}
CAMPAGNA = CampagnaAI(titolo="Campagna di prova", inizio=INIZIO, fine=FINE)
DUE_CANALI = ("facebook", "instagram")


def _gruppo(n_foto: int, *, id: int = 1, da: int = 1, punteggi=None) -> GruppoAI:
    """Un gruppo con ``n_foto`` foto idonee e diverse, già analizzate.

    ``punteggi`` dà il punteggio di ogni foto, nell'ordine; senza, nessuna ne ha.
    """
    return GruppoAI(
        id=id,
        descrizione=f"Vasi del gruppo {id}",
        foto=[
            FotoAI(
                id=numero,
                file=f"{numero}.jpg",
                mime="image/jpeg",
                analisi={"idonea": True, "simile_a": None}
                | ({"punteggio": punteggi[numero - da]} if punteggi else {}),
            )
            for numero in range(da, da + n_foto)
        ],
    )


def _come_li_vede_il_controllo(gruppi: list[GruppoAI]) -> list:
    """Gli stessi gruppi con i nomi dei campi di ``campagne`` (T1-32)."""
    return [
        SimpleNamespace(
            id=gruppo.id,
            origine="caricate",
            foto=[SimpleNamespace(id=f.id, analisi_ai=f.analisi) for f in gruppo.foto],
        )
        for gruppo in gruppi
    ]


def _pianifica(
    finto: AIFinto,
    gruppi,
    *,
    canali=DUE_CANALI,
    adesso=ADESSO,
    **altro,
):
    """Piano del provider finto e violazioni trovate dal controllo di T1-32."""
    visti = _come_li_vede_il_controllo(gruppi)
    limiti = limiti_per_canale(canali, 3, INIZIO, FINE, visti)
    piano = finto.pianifica_campagna(
        SNAPSHOT,
        CAMPAGNA,
        gruppi,
        limiti,
        domain.SCHEDE_CANALE,
        non_prima_di=adesso + timedelta(minutes=MARGINE),
        **altro,
    )
    violazioni = controlla_piano(
        piano.contenuto,
        limiti=limiti,
        gruppi=visti,
        inizio=INIZIO,
        fine=FINE,
        adesso=adesso,
        margine_minuti=MARGINE,
    )
    return piano, violazioni


def _post_del_canale(contenuto: dict, canale: str) -> list[dict]:
    return [p for u in contenuto["uscite"] for p in u["post"] if p["canale"] == canale]


def _post_da_scrivere(canale: str = "instagram", **campi) -> PostAI:
    dati = dict(
        canale=canale,
        tema="Vasi in terracotta",
        formato="singola",
        data_ora=datetime(2030, 1, 8, 10, tzinfo=ROMA),
        foto=[FotoAI(id=1, file="1.jpg", mime="image/jpeg")],
    )
    dati.update(campi)
    return PostAI(**dati)


def _scrivi(finto: AIFinto, canale: str = "instagram", **altro):
    return finto.genera_post(
        SNAPSHOT,
        CAMPAGNA,
        _post_da_scrivere(canale),
        domain.SCHEDE_CANALE[canale],
        **altro,
    )


# --- Composizione -------------------------------------------------------------


@pytest.fixture(autouse=True)
def _ai_di_partenza():
    """Ogni test parte e finisce senza un provider già scelto."""
    imposta_ai(None)
    yield
    imposta_ai(None)


def test_ottieni_ai_restituisce_il_finto_e_sempre_la_stessa_istanza():
    assert isinstance(ottieni_ai(), AIFinto)
    assert ottieni_ai() is ottieni_ai()


def test_ottieni_ai_con_litellm_senza_modelli_e_un_errore_di_configurazione(
    monkeypatch,
):
    """CA-58, parte dell'adattatore: `AI_PROVIDER=litellm` senza i modelli in `.env`."""
    import app.adapters.ai.litellm as modulo_litellm

    senza_modelli = leggi_impostazioni().model_copy(
        update={
            "ai_provider": "litellm",
            "ai_modello_visione": "",
            "ai_modello_testo": "",
        }
    )
    monkeypatch.setattr(modulo_ai, "leggi_impostazioni", lambda: senza_modelli)
    monkeypatch.setattr(modulo_litellm, "leggi_impostazioni", lambda: senza_modelli)
    with pytest.raises(ErroreAI) as sollevato:
        ottieni_ai()
    assert sollevato.value.tipo == "configurazione"
    assert "AI_MODELLO_VISIONE" in sollevato.value.messaggio


def test_usa_ai_ripristina_il_provider_precedente():
    primo = ottieni_ai()
    altro = AIFinto()
    with usa_ai(altro):
        assert ottieni_ai() is altro
    assert ottieni_ai() is primo


def test_nessuna_libreria_di_rete_caricata_dall_adattatore():
    """Con il provider finto LiteLLM non si importa neppure (in un processo pulito)."""
    codice = chr(10).join(
        [
            "import sys",
            "from app.adapters.ai import ottieni_ai",
            "ottieni_ai()",
            "assert 'litellm' not in sys.modules and 'openai' not in sys.modules",
        ]
    )
    ambiente = {**os.environ, "AI_PROVIDER": "finto"}
    risultato = subprocess.run(
        [sys.executable, "-c", codice],
        cwd=Path(__file__).resolve().parents[3],
        env=ambiente,
        capture_output=True,
        text=True,
    )
    assert risultato.returncode == 0, risultato.stderr


# --- Errori (R-35) ------------------------------------------------------------


def test_i_tipi_di_errore_sono_quelli_di_contenuti():
    assert TIPI_ERRORE == domain.TIPI_ERRORE_GENERAZIONE


def test_errore_ai_con_un_tipo_sconosciuto_non_si_crea():
    with pytest.raises(ValueError):
        ErroreAI("grave", "Messaggio")


def _chiama(finto: AIFinto, operazione: str):
    if operazione == "analizza_gruppo":
        return finto.analizza_gruppo(_gruppo(2))
    if operazione == "pianifica_campagna":
        return _pianifica(finto, [_gruppo(6)])[0]
    if operazione == "genera_immagine":
        return finto.genera_immagine("Un prompt di prova")
    return _scrivi(finto)


@pytest.mark.parametrize("operazione", OPERAZIONI)
@pytest.mark.parametrize("tipo", TIPI_ERRORE)
def test_errore_a_comando_di_ogni_tipo_su_ogni_operazione(tipo, operazione):
    finto = AIFinto()
    finto.comanda_errore(operazione, tipo)

    with pytest.raises(ErroreAI) as sollevato:
        _chiama(finto, operazione)

    assert sollevato.value.tipo == tipo
    assert sollevato.value.messaggio
    assert str(sollevato.value) == sollevato.value.messaggio
    assert sollevato.value.foto_id is None
    # una volta sola: la chiamata dopo riesce
    assert _chiama(finto, operazione)


def test_errore_a_comando_per_piu_volte_e_per_sempre():
    finto = AIFinto()
    finto.comanda_errore("genera_post", "temporaneo", volte=2)
    for _ in range(2):
        with pytest.raises(ErroreAI):
            _scrivi(finto)
    assert _scrivi(finto).testo

    finto.comanda_errore("genera_post", "configurazione", volte=None)
    for _ in range(4):
        with pytest.raises(ErroreAI):
            _scrivi(finto)


def test_errore_su_una_sola_foto_finche_la_foto_e_nel_gruppo():
    """CA-59, parte dell'adattatore: l'errore dice quale foto lo ha causato."""
    finto = AIFinto()
    finto.comanda_errore("analizza_gruppo", "rifiuto", volte=None, foto_id=2)
    gruppo = _gruppo(3)

    with pytest.raises(ErroreAI) as sollevato:
        finto.analizza_gruppo(gruppo)
    assert sollevato.value.tipo == "rifiuto"
    assert sollevato.value.foto_id == 2

    gruppo.foto = [foto for foto in gruppo.foto if foto.id != 2]
    assert set(finto.analizza_gruppo(gruppo)) == {1, 3}


def test_errore_solo_sui_post_di_un_canale():
    finto = AIFinto()
    finto.comanda_errore("genera_post", "richiesta", volte=None, canale="facebook")

    assert _scrivi(finto, "instagram").testo
    with pytest.raises(ErroreAI) as sollevato:
        _scrivi(finto, "facebook")
    assert sollevato.value.tipo == "richiesta"


@pytest.mark.parametrize(
    ("operazione", "tipo"), [("traduci", "temporaneo"), ("genera_post", "grave")]
)
def test_comando_di_errore_non_valido(operazione, tipo):
    with pytest.raises(ValueError):
        AIFinto().comanda_errore(operazione, tipo)


# --- Analisi ------------------------------------------------------------------


def test_analisi_ogni_foto_idonea_con_i_campi_del_piano():
    analisi = AIFinto().analizza_gruppo(_gruppo(3))

    assert set(analisi) == {1, 2, 3}
    for una in analisi.values():
        assert set(una) == {
            "idonea",
            "simile_a",
            "tipo",
            "punteggio",
            "motivo",
            "soggetto",
        }
        assert una["idonea"] is True
        assert una["simile_a"] is None
        assert una["soggetto"] == "Vasi del gruppo 1"


def test_analisi_a_comando_non_idonea_e_doppione():
    """A comando una foto è non idonea, un'altra è un doppione."""
    finto = AIFinto()
    finto.comanda_analisi(2, idonea=False, motivo="Foto sfocata")
    finto.comanda_analisi(3, simile_a=1)

    analisi = finto.analizza_gruppo(_gruppo(3))

    assert analisi[1]["idonea"] is True
    assert analisi[2]["idonea"] is False
    assert analisi[2]["motivo"] == "Foto sfocata"
    assert analisi[3]["simile_a"] == 1


def test_le_chiamate_si_registrano():
    """CA-50, parte dell'adattatore: si vede che cosa è stato analizzato."""
    finto = AIFinto()
    finto.analizza_gruppo(_gruppo(2, id=7))
    _scrivi(finto, "facebook")

    assert finto.chiamate == [
        {"operazione": "analizza_gruppo", "gruppo": 7, "foto": [1, 2]},
        {
            "operazione": "genera_post",
            "canale": "facebook",
            "tema": "Vasi in terracotta",
            "riscrittura": False,
        },
    ]


# --- Piano --------------------------------------------------------------------


@pytest.mark.parametrize("canali", [DUE_CANALI, ("instagram",), ("facebook",)])
@pytest.mark.parametrize("n_foto", [0, 1, 3, 5, 6, 9, 20])
def test_il_piano_del_provider_finto_passa_il_controllo(n_foto, canali):
    piano, violazioni = _pianifica(AIFinto(), [_gruppo(n_foto)], canali=canali)

    assert violazioni == []
    assert piano.provider == "finto"
    assert piano.modello == "finto"
    assert piano.versione_prompt == "finto-1"
    assert piano.contenuto["strategia"]


def test_il_piano_passa_il_controllo_con_piu_gruppi():
    gruppi = [_gruppo(2, id=1, da=1), _gruppo(3, id=2, da=10)]
    piano, violazioni = _pianifica(AIFinto(), gruppi)

    assert violazioni == []
    assert [u["gruppo_id"] for u in piano.contenuto["uscite"]] == [1, 1, 2, 2, 2, None]
    assert piano.contenuto["uscite"][2]["tema"] == "Vasi del gruppo 2"


def test_ca17_piano_sei_uscite_cinque_foto_e_un_immagine_ai():
    """CA-17, parte del piano: 5 foto, 6 post chiesti su 2 canali."""
    piano, violazioni = _pianifica(AIFinto(), [_gruppo(5)])
    uscite = piano.contenuto["uscite"]

    assert violazioni == []
    assert [u["numero"] for u in uscite] == [1, 2, 3, 4, 5, 6]
    for canale in DUE_CANALI:
        post = _post_del_canale(piano.contenuto, canale)
        assert [p["foto"] for p in post] == [[1], [2], [3], [4], [5], []]
        assert [p["riempitivo"] for p in post] == [None] * 5 + ["immagine_ai"]
        assert {p["formato"] for p in post} == {"singola"}
    assert uscite[5]["gruppo_id"] is None
    assert uscite[0]["gruppo_id"] == 1


def test_ca57_piano_con_poche_foto_i_post_che_mancano_sono_immagini_ai():
    """4 foto, 6 post chiesti: 2 immagini AI per canale, la stessa uscita su entrambi."""
    piano, violazioni = _pianifica(AIFinto(), [_gruppo(4)])
    uscite = piano.contenuto["uscite"]

    assert violazioni == []
    for canale in DUE_CANALI:
        post = _post_del_canale(piano.contenuto, canale)
        assert [p["foto"] for p in post] == [[1], [2], [3], [4], [], []]
        assert [p["riempitivo"] for p in post] == [None] * 4 + ["immagine_ai"] * 2
    # i temi dei riempitivi sono quelli del finto, senza gruppo
    assert [u["gruppo_id"] for u in uscite] == [1, 1, 1, 1, None, None]
    assert uscite[4]["tema"] != uscite[5]["tema"]


def test_ca57_piano_senza_foto_e_tutto_di_immagini_ai():
    piano, violazioni = _pianifica(AIFinto(), [_gruppo(0)])

    assert violazioni == []
    post = [p for u in piano.contenuto["uscite"] for p in u["post"]]
    assert len(post) == 12
    assert {p["riempitivo"] for p in post} == {"immagine_ai"}
    assert all(p["foto"] == [] and p["formato"] == "singola" for p in post)


def test_ca80_piano_con_le_sole_foto_preselezionate():
    """10 foto idonee, 6 post chiesti: le 6 di punteggio più alto, una per post."""
    punteggi = [3, 5, 1, 4, 2, 5, 4, 1, 3, 2]
    piano, violazioni = _pianifica(AIFinto(), [_gruppo(10, punteggi=punteggi)])

    assert violazioni == []
    for canale in DUE_CANALI:
        post = _post_del_canale(piano.contenuto, canale)
        assert [p["foto"] for p in post] == [[2], [6], [4], [7], [1], [9]]
        assert {p["riempitivo"] for p in post} == {None}
    usate = {f for u in piano.contenuto["uscite"] for p in u["post"] for f in p["foto"]}
    assert usate == {1, 2, 4, 6, 7, 9}


def test_piano_uguale_a_parita_di_dati():
    primo, _ = _pianifica(AIFinto(), [_gruppo(5)])
    secondo, _ = _pianifica(AIFinto(), [_gruppo(5)])
    assert primo == secondo


def test_piano_date_distribuite_e_instagram_il_giorno_dopo_facebook():
    piano, _ = _pianifica(AIFinto(), [_gruppo(6)])

    facebook = [
        datetime.fromisoformat(p["data_ora"])
        for p in _post_del_canale(piano.contenuto, "facebook")
    ]
    instagram = [
        datetime.fromisoformat(p["data_ora"])
        for p in _post_del_canale(piano.contenuto, "instagram")
    ]

    assert [d.date() for d in facebook] == [
        date(2030, 1, 7),
        date(2030, 1, 9),
        date(2030, 1, 11),
        date(2030, 1, 14),
        date(2030, 1, 16),
        date(2030, 1, 18),
    ]
    assert all(i - f == timedelta(days=1) for f, i in zip(facebook, instagram))
    assert {d.hour for d in facebook + instagram} == {10}


def test_piano_senza_facebook_instagram_non_slitta():
    piano, _ = _pianifica(AIFinto(), [_gruppo(6)], canali=("instagram",))
    primo = _post_del_canale(piano.contenuto, "instagram")[0]
    assert datetime.fromisoformat(primo["data_ora"]).date() == INIZIO


def test_piano_a_campagna_iniziata_usa_solo_i_giorni_che_restano():
    """Una Riprova a metà periodo: nessun post nel passato."""
    adesso = datetime(2030, 1, 15, 14, tzinfo=timezone.utc)
    piano, violazioni = _pianifica(AIFinto(), [_gruppo(6)], adesso=adesso)

    assert violazioni == []
    date_dei_post = {
        datetime.fromisoformat(p["data_ora"]).date()
        for u in piano.contenuto["uscite"]
        for p in u["post"]
    }
    assert min(date_dei_post) == date(2030, 1, 16)
    assert max(date_dei_post) <= FINE


def test_piano_a_periodo_finito_non_passa_il_controllo_delle_date():
    adesso = datetime(2030, 2, 1, 9, tzinfo=timezone.utc)
    _, violazioni = _pianifica(AIFinto(), [_gruppo(6)], adesso=adesso)
    assert {v["regola"] for v in violazioni} == {"data_nel_passato"}


def test_piano_con_un_carosello_a_comando_solo_se_avanzano_foto():
    """CA-52, parte del piano (carosello congelato): servono foto oltre i post chiesti."""
    limiti = {
        canale: {
            "post_chiesti": 6,
            "foto_disponibili": list(range(1, 9)),
            "foto_riempitivo": [],
            "riempitivi": 0,
        }
        for canale in DUE_CANALI
    }
    piano = AIFinto(carosello=True).pianifica_campagna(
        SNAPSHOT,
        CAMPAGNA,
        [_gruppo(8)],
        limiti,
        domain.SCHEDE_CANALE,
        non_prima_di=ADESSO + timedelta(minutes=MARGINE),
    )

    for canale in DUE_CANALI:
        primo = _post_del_canale(piano.contenuto, canale)[0]
        assert primo["formato"] == "carosello"
        assert primo["foto"] == [1, 7]


@pytest.mark.parametrize("n_foto", [0, 4, 6, 8, 20])
def test_piano_senza_carosello_con_le_foto_preselezionate(n_foto):
    """Un post = una foto (A8): le foto preselezionate non superano i post chiesti."""
    piano, violazioni = _pianifica(AIFinto(carosello=True), [_gruppo(n_foto)])

    assert violazioni == []
    formati = {p["formato"] for u in piano.contenuto["uscite"] for p in u["post"]}
    assert formati == {"singola"}


def test_piano_non_valido_a_comando_poi_valido():
    """R-09: il primo piano non passa il controllo, la riscrittura sì."""
    finto = AIFinto()
    finto.comanda_piano_non_valido(1)
    gruppi = [_gruppo(6)]

    scartato, violazioni = _pianifica(finto, gruppi)
    assert [v["regola"] for v in violazioni] == ["post_per_canale"] * 2

    _, violazioni = _pianifica(
        finto, gruppi, piano_precedente=scartato.contenuto, violazioni=violazioni
    )
    assert violazioni == []
    assert [c["riscrittura"] for c in finto.chiamate] == [False, True]


# --- Testi --------------------------------------------------------------------


@pytest.mark.parametrize("canale", sorted(domain.SCHEDE_CANALE))
def test_testo_e_hashtag_dentro_i_limiti_editoriali_del_canale(canale):
    scritto = _scrivi(AIFinto(), canale)
    scheda = domain.SCHEDE_CANALE[canale]

    assert "Vasi in terracotta" in scritto.testo
    assert "Bottega di prova" in scritto.testo
    assert len(scritto.testo) <= scheda["max_caratteri"]
    assert 0 < len(scritto.hashtag) <= scheda["max_hashtag"]
    assert all(not tag.startswith("#") for tag in scritto.hashtag)
    assert (scritto.provider, scritto.modello) == ("finto", "finto")
    assert scritto.versione_prompt == "finto-1"


def test_testo_uguale_a_parita_di_dati():
    assert _scrivi(AIFinto()) == _scrivi(AIFinto())


def test_testo_a_comando_per_le_riscritture():
    """CA-18, parte dell'adattatore: un testo vuoto per due volte, poi quello buono."""
    finto = AIFinto()
    finto.comanda_testo("", volte=2)

    assert _scrivi(finto).testo == ""
    riscritto = _scrivi(finto, testo_precedente="", violazioni=[{"livello": "blocco"}])
    assert riscritto.testo == ""
    assert riscritto.hashtag == []
    assert _scrivi(finto, testo_precedente="").testo != ""
    assert [c["riscrittura"] for c in finto.chiamate] == [False, True, True]


def test_testo_a_comando_solo_su_un_canale():
    finto = AIFinto()
    finto.comanda_testo(
        "Testo lungo " * 100, ["uno", "due"], volte=None, canale="facebook"
    )

    assert len(_scrivi(finto, "facebook").testo) > 500
    assert _scrivi(finto, "facebook").hashtag == ["uno", "due"]
    assert len(_scrivi(finto, "instagram").testo) < 500


# --- Immagini AI (T3-34, spec R-28, R-43, R-44) -----------------------------------


def test_il_finto_crea_sempre_la_stessa_immagine_quadrata():
    finto = AIFinto()

    prima = finto.genera_immagine("Un prompt")
    seconda = finto.genera_immagine("Un altro prompt")

    assert prima.contenuto == seconda.contenuto
    assert (prima.mime, prima.provider, prima.modello) == (
        "image/png",
        "finto",
        "finto",
    )
    assert prima.versione_prompt == "finto-1"
    with Image.open(BytesIO(prima.contenuto)) as aperta:
        assert aperta.format == "PNG"
        assert aperta.width == aperta.height


def test_il_finto_registra_la_chiamata_e_il_suo_uso():
    finto = AIFinto(costo_chiamata=Decimal("0.04"))

    finto.genera_immagine("Un prompt")

    assert finto.chiamate == [{"operazione": "genera_immagine", "prompt": "Un prompt"}]
    uso = finto.ultimo_uso
    assert (uso.tipo, uso.provider, uso.modello) == ("immagine", "finto", "finto")
    assert (uso.immagini, uso.costo_usd) == (1, Decimal("0.04"))
    assert (uso.token_ingresso, uso.token_uscita) == (None, None)
