"""Entry point of the planning engine: builds the whole plan (docs/SPEC.md 3.3)."""

from decimal import Decimal

from engine.allocation import allocate
from engine.distribution import distribute_contributions
from engine.emergency_fund import compute_emergency_fund
from engine.models import ContributionTranche, GoalPlan, PlanInput, PlanResult
from engine.parameters import Parameters
from engine.projection import project_goal
from engine.savings import compute_savings_capacity


def to_tranches(monthly_contributions: list[Decimal]) -> list[ContributionTranche]:
    """Group consecutive months with the same contribution."""
    tranches: list[ContributionTranche] = []
    for month, amount in enumerate(monthly_contributions, start=1):
        if tranches and tranches[-1].monthly_amount == amount:
            tranches[-1] = tranches[-1].model_copy(update={"to_month": month})
        else:
            tranches.append(
                ContributionTranche(from_month=month, to_month=month, monthly_amount=amount)
            )
    return tranches


def build_plan(plan_input: PlanInput, params: Parameters) -> PlanResult:
    """Compute the plan. Pure function: same input and parameters, same result."""
    profile = plan_input.profile
    capacity = compute_savings_capacity(profile)
    fund = compute_emergency_fund(profile, capacity, params.emergency_fund)

    goal_plans = []
    for funding in distribute_contributions(plan_input.goals, capacity, fund):
        goal = funding.goal
        allocation = allocate(goal.term_months, profile.risk_profile, params.allocation)
        goal_plans.append(
            GoalPlan(
                name=goal.name,
                amount=goal.amount,
                term_months=goal.term_months,
                priority=goal.priority,
                initial_capital=funding.initial_capital,
                monthly_contributions=funding.monthly_contributions,
                contribution_tranches=to_tranches(funding.monthly_contributions),
                total_contributions=funding.total_contributions,
                feasible=funding.feasible,
                shortfall=funding.shortfall,
                allocation=allocation,
                projections=project_goal(funding, allocation, params.annual_returns),
            )
        )

    return PlanResult(
        parameters_version=params.version,
        savings_capacity=capacity,
        emergency_fund=fund,
        goals=goal_plans,
    )
