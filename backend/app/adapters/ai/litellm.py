"""Provider AI vero, via LiteLLM (plan §5, brief-ai T3-31).

Ogni metodo fa una chiamata con risposta strutturata (un modello Pydantic di
``schemi.py`` passato come ``response_format``) e traduce gli errori del
provider nei cinque tipi di R-35. Dopo ogni chiamata ``ultimo_uso`` dice cosa
è costata (R-44). I messaggi per l'operatore non riportano mai il testo
dell'errore del provider: può contenere pezzi della chiave o dei dati.

Nei test ``litellm.completion`` si sostituisce: nessuna rete.
"""

import base64
import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any, TypeVar

import litellm
import openai
from litellm import exceptions as errori_litellm
from PIL import Image, ImageOps
from pydantic import BaseModel, ValidationError

from app.adapters.archivio import ottieni_archivio
from app.core.config import leggi_impostazioni

from .base import (
    AIAdapter,
    CampagnaAI,
    ErroreAI,
    FotoAI,
    GruppoAI,
    ImmagineAI,
    PianoAI,
    PostAI,
    PostScritto,
    UsoAI,
)
from .immagini import VERSIONE_PROMPT as VERSIONE_PROMPT_IMMAGINE
from .schemi import RispostaAnalisi, RispostaPiano, RispostaPost

PROVIDER = "litellm"
CARTELLA_PROMPT = Path(__file__).parent / "prompts"
# Lato lungo delle foto mandate all'analisi, qualità del JPEG e dettaglio.
# Con `low` il provider riduce la foto a 512 px: troppo poco per descriverla.
LATO_FOTO = 1024
QUALITA_JPEG = 85
DETTAGLIO_FOTO = "high"
# Il job riprova da sé (R-35): LiteLLM non deve moltiplicare i tentativi.
TIMEOUT_SECONDI = 120
# Le immagini AI sono sempre quadrate 1:1, di qualità media (brief-ai T3-34).
DIMENSIONE_IMMAGINE = "1024x1024"
QUALITA_IMMAGINE = "medium"
FORMATI_IMMAGINE = {"PNG": "image/png", "JPEG": "image/jpeg"}
# Del profilo l'AI vede solo ciò che serve a scrivere: non il referente, il
# sito o i profili social.
CAMPI_DEL_PROFILO = (
    "nome",
    "citta",
    "zona",
    "anni_attivita",
    "storia",
    "origine",
    "valori",
    "tipo_prodotto",
    "gamma",
    "fascia_prezzo",
    "stagionalita",
    "clienti_ideali",
    "obiettivo",
    "tono",
    "cortesia",
    "vincoli",
    "eventi_ricorrenti",
    "chiusure",
)

R = TypeVar("R", bound=BaseModel)

# Segnali, nel testo dell'errore, che un 429 o un 400 sono altro da ciò che dicono.
_SENZA_CREDITO = ("insufficient_quota", "billing", "credit", "quota exceeded")
_MODELLO_SBAGLIATO = (
    "llm provider not provided",
    "model not found",
    "does not exist",
    "unknown model",
)
_IMMAGINE = ("image", "immagine")
# Il filtro dei contenuti può arrivare come un 400 qualunque.
_FILTRO = ("content_policy", "moderation_blocked", "safety system")


@lru_cache
def _prompt(nome: str) -> str:
    """Il testo di ``prompts/<nome>.md``; il nome porta la versione (``piano_v2``)."""
    return (CARTELLA_PROMPT / f"{nome}.md").read_text(encoding="utf-8")


def _json(valore: Any) -> str:
    def testo(oggetto: Any) -> str:
        if isinstance(oggetto, (date, datetime)):
            return oggetto.isoformat()
        raise TypeError(type(oggetto).__name__)

    return json.dumps(valore, ensure_ascii=False, default=testo, indent=1)


def traduci_errore(errore: Exception, *, foto_id: int | None = None) -> ErroreAI:
    """L'errore del provider come ``ErroreAI`` di R-35 (tabella di brief-ai).

    ``foto_id`` va dato se la richiesta conteneva una sola foto: allora un
    errore di richiesta riguarda quella foto.
    """
    testo = str(errore).lower()
    # Prima i casi più specifici: molte classi di LiteLLM derivano da BadRequestError.
    if isinstance(errore, errori_litellm.ContentPolicyViolationError):
        return ErroreAI("rifiuto", "Il servizio AI ha rifiutato il contenuto.")
    if isinstance(
        errore,
        (
            errori_litellm.AuthenticationError,
            errori_litellm.PermissionDeniedError,
            errori_litellm.NotFoundError,
            errori_litellm.BudgetExceededError,
            errori_litellm.LiteLLMUnknownProvider,
            errori_litellm.UnsupportedParamsError,
        ),
    ):
        return ErroreAI(
            "configurazione",
            "Il servizio AI non accetta la configurazione: controlla chiave, "
            "credito e nome del modello.",
        )
    if isinstance(errore, errori_litellm.RateLimitError):
        if any(segnale in testo for segnale in _SENZA_CREDITO):
            return ErroreAI("configurazione", "Il credito del servizio AI è finito.")
        return ErroreAI(
            "temporaneo", "Il servizio AI ha ricevuto troppe richieste: riprova."
        )
    if isinstance(errore, errori_litellm.JSONSchemaValidationError):
        return ErroreAI("risposta", "La risposta dell'AI non è nel formato chiesto.")
    if isinstance(
        errore,
        (errori_litellm.ContextWindowExceededError, errori_litellm.ImageFetchError),
    ):
        return ErroreAI(
            "richiesta",
            "La richiesta all'AI è troppo grande o contiene un'immagine non leggibile.",
            foto_id=foto_id,
        )
    if isinstance(errore, errori_litellm.BadRequestError):
        if any(segnale in testo for segnale in _FILTRO):
            return ErroreAI("rifiuto", "Il servizio AI ha rifiutato il contenuto.")
        if any(segnale in testo for segnale in _MODELLO_SBAGLIATO):
            return ErroreAI("configurazione", "Il modello AI scelto non esiste.")
        return ErroreAI(
            "richiesta",
            "Il servizio AI non ha accettato la richiesta.",
            foto_id=foto_id if any(s in testo for s in _IMMAGINE) else None,
        )
    # Timeout, connessione, 5xx...: le classi di LiteLLM derivano da quelle di openai.
    if isinstance(errore, openai.APIError):
        stato = getattr(errore, "status_code", None)
        if stato == 413:
            return ErroreAI(
                "richiesta", "La richiesta all'AI è troppo grande.", foto_id=foto_id
            )
        return ErroreAI(
            "temporaneo",
            "Il servizio AI non ha risposto in tempo o non è disponibile: riprova.",
        )
    raise errore


def _foto_per_ai(foto: FotoAI) -> dict[str, Any]:
    """La foto come ``image_url``: JPEG di al massimo 1024 px, in base64, dettaglio alto."""
    try:
        originale = ottieni_archivio().leggi(foto.file)
    except FileNotFoundError:
        raise ErroreAI(
            "richiesta", f"La foto {foto.id} non si trova più.", foto_id=foto.id
        ) from None
    try:
        with Image.open(BytesIO(originale)) as aperta:
            immagine = ImageOps.exif_transpose(aperta).convert("RGB")
        immagine.thumbnail((LATO_FOTO, LATO_FOTO))
        uscita = BytesIO()
        immagine.save(uscita, "JPEG", quality=QUALITA_JPEG)
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        raise ErroreAI(
            "richiesta", f"La foto {foto.id} non si riesce a leggere.", foto_id=foto.id
        ) from None
    dati = base64.b64encode(uscita.getvalue()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{dati}",
            "detail": DETTAGLIO_FOTO,
        },
    }


def _spezza_i_cicli(analisi: dict[int, dict[str, Any]]) -> None:
    """Se due scatti (o più) si dicono doppioni a vicenda, la migliore resta libera.

    Senza, tutte le foto del ciclo uscirebbero dalle disponibili (R-05).
    """
    for inizio in list(analisi):
        visti = [inizio]
        corrente = analisi[inizio]["simile_a"]
        while corrente is not None and corrente not in visti:
            visti.append(corrente)
            corrente = analisi[corrente]["simile_a"]
        if corrente != inizio:
            continue
        migliore = max(visti, key=lambda uno: (analisi[uno]["punteggio"], -uno))
        analisi[migliore]["simile_a"] = None


class AILiteLLM(AIAdapter):
    """Provider AI vero: modelli e chiave da ``backend/.env``."""

    def __init__(self) -> None:
        impostazioni = leggi_impostazioni()
        self._modello_visione = impostazioni.ai_modello_visione
        self._modello_testo = impostazioni.ai_modello_testo
        self._chiave = (
            (impostazioni.openrouter_api_key or impostazioni.openai_api_key)
            if any(
                m.startswith("openrouter/")
                for m in (self._modello_visione, self._modello_testo)
            )
            else (impostazioni.openai_api_key or impostazioni.openrouter_api_key)
        )
        self._prezzo_ingresso = impostazioni.ai_prezzo_ingresso_milione
        self._prezzo_uscita = impostazioni.ai_prezzo_uscita_milione
        self._modello_immagini = impostazioni.ai_modello_immagini
        self._prezzo_immagine = impostazioni.ai_prezzo_immagine
        for nome, valore in (
            ("AI_MODELLO_VISIONE", self._modello_visione),
            ("AI_MODELLO_TESTO", self._modello_testo),
        ):
            if not valore.strip():
                raise ErroreAI("configurazione", f"{nome} non è impostato.")

    # --- chiamata, risposta, costo ----------------------------------------

    def _chiama(
        self,
        tipo: str,
        modello: str,
        messaggi: list[dict[str, Any]],
        schema: type[R],
        *,
        foto_id: int | None = None,
    ) -> R:
        self.ultimo_uso = None
        try:
            risposta = litellm.completion(
                model=modello,
                messages=messaggi,
                response_format=schema,
                api_key=self._chiave or None,
                timeout=TIMEOUT_SECONDI,
                num_retries=0,
            )
        except Exception as errore:  # noqa: BLE001 - tradotto o rilanciato sotto
            raise traduci_errore(errore, foto_id=foto_id) from errore
        self.ultimo_uso = self._uso(tipo, modello, risposta)
        return self._leggi(risposta, schema)

    @staticmethod
    def _leggi(risposta: Any, schema: type[R]) -> R:
        scelte = getattr(risposta, "choices", None) or []
        if not scelte:
            raise ErroreAI("risposta", "L'AI non ha dato nessuna risposta.")
        scelta = scelte[0]
        fine = getattr(scelta, "finish_reason", None)
        messaggio = getattr(scelta, "message", None)
        if fine == "content_filter" or getattr(messaggio, "refusal", None):
            raise ErroreAI("rifiuto", "Il servizio AI ha rifiutato il contenuto.")
        if fine == "length":
            raise ErroreAI("risposta", "La risposta dell'AI è stata troncata.")
        testo = (getattr(messaggio, "content", None) or "").strip()
        if testo.startswith("```"):
            testo = testo.strip("`").removeprefix("json").strip()
        if not testo:
            raise ErroreAI("risposta", "La risposta dell'AI è vuota.")
        try:
            return schema.model_validate_json(testo)
        except ValidationError:
            raise ErroreAI(
                "risposta", "La risposta dell'AI non è nel formato chiesto."
            ) from None

    def _uso(self, tipo: str, modello: str, risposta: Any) -> UsoAI:
        """Token e costo in dollari (R-44): prima LiteLLM, poi i prezzi di configurazione."""
        uso = getattr(risposta, "usage", None)
        ingresso = getattr(uso, "prompt_tokens", None)
        uscita = getattr(uso, "completion_tokens", None)
        try:
            costo = Decimal(str(litellm.completion_cost(completion_response=risposta)))
        except Exception:  # noqa: BLE001 - modello di cui LiteLLM non sa il prezzo
            costo = (
                Decimal(ingresso or 0) * self._prezzo_ingresso
                + Decimal(uscita or 0) * self._prezzo_uscita
            ) / Decimal(1_000_000)
        return UsoAI(
            tipo=tipo,
            provider=PROVIDER,
            modello=modello,
            token_ingresso=ingresso,
            token_uscita=uscita,
            costo_usd=costo,
        )

    def _costo_immagine(self, modello: str, risposta: Any) -> Decimal:
        """Dollari di un'immagine: prima LiteLLM, poi il prezzo di configurazione."""
        try:
            return Decimal(
                str(
                    litellm.completion_cost(completion_response=risposta, model=modello)
                )
            )
        except Exception:  # noqa: BLE001 - modello di cui LiteLLM non sa il prezzo
            return self._prezzo_immagine

    # --- interfaccia -----------------------------------------------------

    def analizza_gruppo(self, gruppo: GruppoAI) -> dict[int, dict[str, Any]]:
        self.ultimo_uso = None
        if not gruppo.foto:
            return {}
        contenuto: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": _json(
                    {
                        "descrizione_del_gruppo": gruppo.descrizione,
                        "da_usare_il": gruppo.da_usare_il,
                    }
                ),
            }
        ]
        for foto in gruppo.foto:
            contenuto.append({"type": "text", "text": f"Foto {foto.id}:"})
            contenuto.append(_foto_per_ai(foto))
        risposta = self._chiama(
            "analisi",
            self._modello_visione,
            [
                {"role": "system", "content": _prompt("analisi_v2")},
                {"role": "user", "content": contenuto},
            ],
            RispostaAnalisi,
            foto_id=gruppo.foto[0].id if len(gruppo.foto) == 1 else None,
        )

        ids = [foto.id for foto in gruppo.foto]
        per_id = {voce.foto_id: voce for voce in risposta.foto}
        if len(risposta.foto) != len(ids) or set(per_id) != set(ids):
            raise ErroreAI(
                "risposta", "L'analisi dell'AI non riguarda tutte le foto del gruppo."
            )
        analisi = {}
        for uno in ids:
            voce = per_id[uno]
            simile = voce.simile_a if voce.simile_a in per_id else None
            analisi[uno] = {
                "idonea": voce.idonea,
                "simile_a": simile if simile != uno else None,
                "tipo": voce.tipo,
                "punteggio": voce.punteggio,
                "motivo": voce.motivo if not voce.idonea else None,
                "soggetto": voce.soggetto,
                "descrizione": voce.descrizione,
                "persone_riconoscibili": voce.persone_riconoscibili,
                "marchi_visibili": voce.marchi_visibili,
            }
            if not voce.idonea and not voce.motivo:
                analisi[uno]["motivo"] = "La foto non è adatta."
        _spezza_i_cicli(analisi)
        return analisi

    def pianifica_campagna(
        self,
        snapshot: Mapping[str, Any],
        campagna: CampagnaAI,
        gruppi: Sequence[GruppoAI],
        limiti: Mapping[str, Mapping[str, Any]],
        schede: Mapping[str, Mapping[str, Any]],
        *,
        non_prima_di: datetime,
        piano_precedente: Mapping[str, Any] | None = None,
        violazioni: Sequence[Mapping[str, Any]] | None = None,
    ) -> PianoAI:
        self.ultimo_uso = None
        # All'AI le sole foto che i limiti ammettono (T3-33 ne passa già poche).
        ammesse = {
            foto for limite in limiti.values() for foto in limite["foto_disponibili"]
        }
        richiesta: dict[str, Any] = {
            "bottega": _del_profilo(snapshot),
            "campagna": {
                "titolo": campagna.titolo,
                "inizio": campagna.inizio,
                "fine": campagna.fine,
                "descrizione": campagna.descrizione,
                "obiettivo": campagna.obiettivo,
            },
            "non_prima_di": non_prima_di,
            "canali": {
                canale: {
                    "post_chiesti": limite["post_chiesti"],
                    "foto_disponibili": list(limite["foto_disponibili"]),
                    "riempitivi": limite["riempitivi"],
                    "scheda": dict(schede.get(canale, {})),
                }
                for canale, limite in limiti.items()
            },
            "gruppi": [
                {
                    "id": gruppo.id,
                    "descrizione": gruppo.descrizione,
                    "da_usare_il": gruppo.da_usare_il,
                    "foto": [
                        {"id": foto.id} | _valutazione(foto)
                        for foto in gruppo.foto
                        if foto.id in ammesse
                    ],
                }
                for gruppo in gruppi
                if any(foto.id in ammesse for foto in gruppo.foto)
            ],
        }
        if piano_precedente is not None:
            richiesta["piano_precedente"] = piano_precedente
            richiesta["violazioni"] = [v["messaggio"] for v in violazioni or []]
        risposta = self._chiama(
            "piano",
            self._modello_testo,
            [
                {"role": "system", "content": _prompt("piano_v2")},
                {"role": "user", "content": _json(richiesta)},
            ],
            RispostaPiano,
        )
        return PianoAI(
            contenuto=risposta.model_dump(),
            provider=PROVIDER,
            modello=self._modello_testo,
            versione_prompt="piano_v2",
        )

    def genera_post(
        self,
        snapshot: Mapping[str, Any],
        campagna: CampagnaAI,
        post: PostAI,
        scheda: Mapping[str, Any],
        *,
        testo_precedente: str | None = None,
        violazioni: Sequence[Mapping[str, Any]] | None = None,
        versioni_rifiutate: Sequence[str] | None = None,
        testo_proposto: str | None = None,
        nota: str | None = None,
        altri_post: Sequence[str] | None = None,
    ) -> PostScritto:
        self.ultimo_uso = None
        richiesta: dict[str, Any] = {
            "bottega": _del_profilo(snapshot),
            "campagna": {
                "titolo": campagna.titolo,
                "descrizione": campagna.descrizione,
                "obiettivo": campagna.obiettivo,
            },
            "post": {
                "canale": post.canale,
                "tema": post.tema,
                "formato": post.formato,
                "data": post.data_ora,
                "descrizione_del_gruppo": post.descrizione_gruppo,
                "foto": [_valutazione(foto) for foto in post.foto],
                "senza_foto": not post.foto,
                "immagine_creata_con_ai": post.riempitivo == "immagine_ai",
            },
            "scheda_del_canale": dict(scheda),
        }
        if post.immagine_ai:
            richiesta["post"]["immagine_ai"] = post.immagine_ai
        if testo_precedente is not None:
            richiesta["testo_precedente"] = testo_precedente
            richiesta["violazioni"] = [v["messaggio"] for v in violazioni or []]
        if versioni_rifiutate:
            richiesta["versioni_rifiutate"] = list(versioni_rifiutate)
        if testo_proposto is not None:
            richiesta["testo_proposto"] = testo_proposto
        if nota:
            richiesta["nota"] = nota
        if altri_post:
            richiesta["altri_post"] = list(altri_post)
        risposta = self._chiama(
            "testo",
            self._modello_testo,
            [
                {"role": "system", "content": _prompt("post_v3")},
                {"role": "user", "content": _json(richiesta)},
            ],
            RispostaPost,
        )
        hashtag = [uno.strip().lstrip("#").strip() for uno in risposta.hashtag]
        return PostScritto(
            testo=risposta.testo.strip(),
            hashtag=[uno for uno in hashtag if uno],
            provider=PROVIDER,
            modello=self._modello_testo,
            versione_prompt="post_v3",
        )

    def genera_immagine(self, prompt: str) -> ImmagineAI:
        self.ultimo_uso = None
        modello = self._modello_immagini.strip()
        if not modello:
            raise ErroreAI("configurazione", "AI_MODELLO_IMMAGINI non è impostato.")
        try:
            risposta = litellm.image_generation(
                prompt=prompt,
                model=modello,
                n=1,
                size=DIMENSIONE_IMMAGINE,
                quality=QUALITA_IMMAGINE,
                api_key=self._chiave or None,
                timeout=TIMEOUT_SECONDI,
            )
        except Exception as errore:  # noqa: BLE001 - tradotto o rilanciato sotto
            raise traduci_errore(errore) from errore
        immagine = _leggi_immagine(risposta, modello)
        uso = getattr(risposta, "usage", None)
        self.ultimo_uso = UsoAI(
            tipo="immagine",
            provider=PROVIDER,
            modello=modello,
            token_ingresso=getattr(uso, "input_tokens", None),
            token_uscita=getattr(uso, "output_tokens", None),
            immagini=1,
            costo_usd=self._costo_immagine(modello, risposta),
        )
        return immagine


def _leggi_immagine(risposta: Any, modello: str) -> ImmagineAI:
    """I byte dell'immagine della risposta, se sono un PNG o un JPEG leggibile."""
    elenco = getattr(risposta, "data", None) or []
    codificata = getattr(elenco[0], "b64_json", None) if elenco else None
    if not codificata:
        raise ErroreAI("risposta", "L'AI non ha restituito nessuna immagine.")
    try:
        contenuto = base64.b64decode(codificata, validate=True)
        with Image.open(BytesIO(contenuto)) as aperta:
            formato = aperta.format or ""
            aperta.load()
    except (ValueError, OSError, SyntaxError, Image.DecompressionBombError):
        raise ErroreAI(
            "risposta", "L'immagine dell'AI non si riesce a leggere."
        ) from None
    mime = FORMATI_IMMAGINE.get(formato)
    if mime is None:
        raise ErroreAI("risposta", "L'immagine dell'AI non è un PNG né un JPEG.")
    return ImmagineAI(
        contenuto=contenuto,
        mime=mime,
        provider=PROVIDER,
        modello=modello,
        versione_prompt=VERSIONE_PROMPT_IMMAGINE,
    )


def _del_profilo(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        campo: snapshot[campo] for campo in CAMPI_DEL_PROFILO if snapshot.get(campo)
    }


def _valutazione(foto: FotoAI) -> dict[str, Any]:
    """Ciò che l'analisi ha detto di una foto, utile a pianificare e a scrivere."""
    analisi = foto.analisi or {}
    return {
        campo: analisi.get(campo)
        for campo in ("soggetto", "descrizione", "tipo", "punteggio", "motivo")
        if analisi.get(campo) is not None
    }
