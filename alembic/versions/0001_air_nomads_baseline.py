"""air_nomads baseline

The table as it existed when this project took ownership of the schema
from database-service. Existing databases are adopted with
`alembic stamp 0001`; fresh databases are created by `upgrade head`.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "air_nomads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("departure_city", sa.String(), nullable=False),
        sa.Column("departure_iata", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("min_nights", sa.Integer(), nullable=False),
        sa.Column("max_nights", sa.Integer(), nullable=False),
        sa.Column("travel_countries", sa.String(), nullable=False),
        sa.Column("excluded_countries", sa.String(), nullable=True),
        sa.Column("token", sa.String(), nullable=False, unique=True),
        sa.Column("min_days_ahead", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_days_ahead", sa.Integer(), nullable=False, server_default="182"),
    )


def downgrade() -> None:
    op.drop_table("air_nomads")
