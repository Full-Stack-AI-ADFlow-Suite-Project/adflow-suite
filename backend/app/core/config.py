"""Configurazione letta da backend/.env (variabili di plan §1)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Impostazioni(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )

    database_url: str
    database_url_test: str
    archivio_foto_dir: str = "./archivio_foto"

    ai_provider: Literal["finto", "litellm"] = "finto"
    ai_modello_visione: str = ""
    ai_modello_testo: str = ""
    openai_api_key: str = ""

    anticipo_minimo_giorni: int = 3
    margine_slot_minuti: int = 15

    sessione_artigiano_giorni: int = Field(default=7, ge=1)
    sessione_operatore_ore: int = Field(default=12, ge=1)
    consorzio_nome: str = ""
    consorzio_telefono: str = ""
    consorzio_email: str = ""

    smtp_host: str = "localhost"
    smtp_port: int = 1025


@lru_cache
def leggi_impostazioni() -> Impostazioni:
    return Impostazioni()
