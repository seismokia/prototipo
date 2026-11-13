"""ORM models of the relational schema (docs/SPEC.md section 5).

Table and column names are the Spanish ones fixed by the specification;
Python identifiers are in English.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Fixed identifier of the demo user created by the migrations (SPEC 3.6: no real auth).
DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_USER_NAME = "Usuario de demostración"

MONEY = Numeric(12, 2)


class Base(DeclarativeBase):
    pass


def _user_fk(*, primary_key: bool = False) -> Mapped[uuid.UUID]:
    return mapped_column(
        "usuario_id",
        Uuid,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        primary_key=primary_key,
        index=not primary_key,
    )


def _created_at() -> Mapped[datetime]:
    return mapped_column("creado_en", DateTime(timezone=True), server_default=func.now())


def _updated_at() -> Mapped[datetime]:
    return mapped_column(
        "actualizado_en",
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column("nombre", Text)
    created_at: Mapped[datetime] = _created_at()


class Profile(Base):
    __tablename__ = "perfil"
    __table_args__ = (
        CheckConstraint(
            "perfil_riesgo IN ('conservador', 'moderado', 'dinamico')",
            name="ck_perfil_perfil_riesgo",
        ),
    )

    user_id: Mapped[uuid.UUID] = _user_fk(primary_key=True)
    monthly_income: Mapped[Decimal] = mapped_column("ingresos", MONEY)
    monthly_expenses: Mapped[Decimal] = mapped_column("gastos", MONEY)
    monthly_debt_payment: Mapped[Decimal] = mapped_column("cuota_deuda", MONEY)
    current_savings: Mapped[Decimal] = mapped_column("ahorro_actual", MONEY)
    dependents: Mapped[int] = mapped_column("personas_a_cargo", Integer)
    risk_profile: Mapped[str] = mapped_column("perfil_riesgo", String(20))
    updated_at: Mapped[datetime] = _updated_at()


class Goal(Base):
    __tablename__ = "objetivo"
    __table_args__ = (
        CheckConstraint("importe > 0", name="ck_objetivo_importe"),
        CheckConstraint("plazo_meses BETWEEN 1 AND 60", name="ck_objetivo_plazo_meses"),
        CheckConstraint("prioridad BETWEEN 1 AND 3", name="ck_objetivo_prioridad"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = _user_fk()
    name: Mapped[str] = mapped_column("nombre", Text)
    amount: Mapped[Decimal] = mapped_column("importe", MONEY)
    term_months: Mapped[int] = mapped_column("plazo_meses", SmallInteger)
    priority: Mapped[int] = mapped_column("prioridad", SmallInteger)


class Plan(Base):
    __tablename__ = "plan"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = _user_fk()
    parameters_version: Mapped[str] = mapped_column("parametros_version", String(50))
    result: Mapped[dict[str, Any]] = mapped_column("resultado_json", JSONB)
    created_at: Mapped[datetime] = _created_at()


# --- Tables used from phase 3 onwards (no endpoints yet) ----------------------


class UserKnowledge(Base):
    __tablename__ = "conocimiento_usuario"

    user_id: Mapped[uuid.UUID] = _user_fk(primary_key=True)
    topic: Mapped[str] = mapped_column("tema", String(50), primary_key=True)
    level: Mapped[int] = mapped_column("nivel", SmallInteger)
    updated_at: Mapped[datetime] = _updated_at()


class Lesson(Base):
    __tablename__ = "pildora"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = _user_fk()
    topic: Mapped[str] = mapped_column("tema", String(50))
    level: Mapped[int] = mapped_column("nivel", SmallInteger)
    content: Mapped[str] = mapped_column("contenido", Text)
    questions: Mapped[list[Any]] = mapped_column("preguntas_json", JSONB)
    chunk_ids: Mapped[list[Any]] = mapped_column("fragmentos_ids", JSONB)
    created_at: Mapped[datetime] = _created_at()


class LessonAnswer(Base):
    __tablename__ = "respuesta_pildora"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        "pildora_id", Uuid, ForeignKey("pildora.id", ondelete="CASCADE"), primary_key=True
    )
    question_index: Mapped[int] = mapped_column("pregunta_idx", SmallInteger, primary_key=True)
    correct: Mapped[bool] = mapped_column("correcta", Boolean)
    created_at: Mapped[datetime] = _created_at()


class Message(Base):
    __tablename__ = "mensaje"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = _user_fk()
    role: Mapped[str] = mapped_column("rol", String(20))
    content: Mapped[str] = mapped_column("contenido", Text)
    trace_id: Mapped[str | None] = mapped_column("traza_id", String(64))
    created_at: Mapped[datetime] = _created_at()
