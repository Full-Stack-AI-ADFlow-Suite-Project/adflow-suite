"""Dati del login e vista pubblica dell'utente, senza password né token."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


def testo_valido(testo: str, *, campo_postgres: bool = False) -> bool:
    """UTF-8 valido; nei campi text PostgreSQL non sono ammessi byte NUL."""
    if campo_postgres and "\x00" in testo:
        return False
    try:
        testo.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


class Login(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)

    @field_validator("email")
    @classmethod
    def email_rappresentabile(cls, valore: str) -> str:
        if not testo_valido(valore, campo_postgres=True):
            raise ValueError("Indirizzo email non valido.")
        return valore

    @field_validator("password")
    @classmethod
    def password_rappresentabile(cls, valore: str) -> str:
        if not testo_valido(valore):
            raise ValueError("Password non valida.")
        return valore


class UtentePubblico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nome: str
    ruolo: str
