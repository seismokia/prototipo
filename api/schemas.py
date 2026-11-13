"""Pydantic models exposed at the API boundary.

JSON field names are in English, the same as the engine models. Money amounts
are serialised as decimal strings ("1234.56"); inputs accept strings or numbers.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from engine.models import MAX_GOALS, Goal, PlanInput, PlanResult, Profile, RiskProfile

# Amounts that are stored: they must fit the NUMERIC(12, 2) columns.
StoredNonNegativeMoney = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
StoredPositiveMoney = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
# Fits the INTEGER column; far above any realistic value.
MAX_DEPENDENTS = 99


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str


# --- Profile ------------------------------------------------------------------


class ProfileBody(Profile):
    """Profile sheet sent with ``PUT /perfil``: the engine profile, storable."""

    monthly_income: StoredNonNegativeMoney
    monthly_expenses: StoredNonNegativeMoney
    monthly_debt_payment: StoredNonNegativeMoney = Decimal("0")
    current_savings: StoredNonNegativeMoney = Decimal("0")
    dependents: int = Field(default=0, ge=0, le=MAX_DEPENDENTS)


class ProfileResponse(ProfileBody):
    updated_at: datetime


# --- Goals --------------------------------------------------------------------


class GoalBody(Goal):
    """Goal sent with ``POST /objetivos``."""

    name: str = Field(min_length=1, max_length=100)
    amount: StoredPositiveMoney


class GoalResponse(GoalBody):
    id: uuid.UUID


# --- Plan ---------------------------------------------------------------------


class PlanResponse(ApiModel):
    id: uuid.UUID
    created_at: datetime
    result: PlanResult


class ProfileOverrides(ApiModel):
    """Profile fields to change in a simulation; the ones left out keep the stored value."""

    monthly_income: Annotated[Decimal, Field(ge=0)] | None = None
    monthly_expenses: Annotated[Decimal, Field(ge=0)] | None = None
    monthly_debt_payment: Annotated[Decimal, Field(ge=0)] | None = None
    current_savings: Annotated[Decimal, Field(ge=0)] | None = None
    dependents: Annotated[int, Field(ge=0)] | None = None
    risk_profile: RiskProfile | None = None


class SimulationRequest(ApiModel):
    profile: ProfileOverrides | None = None
    # When present, replaces the stored goals for this simulation only.
    goals: Annotated[list[Goal], Field(max_length=MAX_GOALS)] | None = None


class SimulationResponse(ApiModel):
    # The input actually used: stored data with the overrides applied.
    input: PlanInput
    result: PlanResult
