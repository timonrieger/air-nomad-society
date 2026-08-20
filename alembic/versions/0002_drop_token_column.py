"""drop token column

Email links are stateless JWTs now; nothing reads the stored token.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch mode: plain DROP COLUMN on Postgres, table recreate on sqlite
    # (sqlite cannot drop a column that carries a UNIQUE constraint).
    with op.batch_alter_table("air_nomads") as batch:
        batch.drop_column("token")


def downgrade() -> None:
    # The original values are unrecoverable; restore the column as nullable.
    op.add_column("air_nomads", sa.Column("token", sa.String(), nullable=True))
