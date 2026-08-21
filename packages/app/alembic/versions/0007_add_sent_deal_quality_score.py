"""add sent_deal.quality_score

sent_deal.score is the ranking score and carries the freshness repeat
penalties, so as a quality signal it conflates "worse deal" with
"repeat". The pure comfort-adjusted score is now recorded alongside it,
keeping history clean for anything that reads scores as quality.
The server default only satisfies SQLite's ADD COLUMN NOT NULL rule;
existing rows are backfilled from score — exact for every unpenalized
row and a tight upper bound otherwise — and the digest always writes
the real value going forward.

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sent_deal",
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0"),
    )
    op.execute("UPDATE sent_deal SET quality_score = score")


def downgrade() -> None:
    op.drop_column("sent_deal", "quality_score")
