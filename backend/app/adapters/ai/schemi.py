"""Le risposte strutturate che l'AI deve dare (brief-ai, T3-31).

Ogni modello è passato a LiteLLM come ``response_format``. Tutti i campi sono
obbligatori (quelli che possono mancare sono ``... | None`` senza valore di
partenza), perché i provider con schema stretto non ammettono altro. I
controlli di valore stanno nei validatori, non nello schema: un valore
fuori misura è una risposta fuori schema (R-35).
"""

from typing import Literal

from pydantic import BaseModel, field_validator

# plan §2 (foto.analisi_ai.tipo): la copia sta qui perché un adattatore non
# importa i moduli; un test la confronta con quella di campagne.
TipoFoto = Literal[
    "pezzo_finito", "dettaglio", "lavorazione", "persona", "ambientato", "evento"
]
PAROLE_SOGGETTO = 15
# La descrizione è per chi scrive i testi: due o tre frasi, non un tema.
PAROLE_DESCRIZIONE = 60


class AnalisiFoto(BaseModel):
    foto_id: int
    soggetto: str
    descrizione: str
    tipo: TipoFoto
    idonea: bool
    motivo: str | None
    punteggio: int
    simile_a: int | None
    persone_riconoscibili: bool
    marchi_visibili: bool

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
