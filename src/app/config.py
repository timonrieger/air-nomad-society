from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, read from the environment and `.env`.

    Optional features have defaults so importing never crashes: the web app
    doesn't need SMTP, the digest job doesn't need SECRET_KEY — those fail
    at the point of use. PUBLIC_BASE_URL is required everywhere (CORS and
    email links), so a misconfigured deployment fails at startup.
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

    # The frontend origin: the API's CORS allow-list and the base for all
    # links in emails. No default — every environment must set it.
    public_base_url: str


@lru_cache
def get_settings() -> Settings:
    # pydantic-settings fills required fields from the environment.
    return Settings()  # ty: ignore[missing-argument]
