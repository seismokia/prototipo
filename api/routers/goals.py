"""``/objetivos``: manage the user's goals (at most three)."""

import uuid

from fastapi import APIRouter, HTTPException, Response, status

from api import repository
from api.deps import SessionDep, UserIdDep
from api.schemas import GoalBody, GoalResponse
from engine.models import MAX_GOALS

router = APIRouter(prefix="/objetivos", tags=["objetivos"])

TOO_MANY_GOALS = f"Ya hay {MAX_GOALS} objetivos, que es el máximo. Borra uno antes de añadir otro."
GOAL_NOT_FOUND = "El objetivo no existe."


@router.get("", response_model=list[GoalResponse])
def list_goals(session: SessionDep, user_id: UserIdDep) -> list[GoalResponse]:
    """Goals in funding order: priority, then shorter term."""
    rows = repository.list_goals(session, user_id)
    return [GoalResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(body: GoalBody, session: SessionDep, user_id: UserIdDep) -> GoalResponse:
    repository.lock_user(session, user_id)
    if len(repository.list_goals(session, user_id)) >= MAX_GOALS:
        raise HTTPException(status.HTTP_409_CONFLICT, TOO_MANY_GOALS)
    row = repository.add_goal(session, user_id, body)
    response = GoalResponse.model_validate(row, from_attributes=True)
    session.commit()
    return response


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: uuid.UUID, session: SessionDep, user_id: UserIdDep) -> Response:
    if not repository.delete_goal(session, user_id, goal_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, GOAL_NOT_FOUND)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
