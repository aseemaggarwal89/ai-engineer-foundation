# app/core/tracing.py

"""
Tracing setup for OpenTelemetry.

Purpose:
- Enable distributed tracing across FastAPI + SQLAlchemy
- Export traces to OTLP collector (Jaeger/Tempo/etc.)
- Avoid terminal noise by default
- Allow easy temporary console tracing for debugging
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Console exporter — useful only for local debugging (kept commented)
# from opentelemetry.sdk.trace.export import ConsoleSpanExporter

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from app.db.db import engine


def setup_tracing(app, service_name: str) -> None:
    """
    Initialize OpenTelemetry tracing.

    What this wires:
    App → OpenTelemetry SDK → OTLP exporter → Trace backend

    Console exporter is intentionally disabled to prevent terminal spam.
    """

    # ---------------------------------------------------------
    # 1️⃣ Define resource metadata (appears in trace backend)
    # ---------------------------------------------------------
    resource = Resource.create({
        "service.name": service_name
    })

    # ---------------------------------------------------------
    # 2️⃣ Create tracer provider
    # ---------------------------------------------------------
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # ---------------------------------------------------------
    # 3️⃣ OTLP exporter (production path)
    # Sends spans to collector instead of terminal
    # ---------------------------------------------------------
    otlp_exporter = OTLPSpanExporter(
        endpoint="localhost:4317",
        insecure=True
    )

    provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    # ---------------------------------------------------------
    # 4️⃣ OPTIONAL — Console exporter (DEBUG ONLY)
    # This prints every span JSON to terminal → very noisy
    # Enable only for short debugging sessions
    # ---------------------------------------------------------
    # provider.add_span_processor(
    #     BatchSpanProcessor(ConsoleSpanExporter())
    # )

    # ---------------------------------------------------------
    # 5️⃣ FastAPI auto-instrumentation
    # Captures request/response spans automatically
    # ---------------------------------------------------------
    FastAPIInstrumentor.instrument_app(app)

    # ---------------------------------------------------------
    # 6️⃣ SQLAlchemy auto-instrumentation
    # Captures DB connect/query spans
    # ---------------------------------------------------------
    SQLAlchemyInstrumentor().instrument(
        engine=engine.sync_engine
    )
