from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.config import get_settings
from src.app.db import AirNomads, get_session
from src.app.models.subscriber import Subscriber
from src.app.services import emails, mailer, refdata
from src.app.services.tokens import Action, issue_token, verify_token

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


class SubscriptionIn(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    departure_iata: str
    currency: str
    min_nights: int = Field(ge=1)
    max_nights: int = Field(ge=1)
    min_days_ahead: int = Field(ge=1, le=365)
    max_days_ahead: int = Field(ge=1, le=365)
    favorite_countries: list[str] = Field(min_length=1)
    excluded_countries: list[str] = []

    @field_validator("departure_iata")
    @classmethod
    def _known_city(cls, value: str) -> str:
        if value not in {city.code for city in refdata.load().cities}:
            raise ValueError("unknown departure city code")
        return value

    @field_validator("currency")
    @classmethod
    def _known_currency(cls, value: str) -> str:
        if value not in refdata.currency_choices():
            raise ValueError("unknown currency")
        return value

    @field_validator("favorite_countries", "excluded_countries")
    @classmethod
    def _known_countries(cls, value: list[str]) -> list[str]:
        unknown = set(value) - set(refdata.country_choices())
        if unknown:
            raise ValueError(f"unknown countries: {', '.join(sorted(unknown))}")
        return value

    @model_validator(mode="after")
    def _ranges(self) -> "SubscriptionIn":
        if self.max_nights <= self.min_nights:
            raise ValueError("max_nights must be greater than min_nights")
        if self.max_days_ahead <= self.min_days_ahead:
            raise ValueError("max_days_ahead must be greater than min_days_ahead")
        search_range = self.max_days_ahead - self.min_days_ahead
        if self.max_nights > search_range:
            raise ValueError(
                f"max_nights ({self.max_nights}) cannot exceed the search "
                f"range duration ({search_range} days)"
            )
        return self


def _columns(payload: SubscriptionIn) -> dict[str, Any]:
    return {
        "username": payload.username,
        "email": payload.email,
        "departure_city": refdata.city_name(payload.departure_iata),
        "departure_iata": payload.departure_iata,
        "currency": payload.currency,
        "min_nights": payload.min_nights,
        "max_nights": payload.max_nights,
        "min_days_ahead": payload.min_days_ahead,
        "max_days_ahead": payload.max_days_ahead,
        "travel_countries": ",".join(payload.favorite_countries),
        "excluded_countries": ",".join(payload.excluded_countries) or None,
    }


def _authorized_member(token: str, action: Action, session: Session) -> AirNomads:
    subscriber_id = verify_token(token, action)
    if subscriber_id is None:
        raise HTTPException(status_code=401, detail="Invalid token.")
    member = session.get(AirNomads, subscriber_id)
    if member is None:
        raise HTTPException(status_code=404, detail="No member found.")
    return member


def _send_confirmation(member: AirNomads) -> None:
    settings = get_settings()
    token = issue_token(member.id, "confirm")
    confirm_url = f"{settings.public_base_url}/confirm?token={token}"
    mailer.send_email(
        emails.render_confirmation(member.username, confirm_url),
        member.email,
        "Confirm your subscription",
        settings,
    )


@router.post("/subscribe")
def subscribe(payload: SubscriptionIn, session: SessionDep) -> Subscriber:
    """Create an unconfirmed subscription and email a confirmation link.

    Re-subscribing an unconfirmed email updates the pending row and resends
    the link (so a lost email is recoverable); a confirmed email is a 409.
    """
    member = session.scalar(select(AirNomads).where(AirNomads.email == payload.email))
    if member is not None and member.confirmed_at is not None:
        raise HTTPException(
            status_code=409,
            detail="This email is already subscribed. Use the update link from "
            "any digest email to change preferences.",
        )
    if member is None:
        member = AirNomads(**_columns(payload))
        session.add(member)
    else:
        for key, value in _columns(payload).items():
            setattr(member, key, value)
    session.commit()
    session.refresh(member)  # populate server defaults
    _send_confirmation(member)
    return Subscriber.from_row(member)


@router.get("/confirm")
def confirm(token: str, session: SessionDep) -> dict[str, str]:
    """GET on purpose: this is the link clicked in the confirmation email."""
    member = _authorized_member(token, "confirm", session)
    if member.confirmed_at is None:
        member.confirmed_at = datetime.now()
        session.commit()
    return {"detail": f"Subscription confirmed for {member.email}. Happy travels!"}


@router.get("/subscription")
def read_subscription(token: str, session: SessionDep) -> Subscriber:
    return Subscriber.from_row(_authorized_member(token, "update", session))


@router.put("/subscription")
def update_subscription(
    token: str, payload: SubscriptionIn, session: SessionDep
) -> Subscriber:
    member = _authorized_member(token, "update", session)
    if payload.email != member.email:
        raise HTTPException(
            status_code=400,
            detail="The email address cannot be changed. Unsubscribe and "
            "subscribe again with the new address.",
        )
    for key, value in _columns(payload).items():
        setattr(member, key, value)
    session.commit()
    return Subscriber.from_row(member)


@router.get("/unsubscribe")
def unsubscribe(token: str, session: SessionDep) -> dict[str, str]:
    """GET on purpose: this is the link subscribers click in the email."""
    member = _authorized_member(token, "unsubscribe", session)
    email = member.email
    session.delete(member)
    session.commit()
    return {"detail": f"You have successfully unsubscribed with {email}."}
