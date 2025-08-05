# alembic/env.py
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool

from alembic import context

# --- Make "src/" importable so we can import our models ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # repo root
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# --- Import your model metadata ---
from ai_rag_agent.persistence.models import Base  # noqa: E402

# Alembic Config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def get_url() -> str:
    """
    Prefer APP_DB_DSN from env; fallback to sqlalchemy.url in alembic.ini if set.
    Use async DSN: postgresql+asyncpg://user:pass@host:port/db
    """
    return (
        os.getenv("APP_DB_DSN")
        or config.get_main_option("sqlalchemy.url")
        or "postgresql+asyncpg://rag:rag@localhost:5432/rag"
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """
    Synchronous body executed inside connection.run_sync(...).
    IMPORTANT: use *sync* context manager here (no 'async with').
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    from sqlalchemy.ext.asyncio import async_engine_from_config

    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    import asyncio

    async def _run() -> None:
        async with connectable.connect() as connection:
            # Run the *sync* migrator function under run_sync
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    asyncio.run(_run())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
