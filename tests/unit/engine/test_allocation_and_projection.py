from decimal import Decimal

import pytest

from engine.allocation import allocate
from engine.models import Allocation, AssetClass, GoalFunding, RiskProfile, Scenario
from engine.parameters import Parameters
from engine.projection import monthly_portfolio_return, project_goal

from .conftest import make_goal


@pytest.mark.parametrize(
    ("term", "risk_profile", "expected"),
    [
        (1, RiskProfile.CONSERVADOR, {AssetClass.LIQUIDEZ: 100}),
        (12, RiskProfile.MODERADO, {AssetClass.LIQUIDEZ: 50, AssetClass.MONETARIO: 50}),
        (13, RiskProfile.CONSERVADOR, {AssetClass.MONETARIO: 100}),
        (60, RiskProfile.DINAMICO, {AssetClass.RENTA_VARIABLE_GLOBAL: 100}),
    ],
)
def test_allocation_follows_term_band_and_risk_profile(
    params: Parameters, term: int, risk_profile: RiskProfile, expected: dict[AssetClass, int]
) -> None:
    allocation = allocate(term, risk_profile, params.allocation)

    non_zero = {asset: weight for asset, weight in allocation.weights.items() if weight}
    assert non_zero == expected
    assert sum(allocation.weights.values()) == Decimal(100)


def test_term_beyond_the_table_is_an_error(params: Parameters) -> None:
    with pytest.raises(ValueError, match="61"):
        allocate(61, RiskProfile.MODERADO, params.allocation)


def _funding(amount: str, initial: str, contributions: list[str]) -> GoalFunding:
    monthly = [Decimal(value) for value in contributions]
    return GoalFunding(
        goal=make_goal(amount, max(len(monthly), 1)),
        initial_capital=Decimal(initial),
        monthly_contributions=monthly,
        total_contributions=sum(monthly, Decimal(0)),
        feasible=True,
        shortfall=Decimal(0),
    )


def _single_asset(asset_class: AssetClass) -> Allocation:
    return Allocation(weights={asset_class: Decimal(100)})


def _returns(asset_class: AssetClass, pesimista: str, central: str, optimista: str):
    return {
        Scenario.PESIMISTA: {asset_class: Decimal(pesimista)},
        Scenario.CENTRAL: {asset_class: Decimal(central)},
        Scenario.OPTIMISTA: {asset_class: Decimal(optimista)},
    }


def test_monthly_return_compounds_to_the_annual_return() -> None:
    allocation = _single_asset(AssetClass.MONETARIO)

    monthly = monthly_portfolio_return(allocation, {AssetClass.MONETARIO: Decimal("0.05")})

    assert (1 + monthly) ** 12 == pytest.approx(Decimal("1.05"))


def test_monthly_return_is_weighted_by_the_allocation() -> None:
    allocation = Allocation(
        weights={AssetClass.LIQUIDEZ: Decimal(50), AssetClass.MONETARIO: Decimal(50)}
    )
    returns = {AssetClass.LIQUIDEZ: Decimal(0), AssetClass.MONETARIO: Decimal("0.05")}

    only_monetario = monthly_portfolio_return(_single_asset(AssetClass.MONETARIO), returns)

    assert monthly_portfolio_return(allocation, returns) == pytest.approx(only_monetario / 2)


def test_projection_has_three_scenarios_and_one_balance_per_month() -> None:
    funding = _funding("1200", "0", ["100"] * 12)
    asset = AssetClass.MONETARIO

    projections = project_goal(funding, _single_asset(asset), _returns(asset, "-0.05", "0", "0.05"))

    assert [projection.scenario for projection in projections] == list(Scenario)
    for projection in projections:
        assert len(projection.balances) == 13
        assert projection.balances[0] == 0
        assert projection.final_balance == projection.balances[-1]


def test_zero_return_projection_is_the_sum_of_contributions() -> None:
    funding = _funding("1200", "0", ["100"] * 12)
    asset = AssetClass.LIQUIDEZ

    _, central, _ = project_goal(funding, _single_asset(asset), _returns(asset, "0", "0", "0"))

    assert central.balances == [Decimal(100 * month) for month in range(13)]
    assert central.goal_reached


def test_initial_capital_grows_with_the_annual_return() -> None:
    funding = _funding("1050", "1000", ["0"] * 12)
    asset = AssetClass.MONETARIO

    pessimistic, central, optimistic = project_goal(
        funding, _single_asset(asset), _returns(asset, "-0.05", "0", "0.05")
    )

    assert pessimistic.final_balance == Decimal("950.00")
    assert central.final_balance == Decimal("1000.00")
    assert optimistic.final_balance == Decimal("1050.00")
    assert [p.goal_reached for p in (pessimistic, central, optimistic)] == [False, False, True]


def test_scenarios_are_ordered_when_returns_are() -> None:
    funding = _funding("6000", "500", ["100"] * 60)
    asset = AssetClass.RENTA_VARIABLE_GLOBAL

    pessimistic, central, optimistic = project_goal(
        funding, _single_asset(asset), _returns(asset, "-0.10", "0.05", "0.09")
    )

    assert pessimistic.final_balance < central.final_balance < optimistic.final_balance
