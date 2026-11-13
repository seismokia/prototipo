"""Emergency fund (docs/SPEC.md 3.3)."""

from decimal import ROUND_CEILING

from engine.models import EmergencyFund, Profile, SavingsCapacity
from engine.money import ZERO, to_cents
from engine.parameters import EmergencyFundParameters


def compute_emergency_fund(
    profile: Profile, capacity: SavingsCapacity, params: EmergencyFundParameters
) -> EmergencyFund:
    """Size the fund and decide how it is completed.

    The target is N months of expenses (N depends on the risk profile). Current
    savings cover it first; savings above the target are surplus. While there is
    a shortfall, a fixed fraction of the savings capacity goes to the fund.
    """
    target_months = params.months_by_profile[profile.risk_profile]
    target = to_cents(profile.monthly_expenses * target_months)
    savings = to_cents(profile.current_savings)
    covered = min(savings, target)
    shortfall = target - covered

    monthly = ZERO
    if shortfall > 0 and capacity.is_positive:
        monthly = min(shortfall, to_cents(capacity.amount * params.savings_capacity_fraction))

    months_to_complete: int | None
    if shortfall == 0:
        months_to_complete = 0
    elif monthly == 0:
        months_to_complete = None
    else:
        months_to_complete = int((shortfall / monthly).to_integral_value(rounding=ROUND_CEILING))

    return EmergencyFund(
        target_months=target_months,
        target_amount=target,
        covered_amount=covered,
        shortfall=shortfall,
        surplus_savings=savings - covered,
        monthly_contribution=monthly,
        months_to_complete=months_to_complete,
    )
