"""Distribution of the monthly contribution among goals by priority (docs/SPEC.md 3.3)."""

from decimal import Decimal

from engine.models import EmergencyFund, Goal, GoalFunding, SavingsCapacity
from engine.money import ZERO, ceil_to_cents, to_cents


def funding_order(goals: list[Goal]) -> list[Goal]:
    """Priority first (1 is highest); ties go to the shorter term, then input order."""
    return sorted(goals, key=lambda goal: (goal.priority, goal.term_months))


def distribute_contributions(
    goals: list[Goal], capacity: SavingsCapacity, fund: EmergencyFund
) -> list[GoalFunding]:
    """Assign initial capital and monthly contributions to each goal.

    Strict cascade, month by month: after the emergency fund takes its part,
    each goal in funding order asks for a level instalment (what it still needs
    divided by the months it has left, returns not counted, rounded up to the
    cent) and receives it up to the money still available. The instalment is
    kept while it is paid in full; after a short month it is recomputed, so the
    goal catches up as soon as money is released. The last payment absorbs the
    rounding.

    Returns one entry per goal, in funding order.
    """
    ordered = funding_order(goals)
    if not ordered:
        return []

    surplus = fund.surplus_savings
    initial_capital: list[Decimal] = []
    for goal in ordered:
        capital = min(to_cents(goal.amount), surplus)
        surplus -= capital
        initial_capital.append(capital)

    monthly_capacity = max(capacity.amount, ZERO)
    fund_pending = fund.shortfall
    contributed = [ZERO for _ in ordered]
    schedules: list[list[Decimal]] = [[] for _ in ordered]
    # Current instalment of each goal; None means "compute it this month".
    rates: list[Decimal | None] = [None for _ in ordered]

    for month in range(1, max(goal.term_months for goal in ordered) + 1):
        fund_payment = min(fund.monthly_contribution, fund_pending, monthly_capacity)
        fund_pending -= fund_payment
        available = monthly_capacity - fund_payment

        for index, goal in enumerate(ordered):
            if month > goal.term_months:
                continue
            pending = to_cents(goal.amount) - initial_capital[index] - contributed[index]
            if rates[index] is None:
                months_left = goal.term_months - month + 1
                rates[index] = ceil_to_cents(pending / months_left)
            request = min(rates[index], pending)
            payment = min(request, available)
            if payment < request:
                # Short this month: recompute the instalment with what is left.
                rates[index] = None
            available -= payment
            contributed[index] += payment
            schedules[index].append(payment)

    result = []
    for index, goal in enumerate(ordered):
        shortfall = to_cents(goal.amount) - initial_capital[index] - contributed[index]
        result.append(
            GoalFunding(
                goal=goal,
                initial_capital=initial_capital[index],
                monthly_contributions=schedules[index],
                total_contributions=contributed[index],
                feasible=shortfall == 0,
                shortfall=shortfall,
            )
        )
    return result
