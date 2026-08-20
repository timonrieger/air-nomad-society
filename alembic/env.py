from alembic import context
from sqlalchemy import create_engine

from src.config import get_settings
from src.db import Base

target_metadata = Base.metadata

settings = get_settings()
assert settings.db_uri, "DB_URI is not configured"
engine = create_engine(settings.db_uri)
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
