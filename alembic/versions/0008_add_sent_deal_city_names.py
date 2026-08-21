"""add sent_deal city names

The public deal wall shows routes by city name ("Frankfurt → Lisbon"),
but sent_deal only stored IATA codes and the arrival city name is not
derivable from reference data. Nullable: names for rows sent before this
migration are unknowable, and the wall falls back to the country.

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sent_deal", sa.Column("departure_city", sa.String(), nullable=True))
    op.add_column("sent_deal", sa.Column("arrival_city", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("sent_deal", "arrival_city")
    op.drop_column("sent_deal", "departure_city")
