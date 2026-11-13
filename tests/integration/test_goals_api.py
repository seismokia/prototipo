import uuid
from typing import Any

from fastapi.testclient import TestClient


def goal(name: str = "Entrada del piso", **overrides: Any) -> dict[str, Any]:
    return {
        "name": name,
        "amount": "12000.00",
        "term_months": 60,
        "priority": 1,
        **overrides,
    }


def test_there_are_no_goals_at_first(client: TestClient) -> None:
    response = client.get("/objetivos")

    assert response.status_code == 200
    assert response.json() == []


def test_post_creates_a_goal(client: TestClient) -> None:
    response = client.post("/objetivos", json=goal())

    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body.pop("id"))
    assert body == goal()
    assert client.get("/objetivos").json() == [response.json()]


def test_amounts_are_returned_with_two_decimals(client: TestClient) -> None:
    response = client.post("/objetivos", json=goal(amount=12000))

    assert response.json()["amount"] == "12000.00"


def test_goals_are_listed_in_funding_order(client: TestClient) -> None:
    client.post("/objetivos", json=goal("Coche", priority=2, term_months=36))
    client.post("/objetivos", json=goal("Piso", priority=1, term_months=60))
    client.post("/objetivos", json=goal("Viaje", priority=1, term_months=12))

    names = [item["name"] for item in client.get("/objetivos").json()]

    assert names == ["Viaje", "Piso", "Coche"]


def test_a_fourth_goal_is_rejected(client: TestClient) -> None:
    for index in range(3):
        assert client.post("/objetivos", json=goal(f"Objetivo {index}")).status_code == 201

    response = client.post("/objetivos", json=goal("Uno más"))

    assert response.status_code == 409
    assert "máximo" in response.json()["detail"]
    assert len(client.get("/objetivos").json()) == 3


def test_delete_removes_a_goal_and_frees_its_slot(client: TestClient) -> None:
    ids = [client.post("/objetivos", json=goal(f"Objetivo {i}")).json()["id"] for i in range(3)]

    response = client.delete(f"/objetivos/{ids[0]}")

    assert response.status_code == 204
    assert [item["id"] for item in client.get("/objetivos").json()] == ids[1:]
    assert client.post("/objetivos", json=goal("Nuevo")).status_code == 201


def test_delete_of_an_unknown_goal_returns_404(client: TestClient) -> None:
    assert client.delete(f"/objetivos/{uuid.uuid4()}").status_code == 404
    assert client.delete("/objetivos/not-a-uuid").status_code == 422


def test_post_rejects_invalid_goals(client: TestClient) -> None:
    invalid_bodies = [
        goal(amount="0"),
        goal(term_months=61),
        goal(term_months=0),
        goal(priority=4),
        goal(name=""),
        goal(amount="100.001"),
    ]

    for body in invalid_bodies:
        assert client.post("/objetivos", json=body).status_code == 422, body
    assert client.get("/objetivos").json() == []
