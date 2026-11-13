"""``/perfil``: read or correct the profile sheet."""

from fastapi import APIRouter, HTTPException, status

from api import repository
from api.deps import SessionDep, UserIdDep
from api.schemas import ProfileBody, ProfileResponse

router = APIRouter(prefix="/perfil", tags=["perfil"])

PROFILE_NOT_FOUND = "Todavía no hay ficha de perfil. Créala con PUT /perfil."


@router.get("", response_model=ProfileResponse)
def read_profile(session: SessionDep, user_id: UserIdDep) -> ProfileResponse:
    row = repository.get_profile(session, user_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, PROFILE_NOT_FOUND)
    return ProfileResponse.model_validate(row, from_attributes=True)


@router.put("", response_model=ProfileResponse)
def write_profile(body: ProfileBody, session: SessionDep, user_id: UserIdDep) -> ProfileResponse:
    """Create the profile sheet or replace it completely."""
    repository.lock_user(session, user_id)
    row = repository.upsert_profile(session, user_id, body)
    response = ProfileResponse.model_validate(row, from_attributes=True)
    session.commit()
    return response
