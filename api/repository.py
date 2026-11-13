"""Data access: queries and writes on the relational schema.

Functions never commit; the endpoint that owns the request does.
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from api.db import models
from engine.models import Goal, PlanResult, Profile


def lock_user(session: Session, user_id: uuid.UUID) -> None:
    """Take a row lock on the user so concurrent writes for them run one at a time."""
    session.execute(select(models.User.id).where(models.User.id == user_id).with_for_update())


def get_profile(session: Session, user_id: uuid.UUID) -> models.Profile | None:
    return session.get(models.Profile, user_id)


def upsert_profile(session: Session, user_id: uuid.UUID, profile: Profile) -> models.Profile:
    values = {**profile.model_dump(), "risk_profile": profile.risk_profile.value}
    row = session.get(models.Profile, user_id)
    if row is None:
        row = models.Profile(user_id=user_id, **values)
        session.add(row)
    else:
        for field, value in values.items():
            setattr(row, field, value)
    session.flush()
    session.refresh(row)
    return row


def list_goals(session: Session, user_id: uuid.UUID) -> list[models.Goal]:
    query = (
        select(models.Goal)
        .where(models.Goal.user_id == user_id)
        .order_by(models.Goal.priority, models.Goal.term_months, models.Goal.name, models.Goal.id)
    )
    return list(session.scalars(query))


def add_goal(session: Session, user_id: uuid.UUID, goal: Goal) -> models.Goal:
    row = models.Goal(user_id=user_id, **goal.model_dump())
    session.add(row)
    session.flush()
    session.refresh(row)
    return row


def delete_goal(session: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> bool:
    """Delete one goal of the user. Returns False if it does not exist."""
    result = session.execute(
        delete(models.Goal).where(models.Goal.id == goal_id, models.Goal.user_id == user_id)
    )
    return result.rowcount > 0


def save_plan(session: Session, user_id: uuid.UUID, result: PlanResult) -> models.Plan:
    row = models.Plan(
        user_id=user_id,
        parameters_version=result.parameters_version,
        result=result.model_dump(mode="json"),
    )
    session.add(row)
    session.flush()
    session.refresh(row)
    return row


def to_engine_profile(row: models.Profile) -> Profile:
    return Profile(
        monthly_income=row.monthly_income,
        monthly_expenses=row.monthly_expenses,
        monthly_debt_payment=row.monthly_debt_payment,
        current_savings=row.current_savings,
        dependents=row.dependents,
        risk_profile=row.risk_profile,
    )


def to_engine_goal(row: models.Goal) -> Goal:
    return Goal(
        name=row.name, amount=row.amount, term_months=row.term_months, priority=row.priority
    )
