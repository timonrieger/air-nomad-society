from pydantic import BaseModel, Field


class SentHistory(BaseModel):
    """What a subscriber has already been emailed, split for freshness rules."""

    recent_countries: set[str] = Field(
        default_factory=set,
        description="Countries sent within the freshness window",
    )
    recent_cities: set[str] = Field(
        default_factory=set,
        description="Arrival IATAs sent within the freshness window",
    )
    all_countries: set[str] = Field(
        default_factory=set,
        description="Every country ever emailed to this subscriber",
    )
