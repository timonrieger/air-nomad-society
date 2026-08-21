"""add sent_deal usual_price

The route's typical price as the digest email quoted it — the whole-unit
integer its "typically ~X" anchor printed — frozen on the row so the
public wall shows the very number the email showed, immune to baseline
drift. Nullable: routes without enough history have no baseline, and rows
from before this migration never recorded one.

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sent_deal", sa.Column("usual_price", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("sent_deal", "usual_price")
