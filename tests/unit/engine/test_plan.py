import ast
from decimal import Decimal
from pathlib import Path

import engine
from engine import PlanInput, PlanResult, build_plan, load_parameters
from engine.models import ContributionTranche, Scenario
from engine.parameters import Parameters
from engine.plan import to_tranches

from .conftest import make_goal, make_profile


def _plan(params: Parameters, goals: list, **profile_overrides) -> PlanResult:
    return build_plan(PlanInput(profile=make_profile(**profile_overrides), goals=goals), params)


def _reached(plan: PlanResult, index: int = 0) -> dict[Scenario, bool]:
    return {p.scenario: p.goal_reached for p in plan.goals[index].projections}


def test_plan_for_a_feasible_goal(params: Parameters) -> None:
    plan = _plan(params, [make_goal("12000", 60)])

    assert plan.parameters_version == "test"
    assert plan.savings_capacity.amount == Decimal("800.00")
    assert plan.emergency_fund.shortfall == 0
    [goal] = plan.goals
    assert goal.feasible
    assert goal.contribution_tranches == [
        ContributionTranche(from_month=1, to_month=60, monthly_amount=Decimal("200.00"))
    ]
    assert sum(goal.allocation.weights.values()) == Decimal(100)
    assert all(len(p.balances) == 61 for p in goal.projections)
    # Contributions ignore returns, so only non-negative scenarios reach the amount.
    assert _reached(plan) == {
        Scenario.PESIMISTA: False,
        Scenario.CENTRAL: True,
        Scenario.OPTIMISTA: True,
    }


def test_plan_with_negative_savings_capacity(params: Parameters) -> None:
    plan = _plan(
        params,
        [make_goal("3000", 12)],
        monthly_income=Decimal("1000"),
        current_savings=Decimal("0"),
    )

    assert plan.savings_capacity.amount == Decimal("-700.00")
    assert not plan.savings_capacity.is_positive
    assert plan.emergency_fund.months_to_complete is None
    [goal] = plan.goals
    assert goal.total_contributions == 0
    assert not goal.feasible
    assert goal.shortfall == Decimal("3000.00")
    assert not any(_reached(plan).values())
    assert all(p.final_balance == 0 for p in goal.projections)


def test_plan_with_an_infeasible_goal(params: Parameters) -> None:
    plan = _plan(params, [make_goal("60000", 12)])

    [goal] = plan.goals
    assert not goal.feasible
    assert goal.shortfall == Decimal("50400.00")
    assert not any(_reached(plan).values())


def test_infeasible_goal_does_not_block_a_higher_priority_one(params: Parameters) -> None:
    plan = _plan(
        params,
        [make_goal("60000", 12, priority=2, name="car"), make_goal("2400", 12, name="trip")],
    )

    assert [(goal.name, goal.feasible) for goal in plan.goals] == [("trip", True), ("car", False)]


def test_plan_without_goals(params: Parameters) -> None:
    plan = _plan(params, [])

    assert plan.goals == []
    assert plan.emergency_fund.target_amount == Decimal("6000.00")


def test_plan_is_deterministic_and_does_not_mutate_its_input(params: Parameters) -> None:
    plan_input = PlanInput(profile=make_profile(), goals=[make_goal("5000", 30)])
    snapshot = plan_input.model_dump()

    assert build_plan(plan_input, params) == build_plan(plan_input, params)
    assert plan_input.model_dump() == snapshot


def test_plan_serializes_to_json(params: Parameters) -> None:
    plan = _plan(params, [make_goal("5000", 30)])

    assert PlanResult.model_validate_json(plan.model_dump_json()) == plan


def test_plan_with_the_default_parameters_file() -> None:
    plan = _plan(load_parameters(), [make_goal("12000", 60), make_goal("3000", 12, priority=2)])

    assert len(plan.goals) == 2
    assert all(goal.feasible for goal in plan.goals)


def test_to_tranches_groups_equal_consecutive_months() -> None:
    amounts = [Decimal("400")] * 2 + [Decimal("500")] * 3 + [Decimal("400")]

    assert to_tranches(amounts) == [
        ContributionTranche(from_month=1, to_month=2, monthly_amount=Decimal("400")),
        ContributionTranche(from_month=3, to_month=5, monthly_amount=Decimal("500")),
        ContributionTranche(from_month=6, to_month=6, monthly_amount=Decimal("400")),
    ]
    assert to_tranches([]) == []


def test_engine_does_not_import_other_layers() -> None:
    forbidden = {"llm", "rag", "api", "sqlalchemy", "fastapi"}
    engine_dir = Path(engine.__file__).parent

    for path in engine_dir.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                assert module.split(".")[0] not in forbidden, f"{path.name} imports {module}"
