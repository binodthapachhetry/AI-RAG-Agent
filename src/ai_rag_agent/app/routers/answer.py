import asyncio
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from starlette.responses import StreamingResponse


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
    """
    RAG stub. If stream=true (default), returns a streaming response.
    Otherwise, returns a JSON AnswerOut. Replace with real RAG soon.
    """
    canned = "This is a placeholder answer. RAG coming next."
    if stream:
        return StreamingResponse(_stream_stub(canned), media_type="text/plain; charset=utf-8")
    return AnswerOut(answer=canned, citations=[])
