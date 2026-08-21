"""add sent_deal link, restarting the table

The booking deep link — provider-agnostic, whatever provider found the
fare — joins the frozen send-time facts so the public wall can link
straight to the fare. Existing rows predate the column and are wiped
rather than backfilled: sent history rebuilds itself within weeks and
nothing else depends on it.

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM sent_deal")
    op.add_column(
        "sent_deal",
        sa.Column("link", sa.String(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("sent_deal", "link")
