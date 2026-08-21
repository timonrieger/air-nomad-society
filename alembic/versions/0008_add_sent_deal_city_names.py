"""add sent_deal wall columns

The public deal wall shows send-time facts that are unknowable after the
fact: the city names ("Frankfurt → Lisbon" — flyFrom airports like LHR
are not in reference data), the searched origin (the observation
partition key), and the savings percent the digest email quoted (the
wall must show the same number, and baselines drift). All nullable: rows
sent before this migration have none, and the wall falls back gracefully.
The sent_at index serves the wall's recency window.

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
    op.add_column("sent_deal", sa.Column("origin_iata", sa.String(), nullable=True))
    op.add_column(
        "sent_deal", sa.Column("savings_percent", sa.Integer(), nullable=True)
    )
    op.create_index("ix_sent_deal_sent_at", "sent_deal", ["sent_at"])


def downgrade() -> None:
    op.drop_index("ix_sent_deal_sent_at", table_name="sent_deal")
    op.drop_column("sent_deal", "savings_percent")
    op.drop_column("sent_deal", "origin_iata")
    op.drop_column("sent_deal", "arrival_city")
    op.drop_column("sent_deal", "departure_city")
