# app/core/tracing.py

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from app.db.db import engine
from opentelemetry.sdk.resources import Resource


def setup_tracing(app, service_name: str) -> None:
    resource = Resource.create({
    "service.name": "ai-engineer-api"
    })

    # 1️⃣ tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
    provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )
    # 2️⃣ exporter (console for now)
    span_processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(span_processor)

    # 3️⃣ FastAPI instrumentation
    FastAPIInstrumentor.instrument_app(app)

    # 4️⃣ SQLAlchemy instrumentation
    SQLAlchemyInstrumentor().instrument(
        engine=engine.sync_engine
    )
