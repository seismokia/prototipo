from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect, text

from api.db.models import DEMO_USER_ID, DEMO_USER_NAME, Base

SPEC_TABLES = {
    "usuario",
    "perfil",
    "objetivo",
    "plan",
    "conocimiento_usuario",
    "pildora",
    "respuesta_pildora",
    "mensaje",
}


def test_migrations_create_the_tables_of_the_specification(db_engine: Engine) -> None:
    tables = set(inspect(db_engine).get_table_names())

    assert tables == SPEC_TABLES | {"alembic_version"}


def test_migrations_seed_the_demo_user(db_engine: Engine) -> None:
    with db_engine.connect() as connection:
        rows = connection.execute(text("SELECT id, nombre FROM usuario")).all()

    assert rows == [(DEMO_USER_ID, DEMO_USER_NAME)]


def test_orm_models_match_the_migrated_schema(db_engine: Engine) -> None:
    with db_engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)

    assert differences == []


def test_migrations_can_be_reverted_and_reapplied(
    db_engine: Engine, alembic_config: Config
) -> None:
    command.downgrade(alembic_config, "base")
    try:
        assert set(inspect(db_engine).get_table_names()) == {"alembic_version"}
    finally:
        command.upgrade(alembic_config, "head")

    assert SPEC_TABLES <= set(inspect(db_engine).get_table_names())
