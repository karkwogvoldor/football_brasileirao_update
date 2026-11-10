import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import get_db
from main import create_app


def _test_database_url() -> str:
    test_url = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    production_url = os.getenv("DATABASE_URL")

    if production_url and make_url(test_url).render_as_string(hide_password=False) == make_url(
        production_url
    ).render_as_string(hide_password=False):
        pytest.exit("TEST_DATABASE_URL não pode ser igual à DATABASE_URL", returncode=2)

    parsed = make_url(test_url)
    if parsed.get_backend_name() == "sqlite":
        database_name = parsed.database or ":memory:"
        if database_name != ":memory:" and not database_name.endswith("_test.db"):
            pytest.exit(
                "Um arquivo SQLite de integração deve terminar em '_test.db'",
                returncode=2,
            )
    else:
        database_name = parsed.database or ""
        if not database_name.endswith("_test"):
            pytest.exit(
                "O banco de integração deve ter nome terminado em '_test'",
                returncode=2,
            )

    return test_url


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    test_url = _test_database_url()
    parsed = make_url(test_url)
    engine_options: dict = {}

    if parsed.get_backend_name() == "sqlite":
        engine_options = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }

    engine = create_engine(test_url, **engine_options)

    if parsed.get_backend_name() == "sqlite":
        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    yield engine
    engine.dispose()


@pytest.fixture()
def reset_database(test_engine: Engine) -> Generator[None, None, None]:
    models.Base.metadata.drop_all(bind=test_engine)
    models.Base.metadata.create_all(bind=test_engine)
    yield
    models.Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session(
    test_engine: Engine, reset_database: None
) -> Generator[Session, None, None]:
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    session = testing_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def app(db_session: Session):
    application = create_app(create_schema=False)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client

