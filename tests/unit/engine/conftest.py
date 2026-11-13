"""Shared fixtures: fixed parameters so the tests do not depend on the illustrative YAML."""

from copy import deepcopy
from decimal import Decimal
from typing import Any

import pytest

from engine.models import Goal, Profile, RiskProfile
from engine.parameters import Parameters

ASSET_CLASSES = [
    "liquidez",
    "monetario",
    "renta_fija_corto",
    "renta_fija_medio",
    "renta_variable_global",
]


def weights(**non_zero: int) -> dict[str, int]:
    return {asset_class: non_zero.get(asset_class, 0) for asset_class in ASSET_CLASSES}


def flat_returns(value: str) -> dict[str, str]:
    return dict.fromkeys(ASSET_CLASSES, value)


RAW_PARAMETERS: dict[str, Any] = {
    "version": "test",
    "fondo_emergencia": {
        "meses_por_perfil": {"conservador": 6, "moderado": 4, "dinamico": 3},
        "fraccion_capacidad_ahorro": "0.5",
    },
    "asignacion": {
        "tramos": [
            {
                "plazo_max_meses": 12,
                "perfiles": {
                    "conservador": weights(liquidez=100),
                    "moderado": weights(liquidez=50, monetario=50),
                    "dinamico": weights(monetario=100),
                },
            },
            {
                "plazo_max_meses": 60,
                "perfiles": {
                    "conservador": weights(monetario=100),
                    "moderado": weights(monetario=50, renta_variable_global=50),
                    "dinamico": weights(renta_variable_global=100),
                },
            },
        ]
    },
    "rentabilidades_anuales": {
        "pesimista": flat_returns("-0.05"),
        "central": flat_returns("0"),
        "optimista": flat_returns("0.05"),
    },
}


@pytest.fixture
def raw_parameters() -> dict[str, Any]:
    """Mutable copy of the raw parameters, for tests that break them on purpose."""
    return deepcopy(RAW_PARAMETERS)


@pytest.fixture
def params() -> Parameters:
    return Parameters.model_validate(RAW_PARAMETERS)


def make_profile(**overrides: Any) -> Profile:
    """Moderate profile: capacity 800/month, emergency fund (4 x 1500 = 6000) fully covered."""
    data: dict[str, Any] = {
        "monthly_income": Decimal("2500"),
        "monthly_expenses": Decimal("1500"),
        "monthly_debt_payment": Decimal("200"),
        "current_savings": Decimal("6000"),
        "dependents": 0,
        "risk_profile": RiskProfile.MODERADO,
    }
    data.update(overrides)
    return Profile(**data)


def make_goal(amount: str, term_months: int, priority: int = 1, name: str = "Objetivo") -> Goal:
    return Goal(name=name, amount=Decimal(amount), term_months=term_months, priority=priority)
