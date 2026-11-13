"""Profile -> goals -> plan through the API, with synthetic data.

Figures come from the fixed test parameters (tests/unit/engine/conftest.py):
capacity 2500 - 1500 - 200 = 800/month; emergency fund 4 x 1500 = 6000, fully
covered by the 6000 of current savings.
"""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from engine import PlanInput, build_plan
from engine.parameters import Parameters

PROFILE: dict[str, Any] = {
    "monthly_income": "2500.00",
    "monthly_expenses": "1500.00",
    "monthly_debt_payment": "200.00",
    "current_savings": "6000.00",
    "dependents": 0,
    "risk_profile": "moderado",
}
HOME = {"name": "Entrada del piso", "amount": "12000.00", "term_months": 60, "priority": 1}
CAR = {"name": "Coche", "amount": "7200.00", "term_months": 36, "priority": 2}


def _count_plans(session_factory: sessionmaker[Session]) -> int:
    with session_factory() as session:
        return session.scalar(text("SELECT count(*) FROM plan"))


def test_plan_requires_a_profile(client: TestClient) -> None:
    for path, body in (("/plan", None), ("/plan/simular", {})):
        response = client.post(path, json=body)

        assert response.status_code == 409, path
        assert "ficha de perfil" in response.json()["detail"]


def test_profile_goals_plan_flow(
    client: TestClient, params: Parameters, session_factory: sessionmaker[Session]
) -> None:
    assert client.put("/perfil", json=PROFILE).status_code == 200
    assert client.post("/objetivos", json=CAR).status_code == 201
    assert client.post("/objetivos", json=HOME).status_code == 201

    response = client.post("/plan")

    assert response.status_code == 201
    body = response.json()
    result = body["result"]
    assert result["parameters_version"] == "test"
    assert result["savings_capacity"] == {"amount": "800.00", "is_positive": True}
    assert result["emergency_fund"]["target_amount"] == "6000.00"
    assert result["emergency_fund"]["shortfall"] == "0.00"

    home, car = result["goals"]
    assert (home["name"], car["name"]) == ("Entrada del piso", "Coche")
    assert home["feasible"] and car["feasible"]
    assert home["contribution_tranches"] == [
        {"from_month": 1, "to_month": 60, "monthly_amount": "200.00"}
    ]
    assert car["contribution_tranches"] == [
        {"from_month": 1, "to_month": 36, "monthly_amount": "200.00"}
    ]
    assert [p["scenario"] for p in home["projections"]] == ["pesimista", "central", "optimista"]
    assert all(len(p["balances"]) == 61 for p in home["projections"])
    assert sum(float(weight) for weight in home["allocation"]["weights"].values()) == 100

    # The API returns exactly what the engine computes for the same input.
    plan_input = PlanInput.model_validate({"profile": PROFILE, "goals": [HOME, CAR]})
    expected = build_plan(plan_input, params)
    assert result == expected.model_dump(mode="json")

    # The plan is stored with its parameters version and the same result.
    with session_factory() as session:
        [stored] = session.execute(
            text("SELECT id, parametros_version, resultado_json FROM plan")
        ).all()
    assert str(stored.id) == body["id"]
    assert stored.parametros_version == "test"
    assert stored.resultado_json == result


def test_plan_without_goals_reports_capacity_and_emergency_fund(client: TestClient) -> None:
    client.put("/perfil", json={**PROFILE, "current_savings": "0"})

    result = client.post("/plan").json()["result"]

    assert result["goals"] == []
    assert result["emergency_fund"]["shortfall"] == "6000.00"
    assert result["emergency_fund"]["monthly_contribution"] == "400.00"
    assert result["emergency_fund"]["months_to_complete"] == 15


def test_plan_with_negative_savings_capacity_marks_goals_unfeasible(client: TestClient) -> None:
    client.put("/perfil", json={**PROFILE, "monthly_expenses": "2600.00"})
    client.post("/objetivos", json=HOME)

    result = client.post("/plan").json()["result"]

    assert result["savings_capacity"] == {"amount": "-300.00", "is_positive": False}
    [home] = result["goals"]
    assert not home["feasible"]


def test_each_plan_calculation_is_stored(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    client.put("/perfil", json=PROFILE)

    first = client.post("/plan").json()
    second = client.post("/plan").json()

    assert first["id"] != second["id"]
    assert first["result"] == second["result"]
    assert _count_plans(session_factory) == 2


def test_simulation_without_changes_matches_the_plan(client: TestClient) -> None:
    client.put("/perfil", json=PROFILE)
    client.post("/objetivos", json=HOME)

    simulation = client.post("/plan/simular", json={})

    assert simulation.status_code == 200
    assert simulation.json()["result"] == client.post("/plan").json()["result"]
    assert simulation.json()["input"] == {"profile": PROFILE, "goals": [HOME]}


def test_simulation_applies_profile_overrides_without_storing_anything(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    client.put("/perfil", json=PROFILE)
    client.post("/objetivos", json=HOME)

    response = client.post(
        "/plan/simular",
        json={"profile": {"monthly_income": "3000", "risk_profile": "dinamico"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["input"]["profile"]["monthly_income"] == "3000"
    assert body["input"]["profile"]["risk_profile"] == "dinamico"
    assert body["input"]["profile"]["monthly_expenses"] == "1500.00"
    assert body["result"]["savings_capacity"]["amount"] == "1300.00"
    # Dynamic profile, 60 months: everything in global equities with the test parameters.
    assert body["result"]["goals"][0]["allocation"]["weights"]["renta_variable_global"] == "100"

    # Stored data is untouched and no plan was saved.
    assert client.get("/perfil").json()["monthly_income"] == "2500.00"
    assert _count_plans(session_factory) == 0


def test_simulation_replaces_the_goals_for_that_run_only(client: TestClient) -> None:
    client.put("/perfil", json=PROFILE)
    stored_goal = client.post("/objetivos", json=HOME).json()

    response = client.post("/plan/simular", json={"goals": [CAR]})

    assert [g["name"] for g in response.json()["result"]["goals"]] == ["Coche"]
    assert client.get("/objetivos").json() == [stored_goal]


def test_simulation_rejects_invalid_requests(client: TestClient) -> None:
    client.put("/perfil", json=PROFILE)
    invalid_bodies = [
        {"profile": {"monthly_income": "-5"}},
        {"profile": {"risk_profile": "temerario"}},
        {"goals": [HOME, CAR, HOME, CAR]},
        {"goals": [{**HOME, "term_months": 61}]},
        {"parameters": {"version": "x"}},
    ]

    for body in invalid_bodies:
        assert client.post("/plan/simular", json=body).status_code == 422, body
