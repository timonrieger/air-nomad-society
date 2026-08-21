"""add sent_deal.reason

The AI reasoning line shown on each emailed deal card, logged for
debugging ("why did I get this deal?"). Nullable: the AI path is optional
and reasons are skipped whenever it is unconfigured or fails.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sent_deal", sa.Column("reason", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("sent_deal", "reason")
