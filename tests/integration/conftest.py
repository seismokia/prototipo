"""Fixtures for the integration tests: a real PostgreSQL database built with the migrations.

The tests need ``TEST_DATABASE_URL`` (set by docker-compose.yml and the CI) and are
skipped without it. The database is created on demand and its name must end in
``_test``, because the fixtures drop and truncate its contents.
"""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import Session, sessionmaker

from api.db.session import get_session
from api.deps import get_parameters
from api.main import app
from engine.parameters import Parameters
from tests.unit.engine.conftest import RAW_PARAMETERS

TEST_DATABASE_SUFFIX = "_test"
# Every table except `usuario`, which holds the demo user created by the migrations.
USER_DATA_TABLES = (
    "perfil, objetivo, plan, conocimiento_usuario, pildora, respuesta_pildora, mensaje"
)


def _create_database_if_missing(url: str) -> None:
    target = make_url(url)
    admin_engine = create_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": target.database}
        )
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{target.database}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set: integration tests need PostgreSQL")
    database = make_url(url).database or ""
    if not database.endswith(TEST_DATABASE_SUFFIX):
        raise RuntimeError(
            f"TEST_DATABASE_URL must point to a database ending in {TEST_DATABASE_SUFFIX!r}"
        )
    return url


@pytest.fixture(scope="session")
def alembic_config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.attributes["database_url"] = database_url
    config.attributes["configure_logging"] = False
    return config


@pytest.fixture(scope="session")
def db_engine(database_url: str, alembic_config: Config) -> Iterator[Engine]:
    """Empty database brought to the latest revision by the real migrations."""
    _create_database_if_missing(database_url)
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    command.upgrade(alembic_config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(db_engine: Engine) -> Iterator[sessionmaker[Session]]:
    yield sessionmaker(bind=db_engine, expire_on_commit=False)
    with db_engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {USER_DATA_TABLES} CASCADE"))


@pytest.fixture
def params() -> Parameters:
    """Fixed parameters, so the expected figures do not depend on the illustrative YAML."""
    return Parameters.model_validate(RAW_PARAMETERS)


@pytest.fixture
def client(session_factory: sessionmaker[Session], params: Parameters) -> Iterator[TestClient]:
    def override_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_parameters] = lambda: params
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
