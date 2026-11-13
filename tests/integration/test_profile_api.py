from typing import Any

from fastapi.testclient import TestClient

PROFILE: dict[str, Any] = {
    "monthly_income": "2500.00",
    "monthly_expenses": "1500.00",
    "monthly_debt_payment": "200.00",
    "current_savings": "6000.00",
    "dependents": 1,
    "risk_profile": "moderado",
}


def test_profile_does_not_exist_at_first(client: TestClient) -> None:
    response = client.get("/perfil")

    assert response.status_code == 404
    assert "ficha de perfil" in response.json()["detail"]


def test_put_creates_the_profile_and_get_returns_it(client: TestClient) -> None:
    created = client.put("/perfil", json=PROFILE)
    fetched = client.get("/perfil")

    assert created.status_code == 200
    assert fetched.status_code == 200
    assert fetched.json() == created.json()
    body = fetched.json()
    assert body.pop("updated_at")
    assert body == PROFILE


def test_put_replaces_the_whole_profile(client: TestClient) -> None:
    client.put("/perfil", json=PROFILE)

    # Numbers are accepted on input; optional fields fall back to their defaults.
    replaced = client.put(
        "/perfil",
        json={"monthly_income": 3000, "monthly_expenses": 1800.5, "risk_profile": "dinamico"},
    )

    assert replaced.status_code == 200
    body = client.get("/perfil").json()
    assert body["monthly_income"] == "3000.00"
    assert body["monthly_expenses"] == "1800.50"
    assert body["monthly_debt_payment"] == "0.00"
    assert body["current_savings"] == "0.00"
    assert body["dependents"] == 0
    assert body["risk_profile"] == "dinamico"


def test_put_rejects_invalid_profiles(client: TestClient) -> None:
    invalid_bodies = [
        {**PROFILE, "monthly_income": "-1"},
        {**PROFILE, "risk_profile": "temerario"},
        {**PROFILE, "monthly_expenses": "10.123"},
        {**PROFILE, "current_savings": "99999999999.00"},
        {**PROFILE, "unknown_field": 1},
        {key: value for key, value in PROFILE.items() if key != "risk_profile"},
    ]

    for body in invalid_bodies:
        assert client.put("/perfil", json=body).status_code == 422, body
    assert client.get("/perfil").status_code == 404
