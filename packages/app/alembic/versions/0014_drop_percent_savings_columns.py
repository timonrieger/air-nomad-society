"""drop the percent-savings columns from sent deals

The product's value claim moved from percent-below-typical to "lowest
price since <date>", and claims are derived from price observations at
read time rather than frozen on the row — sent_deal keeps only facts.
The raw observations remain the source of truth, so historical savings
stay recomputable.

Revision ID: 0014
Revises: 0013
"""

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("sent_deal", "savings_percent")
    op.drop_column("sent_deal", "usual_price")


def downgrade() -> None:
    op.add_column(
        "sent_deal", sa.Column("savings_percent", sa.Integer(), nullable=True)
    )
    op.add_column("sent_deal", sa.Column("usual_price", sa.Integer(), nullable=True))
