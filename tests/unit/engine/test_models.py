from decimal import Decimal

import pytest
from pydantic import ValidationError

from engine.models import PlanInput

from .conftest import make_goal, make_profile


def test_term_of_60_months_is_accepted() -> None:
    assert make_goal("1000", 60).term_months == 60


@pytest.mark.parametrize("term", [0, 61])
def test_term_outside_limits_is_rejected(term: int) -> None:
    with pytest.raises(ValidationError):
        make_goal("1000", term)


@pytest.mark.parametrize("priority", [0, 4])
def test_priority_outside_limits_is_rejected(priority: int) -> None:
    with pytest.raises(ValidationError):
        make_goal("1000", 12, priority=priority)


@pytest.mark.parametrize("amount", ["0", "-1"])
def test_goal_amount_must_be_positive(amount: str) -> None:
    with pytest.raises(ValidationError):
        make_goal(amount, 12)


def test_more_than_three_goals_are_rejected() -> None:
    goals = [make_goal("1000", 12) for _ in range(4)]
    with pytest.raises(ValidationError):
        PlanInput(profile=make_profile(), goals=goals)


def test_negative_profile_amounts_are_rejected() -> None:
    with pytest.raises(ValidationError):
        make_profile(monthly_income=Decimal("-1"))


def test_unknown_risk_profile_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_profile(risk_profile="temerario")
