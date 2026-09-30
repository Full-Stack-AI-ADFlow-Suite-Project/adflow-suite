from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    database_url_test: str = Field(..., alias="DATABASE_URL_TEST")

    # Archivio foto
    archivio_foto_dir: str = Field(..., alias="ARCHIVIO_FOTO_DIR")

    # AI
    ai_provider: str = Field(default="finto", alias="AI_PROVIDER")
    ai_modello_visione: str = Field(default="gpt-4o", alias="AI_MODELLO_VISIONE")
    ai_modello_testo: str = Field(default="gpt-4o", alias="AI_MODELLO_TESTO")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")

    # Configurazione campagne
    anticipo_minimo_giorni: int = Field(default=3, alias="ANTICIPO_MINIMO_GIORNI")
    margine_slot_minuti: int = Field(default=15, alias="MARGINE_SLOT_MINUTI")

    # Email
    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, alias="SMTP_PORT")


settings = Settings()
