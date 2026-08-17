"""Legacy shim: exposes the old constant names, sourced from `ans.config`
and `ans.refdata`. Dies with the `src/` tree at the end of Phase 0."""

from ans import refdata
from ans.config import get_settings

_settings = get_settings()

SECRET_KEY = _settings.secret_key
DB_URI = _settings.db_uri

TEQUILA_ENDPOINT = _settings.tequila_endpoint
TEQUILA_API_KEY = _settings.tequila_api_key
SMTP_EMAIL = _settings.smtp_email
SMTP_PWD = _settings.smtp_pwd
SMTP_SERVER = _settings.smtp_server
SMTP_PORT = _settings.smtp_port

JSON_DATA = refdata.load().model_dump()
DEPARTURE_CHOICES = refdata.departure_choices()
CURRENCY_CHOICES = refdata.currency_choices()
COUNTRY_CHOICES = refdata.country_choices()
ENVIRONMENT = _settings.environment
MY_UUID = _settings.my_uuid
