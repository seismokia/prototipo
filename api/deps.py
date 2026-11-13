"""Dependencies shared by the routers."""

import uuid
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from api.db.models import DEMO_USER_ID
from api.db.session import get_session
from engine import Parameters, load_parameters


def get_current_user_id() -> uuid.UUID:
    """The prototype has no authentication: every request acts as the demo user."""
    return DEMO_USER_ID


@lru_cache
def get_parameters() -> Parameters:
    """Calculation parameters, loaded once from ``engine/config/parametros.yaml``."""
    return load_parameters()


SessionDep = Annotated[Session, Depends(get_session)]
UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
ParametersDep = Annotated[Parameters, Depends(get_parameters)]
