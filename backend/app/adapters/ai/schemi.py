"""Le risposte strutturate che l'AI deve dare (brief-ai, T3-31).

Ogni modello è passato a LiteLLM come ``response_format``. Tutti i campi sono
obbligatori (quelli che possono mancare sono ``... | None`` senza valore di
partenza), perché i provider con schema stretto non ammettono altro. I
controlli di valore stanno nei validatori, non nello schema: un valore
fuori misura è una risposta fuori schema (R-35).
"""

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

# Le sei inquadrature della scena di un'immagine AI (R-43, ADR-119).
INQUADRATURE = (
    "dettaglio_materia",
    "banco_dall_alto",
    "attrezzi_still_life",
    "bottega_campo_largo",
    "materie_prime",
    "atmosfera_stagione",
)

# plan §2 (foto.analisi_ai.tipo): la copia sta qui perché un adattatore non
# importa i moduli; un test la confronta con quella di campagne.
TipoFoto = Literal[
    "pezzo_finito", "dettaglio", "lavorazione", "persona", "ambientato", "evento"
]
# Le note e i ruoli delle zone del ritocco (ADR-124, nota 12.2): copie del catalogo di
# `campagne/ritocco_catalogo.py`, che un test confronta. L'ordine è quello del prompt.
Nota = Literal[
    # inquadratura
    "lontana", "decentrata", "storta", "ambiente", "non_tagliare",
    "ruota_90", "ruota_180", "ruota_270",
    # luce
    "scura", "chiara", "controluce", "flash",
    "calda", "fredda", "verde", "magenta",
    "riflessi_bordi", "riflessi_soggetto",
    # qualità e tipo
    "mossa_lieve", "mossa_forte", "foto_di_foto", "screenshot", "grafica",
    # altro
    "marchi",
]  # fmt: skip
RuoloZona = Literal[
    "tieni", "togli", "neutro", "volto", "nome", "indirizzo", "targa", "dati"
]
RUOLI_VOLTO = (
    "staff",
    "minore",
    "no",
)  # i soli ruoli che l'AI scrive: gli altri sono "cliente"
NOTE_IN_CONFLITTO = (
    frozenset({"scura", "chiara"}),
    frozenset({"mossa_lieve", "mossa_forte"}),
    frozenset({"calda", "fredda"}),
    frozenset({"verde", "magenta"}),
    frozenset({"ruota_90", "ruota_180", "ruota_270"}),
)
MAX_ZONE = 8
MAX_VOLTI = 12
MAX_NOTE = 8

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


def _intero(valore: Any) -> int | None:
    """Un intero vero (anche un float intero come 12.0), mai un booleano."""
    if isinstance(valore, bool):
        return None
    if isinstance(valore, int):
        return valore
    if isinstance(valore, float) and valore.is_integer():
        return int(valore)
    return None


def box_centesimi_valido(valore: Any) -> list[int] | None:
    """``[x, y, larghezza, altezza]`` in centesimi della foto, se sono interi e il riquadro sta tutto dentro.

    Altrimenti ``None``: un riquadro fuori misura non è un errore (CA-108).
    """
    if not isinstance(valore, (list, tuple)) or len(valore) != 4:
        return None
    x, y, larghezza, altezza = (_intero(v) for v in valore)
    if None in (x, y, larghezza, altezza):
        return None
    if not (
        0 <= x <= 100
        and 0 <= y <= 100
        and 1 <= larghezza <= 100
        and 1 <= altezza <= 100
    ):
        return None
    if x + larghezza > 100 or y + altezza > 100:
        return None
    return [x, y, larghezza, altezza]


def punto_centesimi_valido(valore: Any) -> list[int] | None:
    """``[x, y]`` in centesimi della foto, due interi in 0–100."""
    if not isinstance(valore, (list, tuple)) or len(valore) != 2:
        return None
    x, y = _intero(valore[0]), _intero(valore[1])
    if x is None or y is None or not (0 <= x <= 100 and 0 <= y <= 100):
        return None
    return [x, y]


def riquadro_da_centesimi(valore: Any) -> dict[str, float] | None:
    """Il riquadro nel dizionario 0–1 di oggi (``x``, ``y``, ``larghezza``, ``altezza``)."""
    box = box_centesimi_valido(valore)
    if box is None:
        return None
    return {
        "x": box[0] / 100,
        "y": box[1] / 100,
        "larghezza": box[2] / 100,
        "altezza": box[3] / 100,
    }


class Zona(BaseModel):
    """Un riquadro che l'AI segna nella foto, con il suo ruolo."""

    ruolo: RuoloZona
    b: list[int]  # [x, y, larghezza, altezza] in centesimi

    @field_validator("b", mode="before")
    @classmethod
    def _dentro_la_foto(cls, valore: Any) -> list[int]:
        box = box_centesimi_valido(valore)
        if box is None:
            raise ValueError("Riquadro non valido.")
        return box


class Ritocco(BaseModel):
    """Quello che l'AI dice sul ritocco di una foto, a codici e solo per eccezione (nota 12.2).

    Tutti i controlli sono morbidi: un elemento che non passa si scarta, non fa fallire
    la risposta.
    """

    note: list[Nota]
    centro: list[int] | None  # [x, y] in centesimi: il punto da non tagliare
    zone: list[Zona]
    piana: str | None  # codice Q di una superficie da raddrizzare
    volti: list[str]  # solo eccezioni: "V2 staff", "V3 minore", "V4 no"

    @field_validator("note", mode="before")
    @classmethod
    def _note_note_e_senza_conflitti(cls, valore: Any) -> list[str]:
        if not isinstance(valore, (list, tuple)):
            return []
        conosciute = set(Nota.__args__)
        note = list(
            dict.fromkeys(n for n in valore if isinstance(n, str) and n in conosciute)
        )
        for gruppo in NOTE_IN_CONFLITTO:
            if len(gruppo.intersection(note)) >= 2:
                note = [n for n in note if n not in gruppo]
        return note[:MAX_NOTE]

    @field_validator("centro", mode="before")
    @classmethod
    def _punto_valido(cls, valore: Any) -> list[int] | None:
        return punto_centesimi_valido(valore)

    @field_validator("zone", mode="before")
    @classmethod
    def _zone_valide(cls, valore: Any) -> list[Zona]:
        if not isinstance(valore, (list, tuple)):
            return []
        valide = []
        for voce in valore:
            try:
                valide.append(Zona.model_validate(voce))
            except ValidationError:
                continue
        return valide[:MAX_ZONE]

    @field_validator("piana", mode="before")
    @classmethod
    def _codice_q(cls, valore: Any) -> str | None:
        if isinstance(valore, str) and re.fullmatch(r"Q[1-9]\d?", valore.strip()):
            return valore.strip()
        return None

    @field_validator("volti", mode="before")
    @classmethod
    def _volti_nel_formato(cls, valore: Any) -> list[str]:
        if not isinstance(valore, (list, tuple)):
            return []
        voci = []
        for voce in valore:
            if not isinstance(voce, str):
                continue
            testo = " ".join(voce.split())
            if re.fullmatch(r"V[1-9]\d? (?:" + "|".join(RUOLI_VOLTO) + ")", testo):
                voci.append(testo)
        return voci[:MAX_VOLTI]


class AnalisiFoto(BaseModel):
    foto_id: int
    soggetto: str
    descrizione: str
    tipo: TipoFoto
    idonea: bool
    motivo: str | None
    punteggio: int
    simile_a: int | None
    soggetto_box: list[int] | None  # [x, y, larghezza, altezza] in centesimi
    ritocco: Ritocco | None  # None: niente da segnalare

    @field_validator("soggetto_box", mode="before")
    @classmethod
    def _riquadro_sensato(cls, valore: Any) -> list[int] | None:
        return box_centesimi_valido(valore)

    @field_validator("ritocco", mode="before")
    @classmethod
    def _ritocco_morbido(cls, valore: Any) -> Ritocco | None:
        """Un ritocco malformato vale ``None``: l'analisi resta, senza ritocco."""
        if valore is None or isinstance(valore, Ritocco):
            return valore
        try:
            return Ritocco.model_validate(valore)
        except ValidationError:
            return None

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


class Scena(BaseModel):
    """Che cosa mostra l'immagine AI di un'uscita (R-43, T3-910)."""

    soggetto: str = Field(max_length=200)
    inquadratura: Literal[INQUADRATURE]
    luce: str = Field(max_length=100)
    colori: str = Field(max_length=100)


class UscitaDelPiano(BaseModel):
    numero: int
    tema: str
    gruppo_id: int | None
    scena: Scena | None
    post: list[PostDelPiano]


class RispostaPiano(BaseModel):
    strategia: str
    uscite: list[UscitaDelPiano]


class RispostaPost(BaseModel):
    testo: str
    hashtag: list[str]
