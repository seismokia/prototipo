"""Input and output models of the planning engine.

Identifiers are in English; domain values (risk profiles, asset classes,
scenarios) keep the Spanish names fixed by docs/SPEC.md.
"""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# Domain limits fixed by docs/SPEC.md section 3.2 (not tunable parameters).
MAX_GOALS = 3
MAX_TERM_MONTHS = 60
MIN_PRIORITY = 1
MAX_PRIORITY = 3

NonNegativeMoney = Annotated[Decimal, Field(ge=0)]
PositiveMoney = Annotated[Decimal, Field(gt=0)]


class RiskProfile(StrEnum):
    CONSERVADOR = "conservador"
    MODERADO = "moderado"
    DINAMICO = "dinamico"


class AssetClass(StrEnum):
    LIQUIDEZ = "liquidez"
    MONETARIO = "monetario"
    RENTA_FIJA_CORTO = "renta_fija_corto"
    RENTA_FIJA_MEDIO = "renta_fija_medio"
    RENTA_VARIABLE_GLOBAL = "renta_variable_global"


class Scenario(StrEnum):
    PESIMISTA = "pesimista"
    CENTRAL = "central"
    OPTIMISTA = "optimista"


class EngineModel(BaseModel):
    """Base class: immutable models that reject unknown fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")


# --- Inputs -----------------------------------------------------------------


class Profile(EngineModel):
    monthly_income: NonNegativeMoney
    monthly_expenses: NonNegativeMoney
    monthly_debt_payment: NonNegativeMoney = Decimal("0")
    current_savings: NonNegativeMoney = Decimal("0")
    dependents: int = Field(default=0, ge=0)
    risk_profile: RiskProfile


class Goal(EngineModel):
    name: str = Field(min_length=1)
    amount: PositiveMoney
    term_months: int = Field(ge=1, le=MAX_TERM_MONTHS)
    priority: int = Field(ge=MIN_PRIORITY, le=MAX_PRIORITY)


class PlanInput(EngineModel):
    profile: Profile
    goals: list[Goal] = Field(default_factory=list, max_length=MAX_GOALS)


# --- Outputs ----------------------------------------------------------------


class SavingsCapacity(EngineModel):
    """Monthly income minus expenses and debt payments. May be negative."""

    amount: Decimal
    is_positive: bool


class EmergencyFund(EngineModel):
    target_months: int
    target_amount: Decimal
    covered_amount: Decimal
    shortfall: Decimal
    # Savings above the target, available as initial capital for the goals.
    surplus_savings: Decimal
    monthly_contribution: Decimal
    # 0 if already complete; None if it cannot be completed (no capacity).
    months_to_complete: int | None


class ContributionTranche(EngineModel):
    """A run of consecutive months (1-based, inclusive) with the same contribution."""

    from_month: int
    to_month: int
    monthly_amount: Decimal


class GoalFunding(EngineModel):
    """Money assigned to one goal, before any investment return."""

    goal: Goal
    initial_capital: Decimal
    # One entry per month of the goal's term.
    monthly_contributions: list[Decimal]
    total_contributions: Decimal
    # True if initial capital plus contributions reach the amount without returns.
    feasible: bool
    shortfall: Decimal


class Allocation(EngineModel):
    """Percentage per asset class (sums to 100)."""

    weights: dict[AssetClass, Decimal]


class ScenarioProjection(EngineModel):
    scenario: Scenario
    # Balance at the end of each month; index 0 is the initial capital.
    balances: list[Decimal]
    final_balance: Decimal
    goal_reached: bool


class GoalPlan(EngineModel):
    name: str
    amount: Decimal
    term_months: int
    priority: int
    initial_capital: Decimal
    monthly_contributions: list[Decimal]
    contribution_tranches: list[ContributionTranche]
    total_contributions: Decimal
    feasible: bool
    shortfall: Decimal
    allocation: Allocation
    projections: list[ScenarioProjection]


class PlanResult(EngineModel):
    parameters_version: str
    savings_capacity: SavingsCapacity
    emergency_fund: EmergencyFund
    # Ordered by funding order: priority, then shorter term.
    goals: list[GoalPlan]
