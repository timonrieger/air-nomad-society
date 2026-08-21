"""Stateless JWT links for email actions.

Tokens carry the subscriber id and the permitted action, signed with
SECRET_KEY (HS256). They never expire on purpose: unsubscribe links in old
digests must always work. Revocation means rotating the secret.
"""

from datetime import UTC, datetime
from typing import Literal

import jwt

from src.config import get_settings

Action = Literal["update", "unsubscribe", "confirm"]
ALGORITHM = "HS256"


def issue_token(subscriber_id: int, action: Action) -> str:
    payload = {"sub": str(subscriber_id), "action": action, "iat": datetime.now(UTC)}
    return jwt.encode(payload, get_settings().secret_key, algorithm=ALGORITHM)


def verify_token(token: str, action: Action) -> int | None:
    """The subscriber id the token grants `action` for, or None."""
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    if payload.get("action") != action:
        return None
    return int(payload["sub"])
