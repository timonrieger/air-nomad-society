"""add sent_deal.arrival_city

The public deal wall shows routes by city name ("Frankfurt → Lisbon").
Departure names are derivable from reference data at read time, but the
arrival city is provider-discovered and unknowable after the fact — so
only it is persisted. Nullable: rows sent before this migration have no
name and the wall falls back to the country.

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
    op.add_column("sent_deal", sa.Column("arrival_city", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("sent_deal", "arrival_city")
