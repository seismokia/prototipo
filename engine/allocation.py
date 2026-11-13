"""Asset-class allocation by goal term and risk profile (docs/SPEC.md 3.3)."""

from engine.models import Allocation, RiskProfile
from engine.parameters import AllocationParameters


def allocate(
    term_months: int, risk_profile: RiskProfile, params: AllocationParameters
) -> Allocation:
    """Look up the allocation table: first band whose maximum term covers the goal."""
    for band in params.bands:
        if term_months <= band.max_term_months:
            return Allocation(weights=dict(band.profiles[risk_profile]))
    raise ValueError(f"No allocation band covers a term of {term_months} months")
