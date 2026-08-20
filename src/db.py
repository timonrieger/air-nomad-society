"""Database access: the vendored schema, engine, and session plumbing.

The AirNomads model was vendored 1:1 from the retired database-service
package; this project now owns the `air_nomads` table and its migrations.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.config import Settings, get_settings
from src.models.subscriber import Subscriber


class Base(DeclarativeBase): ...


class AirNomads(Base):
    __tablename__ = "air_nomads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    departure_city: Mapped[str] = mapped_column(String)
    departure_iata: Mapped[str] = mapped_column(String)
    currency: Mapped[str] = mapped_column(String)
    min_nights: Mapped[int] = mapped_column(Integer)
    max_nights: Mapped[int] = mapped_column(Integer)
    travel_countries: Mapped[str] = mapped_column(String)
    excluded_countries: Mapped[str | None] = mapped_column(String, nullable=True)
    min_days_ahead: Mapped[int] = mapped_column(Integer, server_default="1")
    max_days_ahead: Mapped[int] = mapped_column(Integer, server_default="182")


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    assert settings.db_uri, "DB_URI is not configured"
    return create_engine(settings.db_uri, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session


def load_subscribers(settings: Settings) -> list[Subscriber]:
    statement = select(AirNomads)
    if settings.environment == "dev":
        statement = statement.where(AirNomads.id == settings.my_uuid)
    with Session(get_engine()) as session:
        return [Subscriber.from_row(row) for row in session.scalars(statement)]
