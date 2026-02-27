from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "NoPressure Wound Management"
    VERSION: str = "1.0.0"
    SECRET_KEY: str = "change-me-in-production-use-strong-random-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite:///./nopressure.db"

    # HIPAA compliance settings
    ENCRYPTION_KEY: Optional[str] = None
    PHI_ENCRYPTION_ENABLED: bool = True

    # Storage settings
    CLOUD_STORAGE_BUCKET: Optional[str] = None
    SAVE_TO_LOCAL_GALLERY: bool = False  # Zero-footprint: never save to device gallery

    # EHR Integration
    FHIR_BASE_URL: Optional[str] = None
    EHR_API_KEY: Optional[str] = None

    # Wound healing thresholds
    STALLED_WOUND_PAR_THRESHOLD: float = 20.0  # <20% area reduction in 4 weeks = stalled
    STALLED_WOUND_DAYS: int = 28

    # External Wound Classifier API
    CLASSIFIER_API_URL: Optional[str] = None
    CLASSIFIER_API_KEY: Optional[str] = None
    CLASSIFIER_TIMEOUT: int = 10
    CLASSIFIER_MOCK_MODE: bool = True  # Use mock responses when external API is unavailable

    class Config:
        env_file = ".env"


settings = Settings()
