from fastapi import FastAPI

from .middleware import RequestIDMiddleware
from .routers import answer as answer_router
from .routers import echo as echo_router
from .routers import health as health_router
from .settings import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.name, version=settings.version, debug=settings.debug)
    app.add_middleware(RequestIDMiddleware)

    app.include_router(health_router.router, tags=["health"])
    app.include_router(echo_router.router, tags=["echo"])
    app.include_router(answer_router.router, tags=["answer"])

    return app
