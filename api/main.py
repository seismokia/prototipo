"""FastAPI application entry point."""

from typing import Annotated

from fastapi import Depends, FastAPI

from api.config import Settings, get_settings
from api.routers import goals, plan, profile
from api.schemas import HealthResponse

app = FastAPI(title="Asistente patrimonial", version=get_settings().version)
app.include_router(profile.router)
app.include_router(goals.router)
app.include_router(plan.router)


@app.get("/health", response_model=HealthResponse, tags=["sistema"])
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Report that the service is up."""
    return HealthResponse(
        status="ok",
        service=settings.name,
        version=settings.version,
        environment=settings.environment,
    )
