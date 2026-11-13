"""``/plan``: compute the plan with the deterministic engine, or simulate alternatives."""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from api import repository
from api.deps import ParametersDep, SessionDep, UserIdDep
from api.schemas import PlanResponse, SimulationRequest, SimulationResponse
from engine import PlanInput, build_plan
from engine.models import Profile

router = APIRouter(prefix="/plan", tags=["plan"])

PROFILE_REQUIRED = "Para calcular el plan hace falta la ficha de perfil. Créala con PUT /perfil."


def _stored_input(session: Session, user_id: uuid.UUID) -> PlanInput:
    profile_row = repository.get_profile(session, user_id)
    if profile_row is None:
        raise HTTPException(status.HTTP_409_CONFLICT, PROFILE_REQUIRED)
    goals = [repository.to_engine_goal(row) for row in repository.list_goals(session, user_id)]
    return PlanInput(profile=repository.to_engine_profile(profile_row), goals=goals)


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(session: SessionDep, user_id: UserIdDep, params: ParametersDep) -> PlanResponse:
    """Compute the plan from the stored profile and goals, and store the result."""
    result = build_plan(_stored_input(session, user_id), params)
    row = repository.save_plan(session, user_id, result)
    response = PlanResponse(id=row.id, created_at=row.created_at, result=result)
    session.commit()
    return response


@router.post("/simular", response_model=SimulationResponse)
def simulate_plan(
    body: SimulationRequest, session: SessionDep, user_id: UserIdDep, params: ParametersDep
) -> SimulationResponse:
    """Compute a plan with alternative profile values or goals. Nothing is stored."""
    plan_input = _stored_input(session, user_id)
    if body.profile is not None:
        overrides = body.profile.model_dump(exclude_none=True)
        plan_input = PlanInput(
            profile=Profile(**{**plan_input.profile.model_dump(), **overrides}),
            goals=plan_input.goals,
        )
    if body.goals is not None:
        plan_input = PlanInput(profile=plan_input.profile, goals=body.goals)
    return SimulationResponse(input=plan_input, result=build_plan(plan_input, params))
