"""discoveries become a toggle

gem_count let every subscriber set how many surprise destinations their
digest carried. Each one is a searched country, so the number was a
per-subscriber multiplier on the run's shared provider quota (#63). It is
now a yes/no, with the count fixed at DISCOVERIES_PER_DIGEST.

Existing rows keep their intent: anyone who had discoveries switched off
(gem_count 0) stays off, everyone else stays on.

Revision ID: 0012
Revises: 0011
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The default covers every existing row; only the opted-out ones differ,
    # and the server default also satisfies SQLite's ADD COLUMN NOT NULL rule.
    op.add_column(
        "air_nomads",
        sa.Column(
            "include_discoveries",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.execute("UPDATE air_nomads SET include_discoveries = false WHERE gem_count = 0")
    with op.batch_alter_table("air_nomads") as batch:
        batch.drop_column("gem_count")


def downgrade() -> None:
    # Lossy: the per-subscriber count is gone, so opted-in rows come back at
    # the fixed count and opted-out rows at zero.
    op.add_column(
        "air_nomads",
        sa.Column("gem_count", sa.Integer(), nullable=False, server_default="5"),
    )
    op.execute(
        "UPDATE air_nomads SET gem_count = CASE WHEN include_discoveries THEN 3 ELSE 0 END"
    )
    with op.batch_alter_table("air_nomads") as batch:
        batch.drop_column("include_discoveries")
