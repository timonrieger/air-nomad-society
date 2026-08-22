from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, read from the environment and `.env`.

    Every field without a default is required in every environment, so a
    misconfigured deployment fails at startup rather than at the point of use.
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    secret_key: str
    db_uri: str

    tequila_endpoint: str = "https://api.tequila.kiwi.com"
    tequila_api_key: str

    smtp_email: str
    smtp_pwd: str
    smtp_server: str
    smtp_port: int = 587

    # Optional: per-deal AI reasoning lines in the digest
    ai_api_key: str | None = None
    ai_base_url: str = "https://openrouter.ai/api/v1"
    ai_model: str = "anthropic/claude-haiku-4.5"

    # "dev" restricts the digest job to the subscriber with id MY_UUID.
    environment: str = "production"
    my_uuid: int | None = None

    public_base_url: str

    @property
    def digest_only_id(self) -> int | None:
        """The single subscriber the digest is restricted to, in dev only."""
        return self.my_uuid if self.environment == "dev" else None


@lru_cache
def get_settings() -> Settings:
    return Settings()  # ty: ignore[missing-argument]
