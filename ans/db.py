"""Loads subscribers without booting the web app.

The digest job previously imported src.app (Bootstrap, CSRF, cache,
create_all on every start) just to get a database session. The AirNomads
model from database-service is a plain declarative model, so a vanilla
SQLAlchemy session against our own engine is enough.
"""

from typing import Any

from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from ans.config import Settings


class Subscriber(BaseModel):
    id: int
    username: str
    email: str
    token: str
    departure_city: str
    departure_iata: str
    currency: str
    min_nights: int
    max_nights: int
    min_days_ahead: int
    max_days_ahead: int
    favorites: list[str]
    excluded: list[str]

    @classmethod
    def from_row(cls, row: Any) -> "Subscriber":
        return cls(
            id=row.id,
            username=row.username,
            email=row.email,
            token=row.token,
            departure_city=row.departure_city,
            departure_iata=row.departure_iata,
            currency=row.currency.upper(),
            min_nights=row.min_nights,
            max_nights=row.max_nights,
            min_days_ahead=row.min_days_ahead,
            max_days_ahead=row.max_days_ahead,
            favorites=_split(row.travel_countries),
            excluded=_split(row.excluded_countries),
        )


def _split(joined: str | None) -> list[str]:
    return [part.strip() for part in joined.split(",")] if joined else []


def load_subscribers(settings: Settings) -> list[Subscriber]:
    from database import AirNomads  # noqa: PLC0415  # binds to DB_URI at import

    assert settings.db_uri, "DB_URI is not configured"
    statement = select(AirNomads)
    if settings.environment == "dev":
        statement = statement.where(AirNomads.id == settings.my_uuid)
    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        return [Subscriber.from_row(row) for row in session.scalars(statement)]
