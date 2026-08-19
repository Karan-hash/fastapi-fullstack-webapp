from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Maximum allowed profile picture upload size (5 MB)
    max_upload_size_bytes: int = 5 * 1024 * 1024

    posts_per_page: int = 15


settings = Settings()  # type: ignore[call-arg] # Loaded from .env file