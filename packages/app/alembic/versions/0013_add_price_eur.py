"""add price_eur to observations and sent deals

The provider's EUR conversion of every fare, stored next to the native
price so baselines pool across currencies and the public wall can always
display euros. Backfilled from the native price for every existing row —
exact for EUR rows (Tequila's EUR conversion equals the price there), an
accepted approximation for the handful of older non-EUR rows — so the
column is NOT NULL and the code never handles missing conversions.

Revision ID: 0013
Revises: 0012
"""

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "price_observation", sa.Column("price_eur", sa.Float(), nullable=True)
    )
    op.execute("UPDATE price_observation SET price_eur = price")
    op.alter_column("price_observation", "price_eur", nullable=False)

    op.add_column("sent_deal", sa.Column("price_eur", sa.Float(), nullable=True))
    op.execute("UPDATE sent_deal SET price_eur = price")
    op.alter_column("sent_deal", "price_eur", nullable=False)


def downgrade() -> None:
    op.drop_column("sent_deal", "price_eur")
    op.drop_column("price_observation", "price_eur")
