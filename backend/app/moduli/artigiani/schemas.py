"""Stato pubblico dei canali, senza permessi o identificativi social."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .profilo_schemas import ProfiloPubblico


class CanaleCollegato(BaseModel):
    canale: str
    collegato: bool


class NuovoArtigiano(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=1, max_length=320)
    nome: str = Field(min_length=1)

    @field_validator("email", "nome")
    @classmethod
    def testo_rappresentabile(cls, valore: str) -> str:
        valore = valore.strip()
        if not valore or "\x00" in valore:
            raise ValueError("Compilare email e nome con dati validi.")
        try:
            valore.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Caratteri non validi.") from None
        return valore


class ArtigianoCreato(BaseModel):
    id: int
    email: str
    nome: str
    password_provvisoria: str = Field(repr=False)


class SchedaArtigiano(BaseModel):
    """``GET /artigiani/{id}``: account e profilo in sola lettura (spec R-38)."""

    id: int
    nome: str
    email: str
    attivo: bool
    # Lo schema di GET /profilo; None se l'artigiano non l'ha ancora compilato.
    profilo: ProfiloPubblico | None
    canali_collegati: list[str]
