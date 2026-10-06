"""subscriber countries follow Kiwi's names

data.json's countries are now synced from Tequila, which names some of
them differently — and Tequila already reports deals under those names, so
sent_deal and price_observation need no rewrite. Countries without an active
airport left the reference data and are dropped from preferences.

Revision ID: 0015
Revises: 0014
"""

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

RENAMED = {
    "Antigua and Barbuda": "Antigua & Barbuda",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "Czech Republic": "Czechia",
    "East Timor": "Timor-Leste",
    "Ivory Coast": "Côte d’Ivoire",
    "Myanmar": "Myanmar (Burma)",
    "North Macedonia": "Republic of North Macedonia",
    "Saint Kitts and Nevis": "St. Kitts & Nevis",
    "Saint Lucia": "St. Lucia",
    "Saint Vincent and the Grenadines": "St. Vincent & Grenadines",
    "Sao Tome and Principe": "São Tomé & Príncipe",
    "Trinidad and Tobago": "Trinidad & Tobago",
}
REMOVED = {"American Samoa", "Belarus", "Cuba", "Monaco", "Russia", "Ukraine"}


def _rewrite(joined: str | None, mapping: dict[str, str], removed: set[str]) -> str:
    names = [part.strip() for part in joined.split(",")] if joined else []
    return ",".join(mapping.get(name, name) for name in names if name not in removed)


def _migrate(mapping: dict[str, str], removed: set[str]) -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, travel_countries, excluded_countries FROM air_nomads")
    )
    for row_id, travel, excluded in rows.all():
        bind.execute(
            sa.text(
                "UPDATE air_nomads SET travel_countries = :travel, "
                "excluded_countries = :excluded WHERE id = :id"
            ),
            {
                "id": row_id,
                "travel": _rewrite(travel, mapping, removed),
                "excluded": _rewrite(excluded, mapping, removed) or None,
            },
        )


def upgrade() -> None:
    _migrate(RENAMED, REMOVED)


def downgrade() -> None:
    # Lossy: removed countries are not restored.
    _migrate({new: old for old, new in RENAMED.items()}, set())
