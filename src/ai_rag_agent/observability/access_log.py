# src/ai_rag_agent/observability/access_log.py
import time

import structlog
from opentelemetry import trace  # <-- add
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger()


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0

        # Prefer the ID set by RequestIDMiddleware; fall back to inbound header if needed
        req_id = response.headers.get("x-request-id") or request.headers.get("x-request-id")

        # Attach the request_id (and optionally other fields) to the active span
        span = trace.get_current_span()
        if span is not None and span.is_recording():
            span.set_attribute("request_id", req_id or "")
            # Optional: avoid duplicating attrs OpenTelemetry FastAPI instrumentation already sets
            # span.set_attribute("http.duration_ms", round(duration_ms, 2))

        # Log a single JSON line for the request
        logger.info(
            "http_access",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            user_agent=request.headers.get("user-agent"),
            request_id=req_id,  # explicit; also present via structlog contextvars
        )
        return response
