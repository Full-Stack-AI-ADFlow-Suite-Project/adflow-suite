from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/adflow"
    TEST_DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/adflow_test"
    SECRET_KEY: str = "chiave_segreta_sviluppo"
    ALGORITHM: str = "HS256"

    # Archivio foto
    ARCHIVIO_FOTO_DIR: str = "./archivio_foto"

    # AI
    AI_PROVIDER: str = "finto"
    AI_MODELLO_VISIONE: str = "gpt-4-vision-preview"
    AI_MODELLO_TESTO: str = "gpt-4"
    OPENAI_API_KEY: str = ""

    # Configurazione campagne
    ANTICIPO_MINIMO_GIORNI: int = 3
    MARGINE_SLOT_MINUTI: int = 15

    # Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025

    # Questa riga dice a Pydantic di ignorare le altre variabili nel .env
    model_config = ConfigDict(extra="ignore", env_file=".env")

settings = Settings()
