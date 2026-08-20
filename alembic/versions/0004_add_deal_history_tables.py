"""add deal history tables

Append-only history written by the digest job: every candidate itinerary a
search returned (price_observation) and every deal actually emailed
(sent_deal). Feeds the "vs typical price" anchor and freshness downweighting.
sent_deal.subscriber_id has no foreign key on purpose: history stays useful
after unsubscribes.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_observation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("origin_iata", sa.String(), nullable=False),
        sa.Column("destination_iata", sa.String(), nullable=False),
        sa.Column("arrival_country", sa.String(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("departs_at", sa.DateTime(), nullable=False),
        sa.Column("returns_at", sa.DateTime(), nullable=False),
        sa.Column(
            "observed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "sent_deal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subscriber_id", sa.Integer(), nullable=False),
        sa.Column("origin_iata", sa.String(), nullable=False),
        sa.Column("destination_iata", sa.String(), nullable=False),
        sa.Column("arrival_country", sa.String(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column(
            "sent_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("sent_deal")
    op.drop_table("price_observation")
