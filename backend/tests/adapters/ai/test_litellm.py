"""T3-31: adattatore LiteLLM, senza rete (brief-ai, spec R-35 e R-44).

``litellm.completion`` è sostituito da una funzione che risponde con un JSON,
oppure solleva l'eccezione da provare: un test per ogni riga della tabella degli
errori, uno per ``ultimo_uso``.
"""

import base64
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

import httpx
import litellm
import pytest
from PIL import Image

import app.adapters.ai.litellm as modulo
from app.adapters.ai import (
    CampagnaAI,
    ErroreAI,
    FotoAI,
    GruppoAI,
    PostAI,
    ottieni_ai,
    prompt_immagine,
)
from app.adapters.ai.litellm import AILiteLLM
from app.adapters.ai.schemi import TipoFoto
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.config import leggi_impostazioni
from app.core.orologio import ROMA
from app.moduli.campagne.domain import TIPI_CONTENUTO
from app.moduli.contenuti import domain
from app.moduli.contenuti.piano import controlla_piano, limiti_per_canale

INIZIO = date(2030, 1, 7)
FINE = date(2030, 1, 20)
ADESSO = datetime(2030, 1, 1, 9, tzinfo=timezone.utc)
CAMPAGNA = CampagnaAI(titolo="Campagna di prova", inizio=INIZIO, fine=FINE)
SNAPSHOT = {
    "nome": "Bottega di prova",
    "referente": "Una Persona",
    "citta": "Deruta",
    "vincoli": "Non parlare di sconti.",
}
ARGOMENTI = dict(model="m", llm_provider="openai")


# --- Strumenti -----------------------------------------------------------------


class Finta:
    """Sostituisce ``litellm.completion``: registra le chiamate e risponde."""

    def __init__(self) -> None:
        self.chiamate: list[dict] = []
        self.risposte: list = []

    def metti(self, *risposte) -> None:
        self.risposte.extend(risposte)

    def __call__(self, **argomenti):
        self.chiamate.append(argomenti)
        risposta = self.risposte.pop(0)
        if isinstance(risposta, Exception):
            raise risposta
        return risposta


def risposta(contenuto, *, fine="stop", rifiuto=None, token=(120, 30)):
    testo = contenuto if isinstance(contenuto, str) else json.dumps(contenuto)
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason=fine,
                message=SimpleNamespace(content=testo, refusal=rifiuto),
            )
        ],
        usage=SimpleNamespace(prompt_tokens=token[0], completion_tokens=token[1]),
    )


@pytest.fixture
def completion(monkeypatch) -> Finta:
    finta = Finta()
    monkeypatch.setattr(litellm, "completion", finta)
    monkeypatch.setattr(litellm, "completion_cost", lambda **_: 0.0125)
    return finta


@pytest.fixture
def archivio():
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


@pytest.fixture
def ai(monkeypatch) -> AILiteLLM:
    impostazioni = leggi_impostazioni().model_copy(
        update={
            "ai_provider": "litellm",
            "ai_modello_visione": "visione-di-prova",
            "ai_modello_testo": "testo-di-prova",
            "ai_modello_immagini": "immagini-di-prova",
            "ai_prezzo_immagine": Decimal("0.04"),
            "openai_api_key": "chiave-di-prova",
            "ai_prezzo_ingresso_milione": Decimal("2"),
            "ai_prezzo_uscita_milione": Decimal("10"),
        }
    )
    monkeypatch.setattr(modulo, "leggi_impostazioni", lambda: impostazioni)
    return AILiteLLM()


def _immagine(lato_lungo: int = 2000, formato: str = "PNG") -> bytes:
    uscita = BytesIO()
    Image.new("RGB", (lato_lungo, lato_lungo // 2), (180, 90, 40)).save(uscita, formato)
    return uscita.getvalue()


def _gruppo(archivio: ArchivioFinto, n_foto: int = 2, *, da: int = 1) -> GruppoAI:
    foto = [
        FotoAI(
            id=numero,
            file=archivio.salva(_immagine(), "png"),
            mime="image/png",
        )
        for numero in range(da, da + n_foto)
    ]
    return GruppoAI(id=1, descrizione="Vasi in terracotta", foto=foto)


def _voce(foto_id: int, **campi) -> dict:
    dati = dict(
        foto_id=foto_id,
        soggetto="Un vaso di terracotta",
        descrizione="Un vaso di terracotta rossa su un tavolo di legno chiaro.",
        tipo="pezzo_finito",
        idonea=True,
        motivo=None,
        punteggio=4,
        simile_a=None,
        persone_riconoscibili=False,
        marchi_visibili=False,
    )
    dati.update(campi)
    return dati


def _analisi_di(*voci: dict) -> dict:
    return {"foto": list(voci)}


def _errore(classe, messaggio="errore", **altro):
    return classe(message=messaggio, **{**ARGOMENTI, **altro})


# --- Errori (R-35): una riga della tabella per test --------------------------


@pytest.mark.parametrize(
    ("eccezione", "tipo"),
    [
        (_errore(litellm.Timeout), "temporaneo"),
        (_errore(litellm.ServiceUnavailableError), "temporaneo"),
        (_errore(litellm.InternalServerError), "temporaneo"),
        (_errore(litellm.BadGatewayError), "temporaneo"),
        (_errore(litellm.RateLimitError, "Rate limit reached"), "temporaneo"),
        (
            litellm.APIConnectionError(
                message="rete", llm_provider="openai", model="m", request=None
            ),
            "temporaneo",
        ),
        (
            litellm.APIError(
                status_code=502, message="x", llm_provider="openai", model="m"
            ),
            "temporaneo",
        ),
        (
            _errore(litellm.AuthenticationError, "Incorrect API key sk-1234"),
            "configurazione",
        ),
        (
            _errore(
                litellm.PermissionDeniedError,
                response=httpx.Response(
                    403, request=httpx.Request("POST", "http://prova")
                ),
            ),
            "configurazione",
        ),
        (_errore(litellm.NotFoundError, "model not found"), "configurazione"),
        (
            _errore(
                litellm.RateLimitError,
                "You exceeded your current quota: insufficient_quota",
            ),
            "configurazione",
        ),
        (
            _errore(litellm.BadRequestError, "LLM Provider NOT provided"),
            "configurazione",
        ),
        (_errore(litellm.ContextWindowExceededError), "richiesta"),
        (_errore(litellm.BadRequestError, "richiesta sbagliata"), "richiesta"),
        (
            litellm.APIError(
                status_code=413, message="x", llm_provider="openai", model="m"
            ),
            "richiesta",
        ),
        (_errore(litellm.ContentPolicyViolationError), "rifiuto"),
    ],
)
def test_ogni_errore_del_provider_diventa_uno_dei_cinque_tipi(
    completion, ai, eccezione, tipo
):
    completion.metti(eccezione)
    with pytest.raises(ErroreAI) as sollevato:
        ai.genera_post(SNAPSHOT, CAMPAGNA, _post(), domain.SCHEDE_CANALE["instagram"])
    assert sollevato.value.tipo == tipo
    assert ai.ultimo_uso is None


def test_il_messaggio_per_l_operatore_non_riporta_il_testo_del_provider(completion, ai):
    completion.metti(
        _errore(litellm.AuthenticationError, "Incorrect API key: sk-SEGRETO")
    )
    with pytest.raises(ErroreAI) as sollevato:
        ai.genera_post(SNAPSHOT, CAMPAGNA, _post(), domain.SCHEDE_CANALE["instagram"])
    assert "sk-SEGRETO" not in sollevato.value.messaggio


@pytest.mark.parametrize(
    "ricevuta",
    [
        risposta(""),
        risposta("non è json"),
        risposta({"testo": "manca l'altro campo"}),
        risposta({"testo": 5, "hashtag": []}),
        risposta('{"testo": "Troncato', fine="length"),
        SimpleNamespace(choices=[], usage=None),
    ],
)
def test_una_risposta_vuota_troncata_o_fuori_schema_e_di_tipo_risposta(
    completion, ai, ricevuta
):
    completion.metti(ricevuta)
    with pytest.raises(ErroreAI) as sollevato:
        ai.genera_post(SNAPSHOT, CAMPAGNA, _post(), domain.SCHEDE_CANALE["instagram"])
    assert sollevato.value.tipo == "risposta"


def test_il_filtro_dei_contenuti_nella_risposta_e_un_rifiuto(completion, ai):
    completion.metti(risposta("", fine="content_filter"))
    completion.metti(risposta("", rifiuto="Non posso aiutarti."))
    for _ in range(2):
        with pytest.raises(ErroreAI) as sollevato:
            ai.genera_post(
                SNAPSHOT, CAMPAGNA, _post(), domain.SCHEDE_CANALE["instagram"]
            )
        assert sollevato.value.tipo == "rifiuto"


def test_un_errore_che_non_e_del_provider_non_si_nasconde(completion, ai):
    completion.metti(KeyError("bug"))
    with pytest.raises(KeyError):
        ai.genera_post(SNAPSHOT, CAMPAGNA, _post(), domain.SCHEDE_CANALE["instagram"])


# --- Uso e costo (R-44) --------------------------------------------------------


def _post(**campi) -> PostAI:
    dati = dict(
        canale="instagram",
        tema="Vasi in terracotta",
        formato="singola",
        data_ora=datetime(2030, 1, 8, 10, tzinfo=ROMA),
        foto=[
            FotoAI(
                id=1,
                file="1.jpg",
                mime="image/jpeg",
                analisi={"soggetto": "Un vaso", "punteggio": 4},
            )
        ],
    )
    dati.update(campi)
    return PostAI(**dati)


def test_ultimo_uso_ha_modello_token_e_costo_di_litellm(completion, ai):
    completion.metti(risposta({"testo": "Un vaso.", "hashtag": ["#vasi"]}))
    scritto = ai.genera_post(
        SNAPSHOT, CAMPAGNA, _post(), domain.SCHEDE_CANALE["instagram"]
    )
    uso = ai.ultimo_uso
    assert (uso.tipo, uso.provider, uso.modello) == (
        "testo",
        "litellm",
        "testo-di-prova",
    )
    assert (uso.token_ingresso, uso.token_uscita) == (120, 30)
    assert uso.costo_usd == Decimal("0.0125")
    assert scritto.hashtag == ["vasi"]
    assert (scritto.provider, scritto.modello, scritto.versione_prompt) == (
        "litellm",
        "testo-di-prova",
        "post_v2",
    )


def test_senza_il_prezzo_di_litellm_vale_quello_della_configurazione(
    completion, ai, monkeypatch
):
    def sconosciuto(**_):
        raise litellm.NotFoundError(message="senza prezzo", **ARGOMENTI)

    monkeypatch.setattr(litellm, "completion_cost", sconosciuto)
    completion.metti(
        risposta({"testo": "Un vaso.", "hashtag": []}, token=(1_000_000, 500_000))
    )
    ai.genera_post(SNAPSHOT, CAMPAGNA, _post(), domain.SCHEDE_CANALE["instagram"])
    # 1 milione in ingresso a 2 dollari + mezzo milione in uscita a 10
    assert ai.ultimo_uso.costo_usd == Decimal("7")


def test_un_errore_cancella_l_uso_della_chiamata_di_prima(completion, ai):
    completion.metti(
        risposta({"testo": "Un vaso.", "hashtag": []}),
        _errore(litellm.Timeout),
    )
    ai.genera_post(SNAPSHOT, CAMPAGNA, _post(), domain.SCHEDE_CANALE["instagram"])
    assert ai.ultimo_uso is not None
    with pytest.raises(ErroreAI):
        ai.genera_post(SNAPSHOT, CAMPAGNA, _post(), domain.SCHEDE_CANALE["instagram"])
    assert ai.ultimo_uso is None


# --- Chiamata ------------------------------------------------------------------


def test_la_chiamata_usa_schema_chiave_e_nessun_tentativo_di_litellm(completion, ai):
    completion.metti(risposta({"testo": "Un vaso.", "hashtag": []}))
    ai.genera_post(SNAPSHOT, CAMPAGNA, _post(), domain.SCHEDE_CANALE["instagram"])
    chiamata = completion.chiamate[0]
    assert chiamata["model"] == "testo-di-prova"
    assert chiamata["response_format"].__name__ == "RispostaPost"
    assert chiamata["api_key"] == "chiave-di-prova"
    assert chiamata["num_retries"] == 0
    sistema, utente = chiamata["messages"]
    assert sistema["role"] == "system"
    assert "copywriter" in sistema["content"]
    dati = json.loads(utente["content"])
    assert dati["bottega"] == {
        "nome": "Bottega di prova",
        "citta": "Deruta",
        "vincoli": "Non parlare di sconti.",
    }  # senza il referente
    assert dati["post"]["foto"] == [{"soggetto": "Un vaso", "punteggio": 4}]
    assert "immagine_ai" not in dati["post"]


def test_il_post_con_immagine_ai_manda_cio_che_l_immagine_mostra(completion, ai):
    completion.metti(risposta({"testo": "Il banco.", "hashtag": []}))
    post = _post(foto=[], riempitivo="immagine_ai", immagine_ai="Il banco di lavoro")
    ai.genera_post(SNAPSHOT, CAMPAGNA, post, domain.SCHEDE_CANALE["instagram"])
    dati = json.loads(completion.chiamate[0]["messages"][1]["content"])
    assert dati["post"]["immagine_ai"] == "Il banco di lavoro"
    assert dati["post"]["immagine_creata_con_ai"] is True


def test_le_rigenerazioni_mandano_versioni_scartate_proposta_e_nota(completion, ai):
    completion.metti(risposta({"testo": "Nuovo.", "hashtag": []}))
    ai.genera_post(
        SNAPSHOT,
        CAMPAGNA,
        _post(),
        domain.SCHEDE_CANALE["instagram"],
        testo_precedente="Troppo lungo",
        violazioni=[{"messaggio": "Supera i 600 caratteri."}],
        versioni_rifiutate=["Prima versione"],
        testo_proposto="Parti da qui",
        nota="Più caldo",
    )
    dati = json.loads(completion.chiamate[0]["messages"][1]["content"])
    assert dati["testo_precedente"] == "Troppo lungo"
    assert dati["violazioni"] == ["Supera i 600 caratteri."]
    assert dati["versioni_rifiutate"] == ["Prima versione"]
    assert dati["testo_proposto"] == "Parti da qui"
    assert dati["nota"] == "Più caldo"


# --- Analisi -------------------------------------------------------------------


def test_analisi_una_chiamata_per_gruppo_con_foto_ridotte_a_1024(
    completion, ai, archivio
):
    gruppo = _gruppo(archivio, 2)
    completion.metti(risposta(_analisi_di(_voce(1), _voce(2, punteggio=5))))
    analisi = ai.analizza_gruppo(gruppo)

    assert len(completion.chiamate) == 1
    chiamata = completion.chiamate[0]
    assert chiamata["model"] == "visione-di-prova"
    parti = chiamata["messages"][1]["content"]
    immagini = [p["image_url"] for p in parti if p["type"] == "image_url"]
    assert len(immagini) == 2
    for immagine in immagini:
        assert immagine["detail"] == "high"
        assert immagine["url"].startswith("data:image/jpeg;base64,")
    testi = [p["text"] for p in parti if p["type"] == "text"]
    assert "Foto 1:" in testi and "Foto 2:" in testi

    assert set(analisi) == {1, 2}
    assert analisi[1] == {
        "idonea": True,
        "simile_a": None,
        "tipo": "pezzo_finito",
        "punteggio": 4,
        "motivo": None,
        "soggetto": "Un vaso di terracotta",
        "descrizione": "Un vaso di terracotta rossa su un tavolo di legno chiaro.",
        "persone_riconoscibili": False,
        "marchi_visibili": False,
    }
    assert analisi[2]["punteggio"] == 5
    assert ai.ultimo_uso.tipo == "analisi"
    assert ai.ultimo_uso.modello == "visione-di-prova"


def test_la_foto_mandata_all_analisi_e_jpeg_di_al_massimo_1024_px(archivio):
    import base64

    foto = FotoAI(id=1, file=archivio.salva(_immagine(3000), "png"), mime="image/png")
    parte = modulo._foto_per_ai(foto)
    dati = base64.b64decode(parte["image_url"]["url"].split(",", 1)[1])
    with Image.open(BytesIO(dati)) as inviata:
        assert inviata.format == "JPEG"
        assert max(inviata.size) == 1024


def test_il_soggetto_ha_al_massimo_15_parole(completion, ai, archivio):
    gruppo = _gruppo(archivio, 1)
    lungo = " ".join(f"parola{n}" for n in range(30))
    completion.metti(risposta(_analisi_di(_voce(1, soggetto=lungo))))
    assert len(ai.analizza_gruppo(gruppo)[1]["soggetto"].split()) == 15


def test_la_descrizione_ha_al_massimo_60_parole(completion, ai, archivio):
    gruppo = _gruppo(archivio, 1)
    lunga = " ".join(f"parola{n}" for n in range(100))
    completion.metti(risposta(_analisi_di(_voce(1, descrizione=lunga))))
    assert len(ai.analizza_gruppo(gruppo)[1]["descrizione"].split()) == 60


def test_due_foto_che_si_dicono_doppioni_a_vicenda_ne_lasciano_una_libera(
    completion, ai, archivio
):
    gruppo = _gruppo(archivio, 3)
    completion.metti(
        risposta(
            _analisi_di(
                _voce(1, simile_a=2, punteggio=3),
                _voce(2, simile_a=1, punteggio=5),
                _voce(3, simile_a=3),
            )
        )
    )
    analisi = ai.analizza_gruppo(gruppo)
    assert analisi[1]["simile_a"] == 2  # la peggiore punta alla migliore
    assert analisi[2]["simile_a"] is None
    assert analisi[3]["simile_a"] is None  # una foto non è doppione di se stessa


def test_un_doppione_di_una_foto_che_non_c_e_non_conta(completion, ai, archivio):
    gruppo = _gruppo(archivio, 1)
    completion.metti(risposta(_analisi_di(_voce(1, simile_a=99))))
    assert ai.analizza_gruppo(gruppo)[1]["simile_a"] is None


def test_una_foto_non_idonea_ha_sempre_un_motivo(completion, ai, archivio):
    gruppo = _gruppo(archivio, 1)
    completion.metti(risposta(_analisi_di(_voce(1, idonea=False, motivo=None))))
    assert ai.analizza_gruppo(gruppo)[1]["motivo"]


@pytest.mark.parametrize(
    "voci",
    [
        [_voce(1)],  # manca la foto 2
        [_voce(1), _voce(3)],  # una foto che non c'è
        [_voce(1), _voce(1)],  # la stessa due volte
        [_voce(1), _voce(2, punteggio=9)],  # punteggio fuori misura
        [_voce(1), _voce(2, tipo="strano")],  # tipo che non esiste
    ],
)
def test_un_analisi_incompleta_o_fuori_schema_e_di_tipo_risposta(
    completion, ai, archivio, voci
):
    gruppo = _gruppo(archivio, 2)
    completion.metti(risposta(_analisi_di(*voci)))
    with pytest.raises(ErroreAI) as sollevato:
        ai.analizza_gruppo(gruppo)
    assert sollevato.value.tipo == "risposta"


def test_una_foto_mancante_dall_archivio_e_una_richiesta_su_quella_foto(
    completion, ai, archivio
):
    gruppo = _gruppo(archivio, 2)
    archivio.elimina(gruppo.foto[1].file)
    with pytest.raises(ErroreAI) as sollevato:
        ai.analizza_gruppo(gruppo)
    assert (sollevato.value.tipo, sollevato.value.foto_id) == ("richiesta", 2)
    assert completion.chiamate == []


def test_una_foto_illeggibile_e_una_richiesta_su_quella_foto(completion, ai, archivio):
    corrotta = archivio.salva(b"\xff\xd8\xff non e' un jpeg", "jpg")
    gruppo = GruppoAI(
        id=1, descrizione=None, foto=[FotoAI(id=7, file=corrotta, mime="image/jpeg")]
    )
    with pytest.raises(ErroreAI) as sollevato:
        ai.analizza_gruppo(gruppo)
    assert (sollevato.value.tipo, sollevato.value.foto_id) == ("richiesta", 7)


def test_l_errore_di_richiesta_su_un_gruppo_di_una_foto_riguarda_quella_foto(
    completion, ai, archivio
):
    gruppo = _gruppo(archivio, 1, da=5)
    completion.metti(_errore(litellm.ImageFetchError))
    with pytest.raises(ErroreAI) as sollevato:
        ai.analizza_gruppo(gruppo)
    assert (sollevato.value.tipo, sollevato.value.foto_id) == ("richiesta", 5)


def test_un_gruppo_senza_foto_non_chiama_l_ai(completion, ai):
    assert ai.analizza_gruppo(GruppoAI(id=1, descrizione=None)) == {}
    assert completion.chiamate == []
    assert ai.ultimo_uso is None


# --- Piano ---------------------------------------------------------------------


def test_il_piano_arriva_nella_forma_che_il_controllo_si_aspetta(completion, ai):
    foto = [
        FotoAI(id=n, file=f"{n}.jpg", mime="image/jpeg", analisi={"idonea": True})
        for n in (1, 2, 3)
    ]
    gruppo = GruppoAI(id=1, descrizione="Vasi", foto=foto)
    visti = [
        SimpleNamespace(
            id=1,
            origine="caricate",
            foto=[SimpleNamespace(id=f.id, analisi_ai=f.analisi) for f in foto],
        )
    ]
    limiti = limiti_per_canale(
        ["facebook"], 3, INIZIO, INIZIO + timedelta(days=6), visti
    )
    assert limiti["facebook"]["post_chiesti"] == 3
    piano = {
        "strategia": "Raccontare la bottega.",
        "uscite": [
            {
                "numero": numero,
                "tema": f"Tema {numero}",
                "gruppo_id": 1,
                "post": [
                    {
                        "canale": "facebook",
                        "formato": "singola",
                        "foto": [numero],
                        "riempitivo": None,
                        "data_ora": f"2030-01-0{numero + 6}T10:00:00+01:00",
                    }
                ],
            }
            for numero in (1, 2, 3)
        ],
    }
    completion.metti(risposta(piano))
    scritto = ai.pianifica_campagna(
        SNAPSHOT,
        CAMPAGNA,
        [gruppo],
        limiti,
        domain.SCHEDE_CANALE,
        non_prima_di=ADESSO,
    )
    assert (scritto.provider, scritto.modello, scritto.versione_prompt) == (
        "litellm",
        "testo-di-prova",
        "piano_v2",
    )
    assert scritto.contenuto == piano
    assert (
        controlla_piano(
            scritto.contenuto,
            limiti=limiti,
            gruppi=visti,
            inizio=INIZIO,
            fine=INIZIO + timedelta(days=6),
            adesso=ADESSO,
            margine_minuti=15,
        )
        == []
    )
    assert ai.ultimo_uso.tipo == "piano"

    dati = json.loads(completion.chiamate[0]["messages"][1]["content"])
    assert dati["canali"]["facebook"]["post_chiesti"] == 3
    assert dati["canali"]["facebook"]["foto_disponibili"] == [1, 2, 3]
    assert "foto_riempitivo" not in dati["canali"]["facebook"]
    assert dati["non_prima_di"] == ADESSO.isoformat()
    assert "piano_precedente" not in dati


def test_il_piano_riscritto_riceve_il_precedente_e_le_violazioni(completion, ai):
    completion.metti(risposta({"strategia": "S", "uscite": []}))
    limiti = {
        "facebook": {
            "post_chiesti": 1,
            "foto_disponibili": [1],
            "foto_riempitivo": [],
            "riempitivi": 0,
        }
    }
    ai.pianifica_campagna(
        SNAPSHOT,
        CAMPAGNA,
        [],
        limiti,
        domain.SCHEDE_CANALE,
        non_prima_di=ADESSO,
        piano_precedente={"strategia": "vecchia", "uscite": []},
        violazioni=[
            {"regola": "post_per_canale", "messaggio": "Su facebook ne servono 1."}
        ],
    )
    dati = json.loads(completion.chiamate[0]["messages"][1]["content"])
    assert dati["piano_precedente"]["strategia"] == "vecchia"
    assert dati["violazioni"] == ["Su facebook ne servono 1."]


def test_al_piano_vanno_solo_le_foto_che_i_limiti_ammettono(completion, ai):
    foto = [
        FotoAI(id=n, file=f"{n}.jpg", mime="image/jpeg", analisi={"punteggio": n})
        for n in (1, 2, 3)
    ]
    limiti = {
        "facebook": {
            "post_chiesti": 1,
            "foto_disponibili": [3],
            "foto_riempitivo": [],
            "riempitivi": 0,
        }
    }
    completion.metti(risposta({"strategia": "S", "uscite": []}))
    ai.pianifica_campagna(
        SNAPSHOT,
        CAMPAGNA,
        [GruppoAI(id=1, descrizione=None, foto=foto)],
        limiti,
        domain.SCHEDE_CANALE,
        non_prima_di=ADESSO,
    )
    dati = json.loads(completion.chiamate[0]["messages"][1]["content"])
    assert [f["id"] for g in dati["gruppi"] for f in g["foto"]] == [3]


# --- Configurazione e coerenza -------------------------------------------------


def test_senza_il_modello_di_testo_l_adattatore_non_parte(monkeypatch):
    impostazioni = leggi_impostazioni().model_copy(
        update={"ai_modello_visione": "v", "ai_modello_testo": " "}
    )
    monkeypatch.setattr(modulo, "leggi_impostazioni", lambda: impostazioni)
    with pytest.raises(ErroreAI) as sollevato:
        AILiteLLM()
    assert sollevato.value.tipo == "configurazione"
    assert "AI_MODELLO_TESTO" in sollevato.value.messaggio


def test_ottieni_ai_con_litellm_crea_l_adattatore_vero(monkeypatch):
    import app.adapters.ai as pacchetto

    impostazioni = leggi_impostazioni().model_copy(
        update={
            "ai_provider": "litellm",
            "ai_modello_visione": "v",
            "ai_modello_testo": "t",
        }
    )
    monkeypatch.setattr(pacchetto, "leggi_impostazioni", lambda: impostazioni)
    monkeypatch.setattr(modulo, "leggi_impostazioni", lambda: impostazioni)
    pacchetto.imposta_ai(None)
    try:
        assert isinstance(ottieni_ai(), AILiteLLM)
    finally:
        pacchetto.imposta_ai(None)


def test_i_tipi_di_foto_dello_schema_sono_quelli_di_campagne():
    assert set(TipoFoto.__args__) == set(TIPI_CONTENUTO)


@pytest.mark.parametrize("nome", ["analisi_v2", "piano_v2", "post_v2"])
def test_i_prompt_esistono_e_hanno_la_versione_nel_nome(nome):
    assert modulo._prompt(nome).strip()


# --- Immagini (T3-34) ----------------------------------------------------------------


def _png(lato: int = 1024, formato: str = "PNG") -> str:
    uscita = BytesIO()
    Image.new("RGB", (lato, lato), (90, 120, 60)).save(uscita, formato)
    return base64.b64encode(uscita.getvalue()).decode()


def _immagine_ai(codificata: str | None, *, usage=None):
    return SimpleNamespace(
        data=[SimpleNamespace(b64_json=codificata, url=None)] if codificata else [],
        usage=usage,
    )


@pytest.fixture
def generazione(monkeypatch) -> Finta:
    finta = Finta()
    monkeypatch.setattr(litellm, "image_generation", finta)
    monkeypatch.setattr(litellm, "completion_cost", lambda **_: 0.0425)
    return finta


def test_l_immagine_si_chiede_quadrata_di_qualita_media_senza_tentativi_di_litellm(
    generazione, ai
):
    generazione.metti(_immagine_ai(_png()))

    immagine = ai.genera_immagine("Un prompt")

    (chiamata,) = generazione.chiamate
    assert chiamata["prompt"] == "Un prompt"
    assert chiamata["model"] == "immagini-di-prova"
    assert (chiamata["size"], chiamata["quality"], chiamata["n"]) == (
        "1024x1024",
        "medium",
        1,
    )
    assert chiamata["api_key"] == "chiave-di-prova"
    assert chiamata["timeout"] == modulo.TIMEOUT_SECONDI
    assert (immagine.mime, immagine.provider, immagine.modello) == (
        "image/png",
        "litellm",
        "immagini-di-prova",
    )
    assert immagine.versione_prompt == "immagine_v2"
    with Image.open(BytesIO(immagine.contenuto)) as aperta:
        assert aperta.size == (1024, 1024)


def test_un_jpeg_resta_un_jpeg(generazione, ai):
    generazione.metti(_immagine_ai(_png(formato="JPEG")))
    assert ai.genera_immagine("Un prompt").mime == "image/jpeg"


def test_ultimo_uso_dell_immagine_ha_modello_token_immagini_e_costo_di_litellm(
    generazione, ai
):
    generazione.metti(
        _immagine_ai(_png(), usage=SimpleNamespace(input_tokens=60, output_tokens=1056))
    )

    ai.genera_immagine("Un prompt")

    uso = ai.ultimo_uso
    assert (uso.tipo, uso.provider, uso.modello) == (
        "immagine",
        "litellm",
        "immagini-di-prova",
    )
    assert (uso.token_ingresso, uso.token_uscita, uso.immagini) == (60, 1056, 1)
    assert uso.costo_usd == Decimal("0.0425")


def test_senza_il_prezzo_di_litellm_l_immagine_costa_quanto_dice_la_configurazione(
    generazione, ai, monkeypatch
):
    def sconosciuto(**_):
        raise litellm.NotFoundError(message="senza prezzo", **ARGOMENTI)

    monkeypatch.setattr(litellm, "completion_cost", sconosciuto)
    generazione.metti(_immagine_ai(_png()))

    ai.genera_immagine("Un prompt")

    assert ai.ultimo_uso.costo_usd == Decimal("0.04")
    assert (ai.ultimo_uso.token_ingresso, ai.ultimo_uso.token_uscita) == (None, None)


@pytest.mark.parametrize(
    ("eccezione", "tipo"),
    [
        (_errore(litellm.Timeout), "temporaneo"),
        (_errore(litellm.RateLimitError, "Rate limit reached"), "temporaneo"),
        (_errore(litellm.ServiceUnavailableError), "temporaneo"),
        (_errore(litellm.AuthenticationError, "Incorrect API key"), "configurazione"),
        (_errore(litellm.NotFoundError, "model not found"), "configurazione"),
        (_errore(litellm.BadRequestError, "prompt non accettato"), "richiesta"),
        (_errore(litellm.ContentPolicyViolationError), "rifiuto"),
        (
            _errore(
                litellm.BadRequestError,
                "Your request was rejected by the safety system. moderation_blocked",
            ),
            "rifiuto",
        ),
    ],
)
def test_ogni_errore_dell_immagine_diventa_uno_dei_cinque_tipi(
    generazione, ai, eccezione, tipo
):
    generazione.metti(eccezione)

    with pytest.raises(ErroreAI) as sollevato:
        ai.genera_immagine("Un prompt")

    assert sollevato.value.tipo == tipo
    assert sollevato.value.foto_id is None
    assert ai.ultimo_uso is None
    assert "Incorrect API key" not in sollevato.value.messaggio


@pytest.mark.parametrize(
    "risposta_sbagliata",
    [
        _immagine_ai(None),
        _immagine_ai("non è base64!"),
        _immagine_ai(base64.b64encode(b"non e un immagine").decode()),
        _immagine_ai(_png(formato="WEBP")),
    ],
    ids=["vuota", "non_base64", "non_immagine", "formato_non_ammesso"],
)
def test_un_immagine_vuota_illeggibile_o_di_un_altro_formato_e_di_tipo_risposta(
    generazione, ai, risposta_sbagliata
):
    generazione.metti(risposta_sbagliata)

    with pytest.raises(ErroreAI) as sollevato:
        ai.genera_immagine("Un prompt")

    assert sollevato.value.tipo == "risposta"
    assert ai.ultimo_uso is None


def test_senza_il_modello_delle_immagini_la_chiamata_e_di_configurazione(
    generazione, ai, monkeypatch
):
    monkeypatch.setattr(ai, "_modello_immagini", " ")

    with pytest.raises(ErroreAI) as sollevato:
        ai.genera_immagine("Un prompt")

    assert sollevato.value.tipo == "configurazione"
    assert generazione.chiamate == []


def test_il_prompt_dell_immagine_esiste_con_la_versione_nel_nome():
    assert modulo._prompt("immagine_v2").strip()


# --- Prompt dell'immagine (R-43) -----------------------------------------------------

PROFILO = {
    "nome": "Ceramiche Bianchi",
    "citta": "Deruta",
    "tipo_prodotto": "ceramica_vetro",
    "tono": ["caldo", "professionale"],
}


def test_il_prompt_dell_immagine_e_quello_del_brief():
    prompt = prompt_immagine(PROFILO, "Il tornio al lavoro", date(2030, 1, 7))

    assert prompt == (
        "Fotografia realistica, quadrata, per una bottega di ceramica e vetro a Deruta.\n"
        "Soggetto: Il tornio al lavoro, mostrato attraverso ambiente, materiali o "
        "attrezzi della lavorazione.\n"
        "Inquadratura: un solo soggetto chiaro, ripreso da vicino o a mezza distanza, "
        "sfondo semplice e leggermente sfocato, come una foto scattata in bottega con "
        "una buona fotocamera.\n"
        "Stagione: inverno.\n"
        "Tono: caldo, professionale.\n"
        "Luce naturale, morbida, colori fedeli e caldi, senza effetti artificiali.\n"
        "Vincoli: nessun prodotto finito riconoscibile, nessuna persona riconoscibile, "
        "nessun testo, logo o marchio."
    )


@pytest.mark.parametrize(
    ("giorno", "stagione"),
    [
        (date(2030, 3, 1), "primavera"),
        (date(2030, 6, 30), "estate"),
        (date(2030, 9, 1), "autunno"),
        (date(2030, 12, 31), "inverno"),
    ],
)
def test_la_stagione_viene_dalla_data_del_post(giorno, stagione):
    assert f"Stagione: {stagione}." in prompt_immagine(PROFILO, "Tema", giorno)


def test_il_prompt_semplice_non_ha_ne_tono_ne_stagione_ma_tiene_i_vincoli():
    prompt = prompt_immagine(PROFILO, "Tema", date(2030, 1, 7), semplice=True)

    assert "Stagione" not in prompt and "Tono" not in prompt
    assert "Soggetto: Tema," in prompt
    assert "Luce naturale," in prompt
    assert "Vincoli: nessun prodotto finito riconoscibile" in prompt


def test_il_prompt_senza_citta_tono_o_tipo_di_prodotto_esce_comunque():
    prompt = prompt_immagine(
        {"tipo_prodotto": "altro", "tono": []}, "Tema", date(2030, 7, 1)
    )

    assert prompt.splitlines()[0] == (
        "Fotografia realistica, quadrata, per una bottega di prodotti artigianali."
    )
    assert "Tono" not in prompt
    assert "Stagione: estate." in prompt


def test_un_tema_lungo_o_su_piu_righe_non_rompe_il_prompt():
    prompt = prompt_immagine(PROFILO, "Una\nriga  " * 100, date(2030, 1, 7))

    soggetto = next(r for r in prompt.splitlines() if r.startswith("Soggetto:"))
    assert len(soggetto) < 400
    assert len(prompt.splitlines()) == 7
