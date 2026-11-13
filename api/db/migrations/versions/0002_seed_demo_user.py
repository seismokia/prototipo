"""Seed the demo user (docs/SPEC.md 3.6: the prototype has no real authentication).

Revision ID: 0002
Revises: 0001
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Literal copies of api.db.models.DEMO_USER_ID / DEMO_USER_NAME: a migration must
# not change if the application constants do.
DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_USER_NAME = "Usuario de demostración"

user_table = sa.table("usuario", sa.column("id", sa.Uuid()), sa.column("nombre", sa.Text()))


def upgrade() -> None:
    op.execute(
        insert(user_table)
        .values(id=DEMO_USER_ID, nombre=DEMO_USER_NAME)
        .on_conflict_do_nothing(index_elements=["id"])
    )


def downgrade() -> None:
    op.execute(sa.delete(user_table).where(user_table.c.id == DEMO_USER_ID))
