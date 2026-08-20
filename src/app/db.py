"""Database access: schema, engine, and session plumbing for `air_nomads`."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import lru_cache

from sqlalchemy import (
    CursorResult,
    DateTime,
    Engine,
    Integer,
    String,
    create_engine,
    delete,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.app.config import get_settings
from src.app.models.subscriber import Subscriber

UNCONFIRMED_TTL_DAYS = 7


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
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    assert settings.db_uri, "DB_URI is not configured"
    return create_engine(settings.db_uri, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    # expire_on_commit=False: attribute reads after commit stay in memory
    # instead of re-SELECTing — one round trip saved per write endpoint.
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session


session_scope = contextmanager(get_session)


def load_subscribers(only_id: int | None = None) -> list[Subscriber]:
    """Confirmed subscribers only — unconfirmed rows never receive the digest."""
    statement = select(AirNomads).where(AirNomads.confirmed_at.is_not(None))
    if only_id is not None:
        statement = statement.where(AirNomads.id == only_id)
    with session_scope() as session:
        return [Subscriber.from_row(row) for row in session.scalars(statement)]


def purge_unconfirmed() -> int:
    """Deletes rows that never confirmed within the TTL; returns the count."""
    cutoff = datetime.now() - timedelta(days=UNCONFIRMED_TTL_DAYS)
    statement = delete(AirNomads).where(
        AirNomads.confirmed_at.is_(None), AirNomads.created_at < cutoff
    )
    with session_scope() as session:
        result = session.execute(statement)
        session.commit()
        assert isinstance(result, CursorResult)  # DML always returns a cursor
        return result.rowcount
