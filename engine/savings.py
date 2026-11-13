"""Savings capacity (docs/SPEC.md 3.3)."""

from engine.models import Profile, SavingsCapacity
from engine.money import to_cents


def compute_savings_capacity(profile: Profile) -> SavingsCapacity:
    """Monthly income minus expenses and debt payments. Negative means a monthly deficit."""
    amount = to_cents(
        profile.monthly_income - profile.monthly_expenses - profile.monthly_debt_payment
    )
    return SavingsCapacity(amount=amount, is_positive=amount > 0)
