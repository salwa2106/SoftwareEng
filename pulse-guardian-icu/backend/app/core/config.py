from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    SECRET_KEY: str = "pulse-guardian-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./pulse_guardian.db"
    DATASET_PATH: str = "./data/mimic_cleaned.csv"

    class Config:
        env_file = ".env"

settings = Settings()
