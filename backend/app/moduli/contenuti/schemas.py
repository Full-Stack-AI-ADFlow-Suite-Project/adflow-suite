"""Risposta pubblica del calendario: contenuti approvati, senza note interne."""
from datetime import date, datetime

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


class CanaleToltoCalendario(BaseModel):
    canale: str
    nota: str | None


class CalendarioCampagna(BaseModel):
    campagna_id: int
    strategia: str | None
    giorni: list[GiornoCalendario]
    canali_tolti: list[CanaleToltoCalendario]
    n_post_scaduti: int
