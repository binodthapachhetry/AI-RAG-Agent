import asyncio
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from ...persistence.cache import answer_cache_key, cache_get_json, cache_set_json


class AnswerIn(BaseModel):
    query: str


class AnswerOut(BaseModel):
    answer: str
    citations: list[str]


router = APIRouter(prefix="/v1")


async def _stream_stub(text: str) -> AsyncIterator[bytes]:
    # Simulate token streaming; replace later with model streaming
    for part in text.split(" "):
        yield (part + " ").encode("utf-8")
        await asyncio.sleep(0.02)


@router.post("/answer")
async def answer(payload: AnswerIn, stream: Optional[bool] = Query(default=True)):
    key = answer_cache_key(payload.query)

    # 1) Try cache first (works only for non-stream mode for simplicity)
    if not stream:
        cached = await cache_get_json(key)
        if cached:
            return AnswerOut(**cached)

    canned = "This is a placeholder answer. RAG coming next."

    if stream:
        return StreamingResponse(_stream_stub(canned), media_type="text/plain; charset=utf-8")

    # 2) Store non-stream response
    out = AnswerOut(answer=canned, citations=[])
    await cache_set_json(key, out.model_dump(), ttl_s=300)  # 5 minutes
    return out
