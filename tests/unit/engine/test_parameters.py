from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from engine.models import AssetClass, RiskProfile, Scenario
from engine.parameters import DEFAULT_PARAMETERS_PATH, Parameters, load_parameters


def test_default_file_loads_and_is_marked_as_illustrative() -> None:
    params = load_parameters()

    assert "ilustrativo" in params.version
    assert "VALORES ILUSTRATIVOS" in DEFAULT_PARAMETERS_PATH.read_text(encoding="utf-8")
    assert set(params.emergency_fund.months_by_profile) == set(RiskProfile)
    assert set(params.annual_returns) == set(Scenario)
    for band in params.allocation.bands:
        for weights in band.profiles.values():
            assert set(weights) == set(AssetClass)
            assert sum(weights.values()) == Decimal(100)


def test_load_parameters_reads_a_custom_file(tmp_path: Path, raw_parameters: dict) -> None:
    path = tmp_path / "parametros.yaml"
    path.write_text(yaml.safe_dump(raw_parameters), encoding="utf-8")

    assert load_parameters(path).version == "test"


def test_empty_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "parametros.yaml"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValidationError):
        load_parameters(path)


def _first_band(raw: dict[str, Any]) -> dict[str, Any]:
    return raw["asignacion"]["tramos"][0]


def _weights_not_100(raw: dict[str, Any]) -> None:
    _first_band(raw)["perfiles"]["conservador"]["liquidez"] = 90


def _negative_weight(raw: dict[str, Any]) -> None:
    weights = _first_band(raw)["perfiles"]["conservador"]
    weights["liquidez"] = 110
    weights["monetario"] = -10


def _missing_asset_class(raw: dict[str, Any]) -> None:
    del _first_band(raw)["perfiles"]["conservador"]["monetario"]


def _missing_profile_in_band(raw: dict[str, Any]) -> None:
    del _first_band(raw)["perfiles"]["dinamico"]


def _bands_not_increasing(raw: dict[str, Any]) -> None:
    raw["asignacion"]["tramos"].reverse()


def _last_band_too_short(raw: dict[str, Any]) -> None:
    raw["asignacion"]["tramos"][-1]["plazo_max_meses"] = 48


def _no_bands(raw: dict[str, Any]) -> None:
    raw["asignacion"]["tramos"] = []


def _missing_fund_profile(raw: dict[str, Any]) -> None:
    del raw["fondo_emergencia"]["meses_por_perfil"]["moderado"]


def _negative_fund_months(raw: dict[str, Any]) -> None:
    raw["fondo_emergencia"]["meses_por_perfil"]["moderado"] = -1


def _fraction_above_one(raw: dict[str, Any]) -> None:
    raw["fondo_emergencia"]["fraccion_capacidad_ahorro"] = "1.5"


def _missing_scenario(raw: dict[str, Any]) -> None:
    del raw["rentabilidades_anuales"]["pesimista"]


def _missing_return(raw: dict[str, Any]) -> None:
    del raw["rentabilidades_anuales"]["central"]["liquidez"]


def _total_loss_return(raw: dict[str, Any]) -> None:
    raw["rentabilidades_anuales"]["pesimista"]["liquidez"] = "-1"


def _unknown_key(raw: dict[str, Any]) -> None:
    raw["inflacion"] = "0.02"


@pytest.mark.parametrize(
    "break_parameters",
    [
        _weights_not_100,
        _negative_weight,
        _missing_asset_class,
        _missing_profile_in_band,
        _bands_not_increasing,
        _last_band_too_short,
        _no_bands,
        _missing_fund_profile,
        _negative_fund_months,
        _fraction_above_one,
        _missing_scenario,
        _missing_return,
        _total_loss_return,
        _unknown_key,
    ],
)
def test_invalid_parameters_are_rejected(raw_parameters: dict, break_parameters) -> None:
    break_parameters(raw_parameters)

    with pytest.raises(ValidationError):
        Parameters.model_validate(raw_parameters)
