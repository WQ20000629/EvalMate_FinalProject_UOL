# ------------------------------------------------------------------
# File: backend/alembic/env.py
# Purpose: Configures Alembic so it can run database migrations for the app models.
# ------------------------------------------------------------------

# Import the libraries needed to run migrations
import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the project root to the Python path so Alembic can import app files
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# Load DATABASE_URL from backend/.env
load_dotenv()

# Import the database base and all models so Alembic knows the tables
from app.core.database import Base  # noqa: E402
from app.core import db_models  # noqa: E402,F401

# This is the Alembic config object
config = context.config

# Use the DATABASE_URL from the environment if it exists
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Set up logging from the Alembic config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This tells Alembic which metadata to check for schema changes
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a database engine."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


# Pick the migration mode based on how Alembic was started
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
