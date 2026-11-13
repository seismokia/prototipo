from decimal import Decimal

from engine.emergency_fund import compute_emergency_fund
from engine.models import EmergencyFund, RiskProfile
from engine.parameters import Parameters
from engine.savings import compute_savings_capacity

from .conftest import make_profile


def test_savings_capacity_is_income_minus_expenses_and_debt() -> None:
    capacity = compute_savings_capacity(make_profile())

    assert capacity.amount == Decimal("800.00")
    assert capacity.is_positive


def test_savings_capacity_can_be_negative() -> None:
    capacity = compute_savings_capacity(make_profile(monthly_income=Decimal("1000")))

    assert capacity.amount == Decimal("-700.00")
    assert not capacity.is_positive


def test_zero_savings_capacity_is_not_positive() -> None:
    capacity = compute_savings_capacity(make_profile(monthly_income=Decimal("1700")))

    assert capacity.amount == Decimal("0.00")
    assert not capacity.is_positive


def _fund(params: Parameters, **profile_overrides) -> EmergencyFund:
    profile = make_profile(**profile_overrides)
    return compute_emergency_fund(profile, compute_savings_capacity(profile), params.emergency_fund)


def test_fund_target_depends_on_risk_profile(params: Parameters) -> None:
    targets = {}
    for risk_profile in RiskProfile:
        fund = _fund(params, risk_profile=risk_profile)
        targets[risk_profile] = (fund.target_months, fund.target_amount)

    assert targets == {
        RiskProfile.CONSERVADOR: (6, Decimal("9000.00")),
        RiskProfile.MODERADO: (4, Decimal("6000.00")),
        RiskProfile.DINAMICO: (3, Decimal("4500.00")),
    }


def test_fund_already_covered(params: Parameters) -> None:
    fund = _fund(params, current_savings=Decimal("6000"))

    assert fund.covered_amount == Decimal("6000.00")
    assert fund.shortfall == 0
    assert fund.surplus_savings == 0
    assert fund.monthly_contribution == 0
    assert fund.months_to_complete == 0


def test_savings_above_the_target_are_surplus(params: Parameters) -> None:
    fund = _fund(params, current_savings=Decimal("8000"))

    assert fund.covered_amount == Decimal("6000.00")
    assert fund.surplus_savings == Decimal("2000.00")


def test_shortfall_takes_a_fraction_of_the_capacity(params: Parameters) -> None:
    fund = _fund(params, current_savings=Decimal("4000"))

    assert fund.shortfall == Decimal("2000.00")
    assert fund.monthly_contribution == Decimal("400.00")
    assert fund.months_to_complete == 5


def test_months_to_complete_rounds_up(params: Parameters) -> None:
    fund = _fund(params, current_savings=Decimal("3900"))

    assert fund.months_to_complete == 6


def test_contribution_never_exceeds_the_shortfall(params: Parameters) -> None:
    fund = _fund(params, current_savings=Decimal("5900"))

    assert fund.monthly_contribution == Decimal("100.00")
    assert fund.months_to_complete == 1


def test_fund_cannot_be_completed_without_capacity(params: Parameters) -> None:
    fund = _fund(params, current_savings=Decimal("0"), monthly_income=Decimal("1000"))

    assert fund.shortfall == Decimal("6000.00")
    assert fund.monthly_contribution == 0
    assert fund.months_to_complete is None
