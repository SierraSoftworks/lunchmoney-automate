from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from grpc import ssl_channel_credentials
import os
import logging

resource = Resource(attributes={"service.name": "lunchmoney-automate"})

trace_provider = TracerProvider(resource=resource)

if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") is not None:
    trace_exporter = OTLPSpanExporter(
        endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"),
        credentials=ssl_channel_credentials(),
        service_name="lunchmoney-automate",
    )

    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

if os.environ.get("HONEYCOMB_API_KEY") is not None:
    otlp_exporter = OTLPSpanExporter(
        endpoint="api.honeycomb.io:443",
        insecure=False,
        credentials=ssl_channel_credentials(),
        headers=(
            ("x-honeycomb-team", os.environ.get("HONEYCOMB_API_KEY")),
            ("x-honeycomb-dataset", os.environ.get("HONEYCOMB_DATASET")),
        ),
    )

    trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

trace.set_tracer_provider(trace_provider)

LoggingInstrumentor().instrument(set_logging_format=True, log_level=logging.ERROR)
RequestsInstrumentor().instrument()