"""Schemi delle risposte di ``GET /campagne/{id}/post`` (plan §3, spec §2.3)."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CampagnaSchema(BaseModel):
    """La campagna come la legge l'operatore in Vedi campagna."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    profilo_id: int
    titolo: str
    inizio: date
    fine: date
    descrizione: str | None
    stato: str
    canali: list[str] | None
    canali_tolti: list[str] | None
    frequenza: str | None
    obiettivo: str | None
    inviata_il: datetime | None
    chiusa_il: datetime | None


class PianoSchema(BaseModel):
    """Il piano corrente: strategia, esito del controllo e debolezza (R-20)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    strategia: str
    esito_controllo: dict[str, Any] | list[Any] | None
    debole: bool
    creata_il: datetime


class FotoLegataSchema(BaseModel):
    """Una foto legata a una versione, nella sua posizione."""

    foto_id: int
    posizione: int


class VersionePostSchema(BaseModel):
    """Una versione del post con autore, foto e risultati del validatore."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    testo: str
    hashtag: list[str]
    autore_id: int | None
    tipo_intervento: str
    testo_proposto: str | None
    nota: str | None
    provider_ai: str | None
    modello_ai: str | None
    versione_prompt: str | None
    errori_validazione: dict[str, Any] | list[Any] | None
    creata_il: datetime
    foto: list[FotoLegataSchema]


class PostSchema(BaseModel):
    """Un post con tipo di riempitivo, versione corrente e storico."""

    post_id: int
    canale: str
    formato: str
    riempitivo: str | None
    data_ora: datetime
    stato: str
    da_rivedere: bool
    controllato_da: int | None
    controllato_il: datetime | None
    intervento_in_corso: str | None
    intervento_dal: datetime | None
    versione_corrente: VersionePostSchema | None
    versioni: list[VersionePostSchema]


class GruppoSchema(BaseModel):
    """Il gruppo di un'uscita o delle foto non usate."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    origine: str
    descrizione: str | None
    da_usare_il: date | None


class UscitaSchema(BaseModel):
    """Un'uscita con il suo gruppo e i post dei canali."""

    id: int
    numero: int
    tema: str
    gruppo: GruppoSchema | None
    post: list[PostSchema]


class FotoNonUsataSchema(BaseModel):
    """Una foto che il piano non usa, con il motivo dell'analisi."""

    foto_id: int
    motivo: str | None


class GruppoFotoNonUsateSchema(BaseModel):
    """Le foto non usate di un gruppo; ``gruppo_id`` nullo per le cartoline."""

    gruppo_id: int | None
    descrizione: str | None
    foto: list[FotoNonUsataSchema]


class ErroreSchema(BaseModel):
    """L'ultimo errore della generazione (R-35)."""

    model_config = ConfigDict(from_attributes=True)

    tipo: str
    messaggio: str
    tappa: str
    canale: str | None
    creata_il: datetime


class VediCampagnaSchema(BaseModel):
    """Risposta completa di Vedi campagna in ogni stato dopo l'invio."""

    campagna: CampagnaSchema
    piano: PianoSchema | None
    uscite: list[UscitaSchema]
    foto_non_usate: list[GruppoFotoNonUsateSchema]
    ultimo_errore: ErroreSchema | None
