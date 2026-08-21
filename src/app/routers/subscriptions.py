from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.config import get_settings
from src.app.db import AirNomads, get_session
from src.app.models.subscriber import Subscriber, SubscriptionIn
from src.app.services import emails
from src.app.services.tokens import Action, verify_token

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

# At most one confirmation email per address per day: the endpoint is public
# and takes any address, so unthrottled resends are an email-bombing lever.
RESEND_COOLDOWN = timedelta(days=1)


def _columns(payload: SubscriptionIn) -> dict[str, Any]:
    # The dumped field names match the AirNomads columns, so new scalar
    # preferences persist without touching this function.
    return payload.model_dump(
        exclude={"departure_airports", "favorite_countries", "excluded_countries"}
    ) | {
        "departure_airports": ",".join(payload.departure_airports),
        "travel_countries": ",".join(payload.favorite_countries),
        "excluded_countries": ",".join(payload.excluded_countries) or None,
    }


def _apply(member: AirNomads, payload: SubscriptionIn) -> None:
    for key, value in _columns(payload).items():
        setattr(member, key, value)


def _authorized_member(token: str, action: Action, session: Session) -> AirNomads:
    subscriber_id = verify_token(token, action)
    if subscriber_id is None:
        raise HTTPException(status_code=401, detail="Invalid token.")
    member = session.get(AirNomads, subscriber_id)
    if member is None:
        raise HTTPException(status_code=404, detail="No member found.")
    return member


@router.post("/subscribe")
def subscribe(payload: SubscriptionIn, session: SessionDep) -> Subscriber:
    """Create an unconfirmed subscription and email a confirmation link.

    Re-subscribing an unconfirmed email updates the pending row and resends
    the link (so a lost email is recoverable) — but only once the pending
    row is a day old; a confirmed email is a 409.
    """
    member = session.scalar(select(AirNomads).where(AirNomads.email == payload.email))
    if member is not None and member.confirmed_at is not None:
        raise HTTPException(
            status_code=409,
            detail="This email is already subscribed. Use the update link from "
            "any digest email to change preferences.",
        )
    recently_invited = (
        member is not None and member.created_at > datetime.now() - RESEND_COOLDOWN
    )
    if member is None:
        member = AirNomads(**_columns(payload))
        session.add(member)
    else:
        _apply(member, payload)
    session.commit()
    if not recently_invited:
        emails.send_confirmation(
            member.id, member.username, member.email, get_settings()
        )
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
    _apply(member, payload)
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
