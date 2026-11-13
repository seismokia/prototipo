"""Calculation parameters, loaded and validated from ``engine/config/parametros.yaml``.

The YAML keys are in Spanish (they are edited and justified in the thesis);
the Python attributes are in English and mapped through aliases.
"""

from decimal import Decimal
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from engine.models import MAX_TERM_MONTHS, AssetClass, RiskProfile, Scenario

DEFAULT_PARAMETERS_PATH = Path(__file__).parent / "config" / "parametros.yaml"

_HUNDRED = Decimal("100")


class ParametersModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)


class EmergencyFundParameters(ParametersModel):
    months_by_profile: dict[RiskProfile, int] = Field(alias="meses_por_perfil")
    savings_capacity_fraction: Decimal = Field(alias="fraccion_capacidad_ahorro", ge=0, le=1)

    @model_validator(mode="after")
    def _check_profiles(self) -> Self:
        _require_keys(self.months_by_profile, RiskProfile, "meses_por_perfil")
        if any(months < 0 for months in self.months_by_profile.values()):
            raise ValueError("meses_por_perfil: months cannot be negative")
        return self


class AllocationBand(ParametersModel):
    """Allocation table row: applies to goals whose term is at most ``max_term_months``."""

    max_term_months: int = Field(alias="plazo_max_meses", ge=1)
    profiles: dict[RiskProfile, dict[AssetClass, Decimal]] = Field(alias="perfiles")

    @model_validator(mode="after")
    def _check_weights(self) -> Self:
        _require_keys(self.profiles, RiskProfile, "perfiles")
        for profile, weights in self.profiles.items():
            where = f"tramo {self.max_term_months} / {profile.value}"
            _require_keys(weights, AssetClass, where)
            if any(weight < 0 for weight in weights.values()):
                raise ValueError(f"{where}: weights cannot be negative")
            if sum(weights.values()) != _HUNDRED:
                raise ValueError(f"{where}: weights must sum to 100")
        return self


class AllocationParameters(ParametersModel):
    bands: list[AllocationBand] = Field(alias="tramos", min_length=1)

    @model_validator(mode="after")
    def _check_bands(self) -> Self:
        limits = [band.max_term_months for band in self.bands]
        if limits != sorted(set(limits)):
            raise ValueError("tramos: plazo_max_meses must be strictly increasing")
        if limits[-1] < MAX_TERM_MONTHS:
            raise ValueError(f"tramos: the last band must cover {MAX_TERM_MONTHS} months")
        return self


class Parameters(ParametersModel):
    version: str = Field(min_length=1)
    emergency_fund: EmergencyFundParameters = Field(alias="fondo_emergencia")
    allocation: AllocationParameters = Field(alias="asignacion")
    annual_returns: dict[Scenario, dict[AssetClass, Decimal]] = Field(
        alias="rentabilidades_anuales"
    )

    @model_validator(mode="after")
    def _check_returns(self) -> Self:
        _require_keys(self.annual_returns, Scenario, "rentabilidades_anuales")
        for scenario, returns in self.annual_returns.items():
            where = f"rentabilidades_anuales / {scenario.value}"
            _require_keys(returns, AssetClass, where)
            if any(annual_return <= -1 for annual_return in returns.values()):
                raise ValueError(f"{where}: returns must be greater than -1")
        return self


def _require_keys(mapping: dict, enum: type, where: str) -> None:
    missing = [member.value for member in enum if member not in mapping]
    if missing:
        raise ValueError(f"{where}: missing {', '.join(missing)}")


def load_parameters(path: Path = DEFAULT_PARAMETERS_PATH) -> Parameters:
    """Read and validate the parameters file. Raises ``ValidationError`` if it is invalid."""
    with path.open(encoding="utf-8") as file:
        raw = yaml.safe_load(file)
    return Parameters.model_validate(raw)
