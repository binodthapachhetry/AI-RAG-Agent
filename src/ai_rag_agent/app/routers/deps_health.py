# src/ai_rag_agent/app/routers/deps_health.py
from fastapi import APIRouter

from ...app.settings import settings
from ...persistence.cache import get_redis

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/config")
async def config():
    pong = await get_redis().ping()
    return {"redis_url": settings.redis_url, "redis_ping": pong}
