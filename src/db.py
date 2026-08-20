"""Database access for the digest job and the API."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.config import Settings
from src.models.subscriber import Subscriber


def load_subscribers(settings: Settings) -> list[Subscriber]:
    from database import AirNomads  # noqa: PLC0415  # binds to DB_URI at import

    assert settings.db_uri, "DB_URI is not configured"
    statement = select(AirNomads)
    if settings.environment == "dev":
        statement = statement.where(AirNomads.id == settings.my_uuid)
    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        return [Subscriber.from_row(row) for row in session.scalars(statement)]
