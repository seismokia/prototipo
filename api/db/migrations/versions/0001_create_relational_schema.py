"""Create the relational schema of docs/SPEC.md section 5.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONEY = sa.Numeric(12, 2)


def _user_fk(*, primary_key: bool = False) -> sa.Column:
    return sa.Column(
        "usuario_id",
        sa.Uuid(),
        sa.ForeignKey("usuario.id", ondelete="CASCADE"),
        primary_key=primary_key,
        nullable=False,
    )


def _timestamp(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nombre", sa.Text(), nullable=False),
        _timestamp("creado_en"),
    )
    op.create_table(
        "perfil",
        _user_fk(primary_key=True),
        sa.Column("ingresos", MONEY, nullable=False),
        sa.Column("gastos", MONEY, nullable=False),
        sa.Column("cuota_deuda", MONEY, nullable=False),
        sa.Column("ahorro_actual", MONEY, nullable=False),
        sa.Column("personas_a_cargo", sa.Integer(), nullable=False),
        sa.Column("perfil_riesgo", sa.String(20), nullable=False),
        _timestamp("actualizado_en"),
        sa.CheckConstraint(
            "perfil_riesgo IN ('conservador', 'moderado', 'dinamico')",
            name="ck_perfil_perfil_riesgo",
        ),
    )
    op.create_table(
        "objetivo",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_fk(),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("importe", MONEY, nullable=False),
        sa.Column("plazo_meses", sa.SmallInteger(), nullable=False),
        sa.Column("prioridad", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("importe > 0", name="ck_objetivo_importe"),
        sa.CheckConstraint("plazo_meses BETWEEN 1 AND 60", name="ck_objetivo_plazo_meses"),
        sa.CheckConstraint("prioridad BETWEEN 1 AND 3", name="ck_objetivo_prioridad"),
    )
    op.create_index("ix_objetivo_usuario_id", "objetivo", ["usuario_id"])
    op.create_table(
        "plan",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_fk(),
        sa.Column("parametros_version", sa.String(50), nullable=False),
        sa.Column("resultado_json", JSONB(), nullable=False),
        _timestamp("creado_en"),
    )
    op.create_index("ix_plan_usuario_id", "plan", ["usuario_id"])
    op.create_table(
        "conocimiento_usuario",
        _user_fk(primary_key=True),
        sa.Column("tema", sa.String(50), primary_key=True),
        sa.Column("nivel", sa.SmallInteger(), nullable=False),
        _timestamp("actualizado_en"),
    )
    op.create_table(
        "pildora",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_fk(),
        sa.Column("tema", sa.String(50), nullable=False),
        sa.Column("nivel", sa.SmallInteger(), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("preguntas_json", JSONB(), nullable=False),
        sa.Column("fragmentos_ids", JSONB(), nullable=False),
        _timestamp("creado_en"),
    )
    op.create_index("ix_pildora_usuario_id", "pildora", ["usuario_id"])
    op.create_table(
        "respuesta_pildora",
        sa.Column(
            "pildora_id",
            sa.Uuid(),
            sa.ForeignKey("pildora.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("pregunta_idx", sa.SmallInteger(), primary_key=True),
        sa.Column("correcta", sa.Boolean(), nullable=False),
        _timestamp("creado_en"),
    )
    op.create_table(
        "mensaje",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_fk(),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("traza_id", sa.String(64), nullable=True),
        _timestamp("creado_en"),
    )
    op.create_index("ix_mensaje_usuario_id", "mensaje", ["usuario_id"])


def downgrade() -> None:
    for table in (
        "mensaje",
        "respuesta_pildora",
        "pildora",
        "conocimiento_usuario",
        "plan",
        "objetivo",
        "perfil",
        "usuario",
    ):
        op.drop_table(table)
