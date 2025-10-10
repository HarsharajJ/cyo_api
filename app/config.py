from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    database_url: str = "sqlite:///./app.db"
    debug: bool = False
    # Optional GCS/emulator settings
    gcs_bucket_name: Optional[str] = None
    storage_emulator_host: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()