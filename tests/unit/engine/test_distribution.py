from decimal import Decimal

from engine.distribution import distribute_contributions, funding_order
from engine.emergency_fund import compute_emergency_fund
from engine.models import Goal, GoalFunding
from engine.parameters import Parameters
from engine.savings import compute_savings_capacity

from .conftest import make_goal, make_profile


def _distribute(params: Parameters, goals: list[Goal], **profile_overrides) -> list[GoalFunding]:
    profile = make_profile(**profile_overrides)
    capacity = compute_savings_capacity(profile)
    fund = compute_emergency_fund(profile, capacity, params.emergency_fund)
    return distribute_contributions(goals, capacity, fund)


def test_no_goals_gives_no_funding(params: Parameters) -> None:
    assert _distribute(params, []) == []


def test_feasible_goal_gets_amount_divided_by_term(params: Parameters) -> None:
    [funding] = _distribute(params, [make_goal("12000", 60)])

    assert funding.monthly_contributions == [Decimal("200.00")] * 60
    assert funding.total_contributions == Decimal("12000.00")
    assert funding.feasible
    assert funding.shortfall == 0


def test_rounding_never_loses_or_creates_cents(params: Parameters) -> None:
    [funding] = _distribute(params, [make_goal("1000", 3)])

    assert funding.monthly_contributions == [
        Decimal("333.34"),
        Decimal("333.34"),
        Decimal("333.32"),
    ]
    assert funding.total_contributions == Decimal("1000.00")
    assert funding.feasible


def test_infeasible_goal_gets_what_is_available(params: Parameters) -> None:
    [funding] = _distribute(params, [make_goal("60000", 12)])

    assert funding.monthly_contributions == [Decimal("800.00")] * 12
    assert not funding.feasible
    assert funding.shortfall == Decimal("50400.00")


def test_negative_capacity_gives_zero_contributions(params: Parameters) -> None:
    [funding] = _distribute(params, [make_goal("1000", 12)], monthly_income=Decimal("1000"))

    assert funding.monthly_contributions == [Decimal("0.00")] * 12
    assert funding.total_contributions == 0
    assert not funding.feasible
    assert funding.shortfall == Decimal("1000.00")


def test_higher_priority_is_served_first(params: Parameters) -> None:
    low = make_goal("6000", 12, priority=2, name="low")
    high = make_goal("6000", 12, priority=1, name="high")

    first, second = _distribute(params, [low, high])

    assert first.goal.name == "high"
    assert first.monthly_contributions == [Decimal("500.00")] * 12
    assert first.feasible
    assert second.monthly_contributions == [Decimal("300.00")] * 12
    assert not second.feasible
    assert second.shortfall == Decimal("2400.00")


def test_priority_ties_go_to_the_shorter_term() -> None:
    long = make_goal("1000", 24, priority=1, name="long")
    short = make_goal("1000", 12, priority=1, name="short")
    other = make_goal("1000", 6, priority=2, name="other")

    assert [goal.name for goal in funding_order([long, other, short])] == [
        "short",
        "long",
        "other",
    ]


def test_lower_priority_catches_up_when_money_is_released(params: Parameters) -> None:
    high = make_goal("6000", 12, priority=1, name="high")
    low = make_goal("12000", 24, priority=2, name="low")

    _, funding = _distribute(params, [high, low])

    assert funding.monthly_contributions == [Decimal("300.00")] * 12 + [Decimal("700.00")] * 12
    assert funding.feasible


def test_emergency_fund_is_funded_before_goals(params: Parameters) -> None:
    # Fund shortfall of 2000 takes 400/month during 5 months; the goal gets the
    # other 400 and catches up afterwards.
    [funding] = _distribute(params, [make_goal("12000", 24)], current_savings=Decimal("4000"))

    assert funding.monthly_contributions[:5] == [Decimal("400.00")] * 5
    assert funding.monthly_contributions[5:23] == [Decimal("526.32")] * 18
    assert funding.monthly_contributions[23] == Decimal("526.24")
    assert funding.total_contributions == Decimal("12000.00")
    assert funding.feasible


def test_surplus_savings_become_initial_capital_by_priority(params: Parameters) -> None:
    second = make_goal("3000", 12, priority=2, name="second")
    first = make_goal("1500", 12, priority=1, name="first")

    covered, partial = _distribute(params, [second, first], current_savings=Decimal("8000"))

    assert covered.initial_capital == Decimal("1500.00")
    assert covered.total_contributions == 0
    assert covered.feasible
    assert partial.initial_capital == Decimal("500.00")
    assert partial.total_contributions == Decimal("2500.00")
    assert partial.feasible


def test_contributions_never_exceed_the_capacity(params: Parameters) -> None:
    goals = [make_goal("20000", 60, 1), make_goal("9000", 18, 2), make_goal("7000", 36, 3)]

    fundings = _distribute(params, goals, current_savings=Decimal("1000"))

    for month in range(60):
        total = sum(
            funding.monthly_contributions[month]
            for funding in fundings
            if month < len(funding.monthly_contributions)
        )
        assert total <= Decimal("800.00")
