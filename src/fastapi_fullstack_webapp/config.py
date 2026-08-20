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

    # Password reset token expiration time in minutes
    reset_token_expire_minutes: int = 60

    # SMTP mail server hostname
    mail_server: str = "localhost"

    # SMTP mail server port
    mail_port: int = 587

    # Username used to authenticate with the mail server
    mail_username: str = ""

    # Password used to authenticate with the mail server
    mail_password: SecretStr = SecretStr("")

    # Email address used as the sender for outgoing emails
    mail_from: str = "noreply@example.com"

    # Enable TLS encryption for secure SMTP communication
    mail_use_tls: bool = True

    # Frontend base URL used to generate password reset links
    frontend_url: str = "http://localhost:8000"


settings = Settings()  # type: ignore[call-arg] # Loaded from .env file