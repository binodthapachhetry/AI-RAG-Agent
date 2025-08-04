import os

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = structlog.get_logger()


def setup_tracing(app, service_name: str = "ai-rag-agent") -> None:
    from ..app.settings import settings

    if not settings.enable_tracing:
        # Do nothing in tests / by default
        return

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    logger.info("otel_config", exporter_endpoint=endpoint)

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
