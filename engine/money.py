"""Monetary rounding shared by the engine."""

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def to_cents(value: Decimal) -> Decimal:
    """Round to two decimal places, half up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def ceil_to_cents(value: Decimal) -> Decimal:
    """Round up to two decimal places."""
    return value.quantize(CENT, rounding=ROUND_CEILING)
