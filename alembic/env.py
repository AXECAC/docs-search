import os
import asyncio
from logging.config import fileConfig
from dotenv import load_dotenv

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Загружаем переменные из .env (нужно для команд `alembic` из терминала)
load_dotenv()

# Alembic Config object
config = context.config

# Настройка логирования из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --------------------------------------------------------------
# Подключаем все модели, чтобы autogenerate видел изменения
# --------------------------------------------------------------
from app.database import Base  # noqa: E402
import app.models  # noqa: F401, E402 - важно: просто импортируем, чтобы модели зарегистрировались

target_metadata = Base.metadata

# --------------------------------------------------------------
# Берём DATABASE_URL из переменной окружения.
# Alembic не умеет работать с asyncpg напрямую, поэтому
# заменяем драйвер: asyncpg → psycopg2 (синхронный) для offline,
# и используем async_engine_from_config для online.
# --------------------------------------------------------------
def get_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    # Для async-движка оставляем asyncpg; alembic использует его через run_sync
    return url


def run_migrations_offline() -> None:
    """Offline mode: генерирует SQL-скрипт без подключения к БД."""
    # В offline-режиме используем синхронный URL (psycopg2)
    url = get_url().replace("postgresql+asyncpg://", "postgresql://")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Online mode: подключается к БД и применяет миграции."""
    # Переопределяем URL из env для async engine
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Online mode entry point."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
