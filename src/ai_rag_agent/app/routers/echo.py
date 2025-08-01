from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field


class EchoIn(BaseModel):
    message: str = Field(..., min_length=1)


class EchoOut(BaseModel):
    message: str
    received_at: datetime


router = APIRouter()


@router.post("/echo", response_model=EchoOut)
async def echo(payload: EchoIn) -> EchoOut:
    return EchoOut(message=payload.message, received_at=datetime.now(timezone.utc))
