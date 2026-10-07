"""Dati del login e vista pubblica dell'utente, senza password né token."""

from pydantic import BaseModel, ConfigDict, Field


class Login(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class UtentePubblico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nome: str
    ruolo: str
