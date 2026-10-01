from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/adflow"
    TEST_DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/adflow_test"
    SECRET_KEY: str = "chiave_segreta_sviluppo"
    ALGORITHM: str = "HS256"

    # Questa riga dice a Pydantic di ignorare le altre variabili nel .env
    model_config = ConfigDict(extra="ignore", env_file=".env")

settings = Settings()
