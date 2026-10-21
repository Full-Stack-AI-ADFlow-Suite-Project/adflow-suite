"""Risposta pubblica del calendario: contenuti approvati, senza note interne."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class FotoCalendario(BaseModel):
    id: int
    url: str
    mime: str
    larghezza: int
    altezza: int
    origine: str


class PostCalendario(BaseModel):
    id: int
    data_ora: datetime
    ora: str
    canale: str
    stato: str
    testo: str
    hashtag: list[str]
    foto: list[FotoCalendario]


class GiornoCalendario(BaseModel):
    data: date
    post: list[PostCalendario]


class PostSettimana(PostCalendario):
    """Un post del calendario settimanale (spec R-48)."""

    campagna_id: int
    campagna_titolo: str
    bottega: str | None


class GiornoSettimana(BaseModel):
    data: date
    post: list[PostSettimana]


class CalendarioSettimana(BaseModel):
    dal: date  # lunedì
    al: date  # domenica
    giorni: list[GiornoSettimana]  # sempre 7, anche vuoti


class CanaleToltoCalendario(BaseModel):
    canale: str
    nota: str | None


class CalendarioCampagna(BaseModel):
    campagna_id: int
    strategia: str | None
    giorni: list[GiornoCalendario]
    canali_tolti: list[CanaleToltoCalendario]
    n_post_scaduti: int


class ChiamateAIDiUnTipo(BaseModel):
    """Le chiamate all'AI di un tipo (analisi, piano, testo, immagine) e ciò che sono costate."""

    tipo: str
    chiamate: int
    modelli: list[str]
    token_ingresso: int
    token_uscita: int
    immagini: int
    costo_usd: Decimal


class PostSegnalato(BaseModel):
    """Un post la cui versione corrente ha blocchi o avvisi del validatore."""

    post_id: int
    canale: str
    data_ora: datetime
    con_blocco: bool
    segnalazioni: list[str]


class RiepilogoAI(BaseModel):
    """Che cosa ha fatto e speso l'AI per una campagna (spec R-44, prova di T3-32)."""

    campagna_id: int
    per_tipo: list[ChiamateAIDiUnTipo]
    costo_totale_usd: Decimal
    n_post: int
    riscritture_piano: int
    riscritture_testi: int
    post_segnalati: list[PostSegnalato]
