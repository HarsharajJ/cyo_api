from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    database_url: str = "sqlite:///./app.db"
    debug: bool = False
    # GCP settings
    gcp_service_account_file: Optional[str] = None
    gcp_bucket_name: Optional[str] = None
    # Brevo email settings
    brevo_api_key: Optional[str] = None
    brevo_sender_email: Optional[str] = None
    brevo_sender_name: str = "OTP Service"
    otp_expire_minutes: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = False
        # extra = "ignore"  # Ignore extra fields in .env file

settings = Settings()