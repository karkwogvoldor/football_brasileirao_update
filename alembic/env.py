from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import make_url

import models


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = models.Base.metadata


def _migration_url() -> str:
    migration_url = os.getenv("MIGRATION_DATABASE_URL") or config.get_main_option(
        "sqlalchemy.url"
    )
    if not migration_url:
        raise RuntimeError(
            "Defina MIGRATION_DATABASE_URL ou sqlalchemy.url explicitamente"
        )

    application_url = os.getenv("DATABASE_URL")
    allow_production = os.getenv("ALLOW_PRODUCTION_MIGRATIONS") == "1"
    if application_url and not allow_production:
        migration_target = make_url(migration_url).render_as_string(hide_password=False)
        application_target = make_url(application_url).render_as_string(
            hide_password=False
        )
        if migration_target == application_target:
            raise RuntimeError(
                "MIGRATION_DATABASE_URL não pode ser igual à DATABASE_URL sem "
                "ALLOW_PRODUCTION_MIGRATIONS=1"
            )
    return migration_url


def run_migrations_offline() -> None:
    context.configure(
        url=_migration_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _migration_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
