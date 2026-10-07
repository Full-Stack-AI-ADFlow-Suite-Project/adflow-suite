"""Schemi Pydantic per il modulo campagne (richieste e risposte API)."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def testo_valido(testo: str, *, campo_postgres: bool = True) -> bool:
    """Verifica che il testo sia UTF-8 valido e senza byte NUL per PostgreSQL."""
    if campo_postgres and "\x00" in testo:
        return False
    try:
        testo.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


class CampagnaCrea(BaseModel):
    """Payload per la creazione di una nuova bozza di campagna (POST /campagne)."""

    titolo: str = Field(min_length=1, max_length=200)
    inizio: date
    fine: date
    descrizione: str | None = Field(default=None, max_length=2000)
    crea_immagini_ai: bool = Field(default=False)

    @field_validator("titolo")
    @classmethod
    def valida_titolo(cls, valore: str) -> str:
        pulito = valore.strip()
        if not pulito:
            raise ValueError("Il titolo non può essere vuoto.")
        if not testo_valido(pulito):
            raise ValueError("Il titolo contiene caratteri non validi.")
        return pulito

    @field_validator("descrizione")
    @classmethod
    def valida_descrizione(cls, valore: str | None) -> str | None:
        if valore is None:
            return None
        pulito = valore.strip()
        if not pulito:
            return None
        if not testo_valido(pulito):
            raise ValueError("La descrizione contiene caratteri non validi.")
        return pulito


class FotoSintetica(BaseModel):
    """Rappresentazione essenziale di una foto nel dettaglio della campagna."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    gruppo_id: UUID
    file: str
    mime: str
    larghezza: int
    altezza: int
    descrizione: str | None = None


class DecisioneSintetica(BaseModel):
    """Decisione dell'operatore sulla campagna (consultabile da operatore/admin)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    esito: str
    motivo: str | None = None
    nota: str | None = None


class CampagnaDettaglio(BaseModel):
    """Dettaglio completo di una campagna (GET /campagne/{id})."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    profilo_id: int
    titolo: str
    inizio: date
    fine: date
    descrizione: str | None = None
    crea_immagini_ai: bool = False
    stato: str
    canali: list[str] | None = None
    frequenza: str | None = None
    obiettivo: str | None = None
    inviata_il: datetime | None = None
    rimandata: bool = False
    foto: list[FotoSintetica] = []
    profilo_snapshot: dict[str, Any] | None = None
    decisioni: list[DecisioneSintetica] = []


class CampagnaElencoItem(BaseModel):
    """Elemento sintetico per la lista delle campagne (GET /campagne)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    profilo_id: int
    titolo: str
    inizio: date
    fine: date
    stato: str
    crea_immagini_ai: bool = False


class FotoDettaglio(BaseModel):
    """Rappresentazione completa di una foto appena caricata o consultata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    profilo_id: int
    campagna_id: int
    gruppo_id: UUID
    origine: str
    file: str
    mime: str
    larghezza: int
    altezza: int
    descrizione: str | None = None
    n_utilizzi: int = 0


class GruppoDescrizioneAggiorna(BaseModel):
    """Payload per l'aggiornamento della descrizione di un gruppo di foto (PUT /campagne/{id}/gruppi/{gruppo_id})."""

    descrizione: str = Field(min_length=1, max_length=2000)

    @field_validator("descrizione")
    @classmethod
    def valida_descrizione(cls, valore: str) -> str:
        pulito = valore.strip()
        if not pulito:
            raise ValueError("La descrizione del gruppo non può essere vuota.")
        if not testo_valido(pulito):
            raise ValueError("La descrizione del gruppo contiene caratteri non validi.")
        return pulito
