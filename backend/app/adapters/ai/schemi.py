"""Le risposte strutturate che l'AI deve dare (brief-ai, T3-31).

Ogni modello è passato a LiteLLM come ``response_format``. Tutti i campi sono
obbligatori (quelli che possono mancare sono ``... | None`` senza valore di
partenza), perché i provider con schema stretto non ammettono altro. I
controlli di valore stanno nei validatori, non nello schema: un valore
fuori misura è una risposta fuori schema (R-35).
"""

from typing import Any, Literal

from pydantic import BaseModel, field_validator

# plan §2 (foto.analisi_ai.tipo): la copia sta qui perché un adattatore non
# importa i moduli; un test la confronta con quella di campagne.
TipoFoto = Literal[
    "pezzo_finito", "dettaglio", "lavorazione", "persona", "ambientato", "evento"
]
PAROLE_SOGGETTO = 15
# La descrizione è per chi scrive i testi: due o tre frasi, non un tema.
PAROLE_DESCRIZIONE = 60


def riquadro_valido(valore: Any) -> dict[str, float] | None:
    """Il riquadro del soggetto se è ben formato e dentro la foto, altrimenti ``None``.

    Quattro numeri tra 0 e 1 (``x``, ``y``, ``larghezza``, ``altezza``), con
    l'origine in alto a sinistra e il rettangolo tutto dentro la foto. Un
    riquadro fuori misura non è un errore: l'analisi resta, senza riquadro.
    """
    if not isinstance(valore, dict):
        return None
    try:
        x, y, larghezza, altezza = (
            float(valore[chiave]) for chiave in ("x", "y", "larghezza", "altezza")
        )
    except (KeyError, TypeError, ValueError):
        return None
    if isinstance(valore["x"], bool):
        return None
    margine = 1e-6
    if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < larghezza <= 1 and 0 < altezza <= 1):
        return None
    if x + larghezza > 1 + margine or y + altezza > 1 + margine:
        return None
    return {"x": x, "y": y, "larghezza": larghezza, "altezza": altezza}


class SoggettoBox(BaseModel):
    x: float
    y: float
    larghezza: float
    altezza: float


class AnalisiFoto(BaseModel):
    foto_id: int
    soggetto: str
    descrizione: str
    tipo: TipoFoto
    idonea: bool
    motivo: str | None
    punteggio: int
    simile_a: int | None
    soggetto_box: SoggettoBox | None
    persone_riconoscibili: bool
    marchi_visibili: bool

    @field_validator("soggetto_box", mode="before")
    @classmethod
    def _riquadro_sensato(cls, valore: Any) -> dict[str, float] | None:
        return riquadro_valido(valore)

    @field_validator("punteggio")
    @classmethod
    def _da_uno_a_cinque(cls, valore: int) -> int:
        if not 1 <= valore <= 5:
            raise ValueError("Il punteggio va da 1 a 5.")
        return valore

    @field_validator("soggetto")
    @classmethod
    def _breve(cls, valore: str) -> str:
        return " ".join(valore.split()[:PAROLE_SOGGETTO])

    @field_validator("descrizione")
    @classmethod
    def _non_troppo_lunga(cls, valore: str) -> str:
        return " ".join(valore.split()[:PAROLE_DESCRIZIONE])


class RispostaAnalisi(BaseModel):
    foto: list[AnalisiFoto]


class PostDelPiano(BaseModel):
    """Un post del piano; il controllo di ``contenuti`` ne verifica i valori."""

    canale: str
    formato: str
    foto: list[int]
    riempitivo: str | None
    data_ora: str


class UscitaDelPiano(BaseModel):
    numero: int
    tema: str
    gruppo_id: int | None
    post: list[PostDelPiano]


class RispostaPiano(BaseModel):
    strategia: str
    uscite: list[UscitaDelPiano]


class RispostaPost(BaseModel):
    testo: str
    hashtag: list[str]
