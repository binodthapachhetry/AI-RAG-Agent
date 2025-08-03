from fastapi import FastAPI

from ..observability.access_log import AccessLogMiddleware
from ..observability.logging import setup_logging
from ..observability.metrics import setup_metrics
from ..observability.tracing import setup_tracing
from .middleware import RequestIDMiddleware
from .routers import answer as answer_router
from .routers import echo as echo_router
from .routers import health as health_router
from .settings import settings


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.name, version=settings.version, debug=settings.debug)
    setup_tracing(app, service_name=settings.name)
    setup_metrics(app)

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(AccessLogMiddleware)

    app.include_router(health_router.router, tags=["health"])
    app.include_router(echo_router.router, tags=["echo"])
    app.include_router(answer_router.router, tags=["answer"])

    return app
