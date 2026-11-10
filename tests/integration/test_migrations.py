from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def migration_config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


# Verifica que um banco vazio pode subir até o catálogo e voltar à base vazia.
def test_migrations_upgrade_and_downgrade_on_temporary_database(tmp_path, monkeypatch):
    database_path = tmp_path / "migrations_test.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.delenv("MIGRATION_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    config = migration_config(database_url)

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    expected_tables = {
        "alembic_version",
        "browser_sessions",
        "clubs",
        "competitions",
        "fixtures",
        "game_saves",
        "jogadores",
        "seasons",
        "times",
    }
    assert set(inspect(engine).get_table_names()) == expected_tables
    engine.dispose()

    command.downgrade(config, "base")
    engine = create_engine(database_url)
    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()


# Impede que uma migração use a mesma URL configurada para a aplicação por engano.
def test_migrations_refuse_application_database_without_explicit_override(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "protected_test.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.delenv("MIGRATION_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.delenv("ALLOW_PRODUCTION_MIGRATIONS", raising=False)

    config = migration_config(database_url)
    try:
        command.upgrade(config, "head")
    except RuntimeError as error:
        assert "não pode ser igual" in str(error)
    else:
        raise AssertionError("A migração deveria recusar a DATABASE_URL da aplicação")
