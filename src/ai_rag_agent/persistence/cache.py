# src/ai_rag_agent/persistence/cache.py
from __future__ import annotations

import json
from typing import Any, Optional

import redis.asyncio as redis

from ..app.settings import settings

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        # Create a single asyncio connection pool
        _redis = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return _redis


async def cache_get_json(key: str) -> Optional[dict[str, Any]]:
    r = get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None


async def cache_set_json(key: str, value: dict[str, Any], ttl_s: int) -> None:
    r = get_redis()
    await r.set(key, json.dumps(value), ex=ttl_s)


def answer_cache_key(query: str) -> str:
    # Simple deterministic key; consider hashing for long strings
    return f"ans:v1:{query.strip().lower()}"
