"""
Alembic environment configuration for court-monitor database migrations.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Build a synchronous SQLAlchemy URL for migrations."""
    cs = os.environ.get("AZURE_SQL_CONNECTION_STRING", "")
    if cs.startswith("mssql"):
        # Replace async driver with sync pyodbc for alembic
        return cs.replace("mssql+aioodbc", "mssql+pyodbc")
    if cs:
        import urllib.parse
        params = urllib.parse.quote_plus(cs)
        return f"mssql+pyodbc:///?odbc_connect={params}"
    raise RuntimeError("AZURE_SQL_CONNECTION_STRING is not set")


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generate SQL script)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
