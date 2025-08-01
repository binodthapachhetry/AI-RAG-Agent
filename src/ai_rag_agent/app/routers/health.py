from fastapi import APIRouter
from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str
    version: str


router = APIRouter()


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    # Minimal liveness info; extend later with dependency checks
    from ..settings import settings

    return HealthOut(status="ok", version=settings.version)
