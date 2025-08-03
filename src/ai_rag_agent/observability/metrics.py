from prometheus_fastapi_instrumentator import Instrumentator


def setup_metrics(app) -> None:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
