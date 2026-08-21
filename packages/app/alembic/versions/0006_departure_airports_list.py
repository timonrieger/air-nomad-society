"""departure airports become a list column

Multi-departure: departure_airports is a comma-joined IATA list mirroring
travel_countries — NOT a relational split; all other preferences stay
shared per subscriber. The data migration folds the existing single
departure_iata in; departure_city goes away entirely (the email shows the
per-deal departure city from the provider, and forms resolve names from
reference data).

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "air_nomads", sa.Column("departure_airports", sa.String(), nullable=True)
    )
    op.execute("UPDATE air_nomads SET departure_airports = departure_iata")
    with op.batch_alter_table("air_nomads") as batch:
        batch.alter_column("departure_airports", nullable=False)
        batch.drop_column("departure_iata")
        batch.drop_column("departure_city")


def downgrade() -> None:
    # Lossy: a single-airport row round-trips exactly; a multi-airport row
    # keeps the joined list in departure_iata and needs manual attention.
    # departure_city is not recoverable here (names live in reference data).
    with op.batch_alter_table("air_nomads") as batch:
        batch.add_column(sa.Column("departure_iata", sa.String(), nullable=True))
        batch.add_column(sa.Column("departure_city", sa.String(), nullable=True))
    op.execute("UPDATE air_nomads SET departure_iata = departure_airports")
    op.execute("UPDATE air_nomads SET departure_city = departure_airports")
    with op.batch_alter_table("air_nomads") as batch:
        batch.alter_column("departure_iata", nullable=False)
        batch.alter_column("departure_city", nullable=False)
        batch.drop_column("departure_airports")
