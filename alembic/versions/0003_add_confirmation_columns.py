"""add confirmation columns

Double opt-in: rows start unconfirmed and the digest only mails confirmed
subscribers. Everyone present before this migration already receives the
digest legitimately, so existing rows are backfilled as confirmed.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "air_nomads",
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.add_column("air_nomads", sa.Column("confirmed_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE air_nomads SET confirmed_at = CURRENT_TIMESTAMP")


def downgrade() -> None:
    with op.batch_alter_table("air_nomads") as batch:
        batch.drop_column("confirmed_at")
        batch.drop_column("created_at")
