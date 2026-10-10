"""T1-31: adattatore AI e provider finto, senza nessuna chiamata di rete.

- Il piano del provider finto passa il controllo di T1-32.
- Un test per tipo di errore di R-35, su ogni operazione.
"""

import sys
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

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


def _gruppo(n_foto: int, *, stelle=(), id: int = 1, da: int = 1) -> GruppoAI:
    """Un gruppo con ``n_foto`` foto idonee e diverse, già analizzate."""
    return GruppoAI(
        id=id,
        descrizione=f"Vasi del gruppo {id}",
        foto=[
            FotoAI(
                id=numero,
                file=f"{numero}.jpg",
                mime="image/jpeg",
                da_usare=numero in stelle,
                analisi={"idonea": True, "simile_a": None},
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
            foto=[
                SimpleNamespace(id=f.id, da_usare=f.da_usare, analisi_ai=f.analisi)
                for f in gruppo.foto
            ],
        )
        for gruppo in gruppi
    ]


def _voce(foto_id: int, *, mai_uscita: bool = True, gruppo_id: int = 9):
    """Una foto d'archivio, come la dà ``campagne.service.foto_di_archivio()``."""
    return SimpleNamespace(
        foto=SimpleNamespace(
            id=foto_id, da_usare=False, analisi_ai={"idonea": True, "simile_a": None}
        ),
        gruppo=SimpleNamespace(id=gruppo_id),
        mai_uscita=mai_uscita,
    )


def _pianifica(
    finto: AIFinto,
    gruppi,
    *,
    canali=DUE_CANALI,
    adesso=ADESSO,
    archivio=None,
    **altro,
):
    """Piano del provider finto e violazioni trovate dal controllo di T1-32.

    ``archivio`` ha le foto d'archivio di ogni canale; i loro gruppi stanno in
    ``gruppi``, segnati con ``archivio=True``.
    """
    visti = _come_li_vede_il_controllo([g for g in gruppi if not g.archivio])
    limiti = limiti_per_canale(canali, 3, INIZIO, FINE, visti, archivio)
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
        archivio=archivio,
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


def test_ottieni_ai_con_un_provider_non_disponibile_e_un_errore_di_configurazione(
    monkeypatch,
):
    """CA-58, parte dell'adattatore: `AI_PROVIDER=litellm` non c'è ancora."""
    monkeypatch.setattr(
        modulo_ai, "leggi_impostazioni", lambda: SimpleNamespace(ai_provider="litellm")
    )
    with pytest.raises(ErroreAI) as sollevato:
        ottieni_ai()
    assert sollevato.value.tipo == "configurazione"
    assert "litellm" in sollevato.value.messaggio


def test_usa_ai_ripristina_il_provider_precedente():
    primo = ottieni_ai()
    altro = AIFinto()
    with usa_ai(altro):
        assert ottieni_ai() is altro
    assert ottieni_ai() is primo


def test_nessuna_libreria_di_rete_caricata_dall_adattatore():
    """LiteLLM non si usa nei test: il provider finto non lo importa."""
    assert isinstance(ottieni_ai(), AIFinto)
    assert "litellm" not in sys.modules
    assert "openai" not in sys.modules


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
    """CA-51, parte dell'adattatore."""
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


def test_ca17_piano_sei_uscite_cinque_foto_e_una_cartolina():
    """CA-17, parte del piano: 5 foto, 6 post chiesti su 2 canali."""
    piano, violazioni = _pianifica(AIFinto(), [_gruppo(5)])
    uscite = piano.contenuto["uscite"]

    assert violazioni == []
    assert [u["numero"] for u in uscite] == [1, 2, 3, 4, 5, 6]
    for canale in DUE_CANALI:
        post = _post_del_canale(piano.contenuto, canale)
        assert [p["foto"] for p in post] == [[1], [2], [3], [4], [5], []]
        assert [p["riempitivo"] for p in post] == [None] * 5 + ["cartolina"]
        assert {p["formato"] for p in post} == {"singola"}
    assert uscite[5]["gruppo_id"] is None
    assert uscite[0]["gruppo_id"] == 1


def test_ca76_piano_prima_le_foto_poi_l_archivio_gia_uscito_poi_le_cartoline():
    """CA-76, parte del piano: 3 foto, 2 d'archivio; la 11 su Facebook è già uscita."""
    d_archivio = _gruppo(2, id=9, da=10)
    d_archivio.archivio = True
    archivio = {
        "facebook": [_voce(10), _voce(11, mai_uscita=False)],
        "instagram": [_voce(10), _voce(11)],
    }

    piano, violazioni = _pianifica(
        AIFinto(), [_gruppo(3), d_archivio], archivio=archivio
    )
    uscite = piano.contenuto["uscite"]

    assert violazioni == []
    facebook = _post_del_canale(piano.contenuto, "facebook")
    assert [p["foto"] for p in facebook] == [[1], [2], [3], [10], [11], []]
    assert [p["riempitivo"] for p in facebook] == [None] * 4 + ["archivio", "cartolina"]
    instagram = _post_del_canale(piano.contenuto, "instagram")
    assert [p["foto"] for p in instagram] == [[1], [2], [3], [10], [11], []]
    assert [p["riempitivo"] for p in instagram] == [None] * 5 + ["cartolina"]
    assert {p["formato"] for p in facebook + instagram} == {"singola"}
    # l'uscita con una foto d'archivio prende gruppo e tema dall'archivio
    assert [u["gruppo_id"] for u in uscite] == [1, 1, 1, 9, 9, None]
    assert uscite[3]["tema"] == "Vasi del gruppo 9"


def test_piano_con_piu_foto_d_archivio_gia_uscite_dei_riempitivi_che_servono():
    """Le foto d'archivio che avanzano restano fuori: nessuna cartolina."""
    d_archivio = _gruppo(3, id=9, da=20)
    d_archivio.archivio = True
    archivio = {"instagram": [_voce(n, mai_uscita=False) for n in (20, 21, 22)]}

    piano, violazioni = _pianifica(
        AIFinto(carosello=True),
        [_gruppo(4), d_archivio],
        canali=("instagram",),
        archivio=archivio,
    )

    assert violazioni == []
    post = _post_del_canale(piano.contenuto, "instagram")
    assert [p["foto"] for p in post] == [[1], [2], [3], [4], [20], [21]]
    assert [p["riempitivo"] for p in post] == [None] * 4 + ["archivio"] * 2
    assert {p["formato"] for p in post} == {"singola"}


def test_piano_uguale_a_parita_di_dati():
    primo, _ = _pianifica(AIFinto(), [_gruppo(5, stelle={4})])
    secondo, _ = _pianifica(AIFinto(), [_gruppo(5, stelle={4})])
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


@pytest.mark.parametrize("stelle", [{9}, {7, 8, 9}, set(range(1, 10))])
def test_piano_con_le_foto_con_la_stella_per_prime(stelle):
    """CA-51, parte del piano: anche con più stelle che post chiesti (#45)."""
    piano, violazioni = _pianifica(AIFinto(), [_gruppo(9, stelle=stelle)])

    assert violazioni == []
    usate = {
        foto
        for p in _post_del_canale(piano.contenuto, "facebook")
        for foto in p["foto"]
    }
    assert len(usate & stelle) == min(len(stelle), 6)


def test_piano_con_un_carosello_a_comando():
    """CA-52, parte del piano: più foto in un post, dove non ci sono riempitivi."""
    piano, violazioni = _pianifica(AIFinto(carosello=True), [_gruppo(8)])

    assert violazioni == []
    for canale in DUE_CANALI:
        primo = _post_del_canale(piano.contenuto, canale)[0]
        assert primo["formato"] == "carosello"
        assert primo["foto"] == [1, 7]


@pytest.mark.parametrize("n_foto", [4, 6])
def test_piano_senza_carosello_se_servono_riempitivi_o_non_avanzano_foto(n_foto):
    """CA-57, parte del piano: su un canale con riempitivi nessun carosello."""
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
