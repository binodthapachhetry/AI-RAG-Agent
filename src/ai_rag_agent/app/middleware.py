import uuid
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=req_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers["x-request-id"] = req_id
        return response
