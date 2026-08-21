"""add air_nomads cadence and gem_count

Quality-of-life preferences: how often the digest arrives (weekly or
biweekly, enforced as a due-filter on the weekly run) and how many
surprise discoveries each email carries (previously hardcoded at 5).
Server defaults keep every existing subscriber on today's behavior.

Revision ID: 0009
Revises: 0008
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "air_nomads",
        sa.Column("cadence", sa.String(), nullable=False, server_default="weekly"),
    )
    op.add_column(
        "air_nomads",
        sa.Column("gem_count", sa.Integer(), nullable=False, server_default="5"),
    )


def downgrade() -> None:
    op.drop_column("air_nomads", "gem_count")
    op.drop_column("air_nomads", "cadence")
