"""Projection of a goal's balance in three scenarios (docs/SPEC.md 3.3)."""

from decimal import Decimal

from engine.models import Allocation, AssetClass, GoalFunding, Scenario, ScenarioProjection
from engine.money import to_cents

_ONE = Decimal(1)
_MONTHS_PER_YEAR = Decimal(12)
_HUNDRED = Decimal(100)


def monthly_portfolio_return(
    allocation: Allocation, annual_returns: dict[AssetClass, Decimal]
) -> Decimal:
    """Weighted monthly return of the mix, from the annual return of each asset class."""
    total = Decimal(0)
    for asset_class, weight in allocation.weights.items():
        monthly = (_ONE + annual_returns[asset_class]) ** (_ONE / _MONTHS_PER_YEAR) - _ONE
        total += weight / _HUNDRED * monthly
    return total


def project_goal(
    funding: GoalFunding,
    allocation: Allocation,
    annual_returns: dict[Scenario, dict[AssetClass, Decimal]],
) -> list[ScenarioProjection]:
    """Project the balance month by month in each scenario.

    Monthly compounding, contributions at the end of each month, constant mix
    during the whole term. Nominal figures: no inflation, fees or taxes.
    """
    projections = []
    for scenario in Scenario:
        rate = monthly_portfolio_return(allocation, annual_returns[scenario])
        balance = funding.initial_capital
        balances = [to_cents(balance)]
        for contribution in funding.monthly_contributions:
            balance = balance * (_ONE + rate) + contribution
            balances.append(to_cents(balance))
        projections.append(
            ScenarioProjection(
                scenario=scenario,
                balances=balances,
                final_balance=balances[-1],
                goal_reached=balances[-1] >= funding.goal.amount,
            )
        )
    return projections
