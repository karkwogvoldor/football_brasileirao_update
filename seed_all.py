"""Populate a local BRAFOOT database without calling external services."""

from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from brafoot.catalog.seeder import seed_brasileirao_2026


PROJECT_ROOT = Path(__file__).resolve().parent


def validate_local_seed_url(database_url: str) -> None:
    parsed = make_url(database_url)
    if parsed.get_backend_name() == "sqlite":
        database_name = parsed.database or ""
        if database_name == ":memory:":
            return
        if not database_name.endswith(("_dev.db", "_test.db")):
            raise RuntimeError("O banco SQLite de seed deve terminar em _dev.db ou _test.db")
        return

    if parsed.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("Seeds só podem usar um banco local")
    if not (parsed.database or "").endswith(("_dev", "_test")):
        raise RuntimeError("O banco local deve terminar em _dev ou _test")


def run_seed(database_url: str) -> None:
    validate_local_seed_url(database_url)
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(alembic_config, "head")

    engine = create_engine(database_url)
    testing_session = sessionmaker(bind=engine)
    with testing_session() as session:
        season = seed_brasileirao_2026(session)
        print(
            f"Seed local concluído: {season.name}, "
            f"{len(season.fixtures)} partidas."
        )
    engine.dispose()


if __name__ == "__main__":
    seed_url = os.getenv("SEED_DATABASE_URL")
    if not seed_url:
        raise SystemExit(
            "Defina SEED_DATABASE_URL para um banco local terminado em _dev ou _test."
        )
    run_seed(seed_url)
