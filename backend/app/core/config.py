"""Configurazione letta da backend/.env (variabili di plan §1)."""

from functools import lru_cache
from typing import Literal
from pydantic import Field, model_validator

from pydantic_settings import BaseSettings, SettingsConfigDict


class Impostazioni(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )

    database_url: str
    database_url_test: str
    ambiente: Literal["sviluppo", "test", "produzione"] = "sviluppo"
    login_limite_tentativi: int = Field(default=5, ge=1, le=1000)
    login_finestra_secondi: int = Field(default=900, ge=1, le=86400)
    login_limite_segreto: str = "solo-sviluppo-cambiare-in-produzione"
    email_test_environment: bool = False
    cookie_secure: bool | None = None

    @model_validator(mode="after")
    def sicurezza_produzione(self) -> "Impostazioni":
        if self.ambiente == "produzione":
            if (
                len(self.login_limite_segreto) < 32
                or self.login_limite_segreto == "solo-sviluppo-cambiare-in-produzione"
            ):
                raise ValueError(
                    "Configurare un segreto per il limite login in produzione."
                )
            if self.email_test_environment or self.cookie_secure is False:
                raise ValueError(
                    "Configurazione di sicurezza non valida in produzione."
                )
        return self

    archivio_foto_dir: str = "./archivio_foto"

    ai_provider: Literal["finto", "litellm"] = "finto"
    ai_modello_visione: str = ""
    ai_modello_testo: str = ""
    openai_api_key: str = ""

    anticipo_minimo_giorni: int = 3
    margine_slot_minuti: int = 15

    smtp_host: str = "localhost"
    smtp_port: int = 1025


@lru_cache
def leggi_impostazioni() -> Impostazioni:
    return Impostazioni()
