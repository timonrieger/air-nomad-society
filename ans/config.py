from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, read from the environment and `.env`.

    Every field has a default so importing (and instantiating) never crashes:
    the web app doesn't need SMTP, the digest job doesn't need SECRET_KEY.
    Missing values fail at the point of use instead.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str | None = None
    db_uri: str | None = None

    tequila_endpoint: str = "https://api.tequila.kiwi.com"
    tequila_api_key: str | None = None

    smtp_email: str | None = None
    smtp_pwd: str | None = None
    smtp_server: str | None = None
    smtp_port: int = 587

    # "dev" restricts the digest job to the subscriber with id MY_UUID.
    environment: str = "production"
    my_uuid: int | None = None

    public_base_url: str = "https://ans.timonrieger.de"


@lru_cache
def get_settings() -> Settings:
    return Settings()
