import os
import time

from fastapi import Request
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from starlette.middleware.base import BaseHTTPMiddleware

# Global metrics instruments
meter = None
http_requests_total = None
http_request_duration = None
http_request_size = None
http_response_size = None

# Business metrics counters
user_registrations_total = None
login_attempts_total = None
postings_created_total = None
applications_submitted_total = None

class HTTPMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        path = request.url.path

        request_size = 0
        if hasattr(request, "headers"):
            content_length = request.headers.get("content-length")
            if content_length:
                request_size = int(content_length)

        # Default to 500 so that unhandled exceptions are counted correctly.
        # BaseHTTPMiddleware.call_next propagates exceptions instead of returning
        # a 500 response, so without this default the metric would be missed.
        status_code = "500"
        response = None
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception:
            raise
        finally:
            duration = time.time() - start_time

            if http_requests_total:
                http_requests_total.add(1, {
                    "method": method,
                    "endpoint": path,
                    "status": status_code,
                })

            if http_request_duration:
                http_request_duration.record(duration, {
                    "method": method,
                    "endpoint": path,
                    "status": status_code,
                })

            if http_request_size and request_size > 0:
                http_request_size.record(request_size, {
                    "method": method,
                    "endpoint": path,
                })

            if response is not None and http_response_size:
                response_size = 0
                if hasattr(response, "headers"):
                    content_length = response.headers.get("content-length")
                    if content_length:
                        response_size = int(content_length)
                if response_size > 0:
                    http_response_size.record(response_size, {
                        "method": method,
                        "endpoint": path,
                        "status": status_code,
                    })

        return response

def configure_telemetry(app_name: str = "fastapi-backend"):
    """
    Configure OpenTelemetry for traces and metrics.
    All data goes to self-hosted LGTM stack - NO external services.
    """
    
    tempo_endpoint = os.getenv('TEMPO_ENDPOINT', 'http://tempo:4317')
    trace_provider = TracerProvider(
        resource=Resource.create({
            "service.name": app_name,
            "service.version": "1.0.0",
            "deployment.environment": "dev"
        })
    )
    
    # Export traces to your Tempo instance
    otlp_trace_exporter = OTLPSpanExporter(
        endpoint=tempo_endpoint,
        insecure=True  # Internal cluster communication
    )
    
    trace_provider.add_span_processor(
        BatchSpanProcessor(otlp_trace_exporter)
    )
    
    trace.set_tracer_provider(trace_provider)
    
    # configure metrics with Mimir by /metrics endpoint
    prometheus_reader = PrometheusMetricReader()  # Creates /metrics endpoint for Mimir to scrape    
    metric_provider = MeterProvider(
        resource=Resource.create({
            "service.name": app_name,
            "service.version": "1.0.0",
            "deployment.environment": "dev"
        }),
        metric_readers=[prometheus_reader]
    )
    
    metrics.set_meter_provider(metric_provider)
    
    return trace_provider, metric_provider

def init_http_metrics():
    """Initialize HTTP metrics after meter provider is set up"""
    global meter, http_requests_total, http_request_duration, http_request_size, http_response_size
    global user_registrations_total, login_attempts_total, postings_created_total, applications_submitted_total

    meter = metrics.get_meter(__name__)

    http_requests_total = meter.create_counter(
        name="http_requests_total",
        description="Total number of HTTP requests",
        unit="1"
    )

    http_request_duration = meter.create_histogram(
        name="http_request_duration_seconds",
        description="HTTP request duration in seconds",
        unit="s"
    )

    http_request_size = meter.create_histogram(
        name="http_request_size_bytes",
        description="HTTP request size in bytes",
        unit="By"
    )

    http_response_size = meter.create_histogram(
        name="http_response_size_bytes",
        description="HTTP response size in bytes",
        unit="By"
    )

    # Business metrics — endpoints return 303 redirects for both success and failure
    # so we cannot rely on HTTP status codes to distinguish outcomes
    user_registrations_total = meter.create_counter(
        name="user_registrations_total",
        description="Total user registration attempts",
        unit="1"
    )

    login_attempts_total = meter.create_counter(
        name="login_attempts_total",
        description="Total login attempts",
        unit="1"
    )

    postings_created_total = meter.create_counter(
        name="postings_created_total",
        description="Total postings created",
        unit="1"
    )

    applications_submitted_total = meter.create_counter(
        name="applications_submitted_total",
        description="Total job application submissions",
        unit="1"
    )


def record_user_registration(result: str):
    """result: 'success' | 'error'"""
    if user_registrations_total:
        user_registrations_total.add(1, {"result": result})


def record_login_attempt(result: str):
    """result: 'success' | 'failure'"""
    if login_attempts_total:
        login_attempts_total.add(1, {"result": result})


def record_posting_created():
    if postings_created_total:
        postings_created_total.add(1, {})


def record_application_submitted(result: str):
    """result: 'success' | 'failure'"""
    if applications_submitted_total:
        applications_submitted_total.add(1, {"result": result})

def instrument_app(app):
    """
    Auto-instrument FastAPI app and database connections.
    """
    
    # Auto instrument FastAPI, traces all HTTP requests
    FastAPIInstrumentor.instrument_app(app)
    
    # Auto instrument database connections
    Psycopg2Instrumentor().instrument()
    RedisInstrumentor().instrument()

    init_http_metrics()
    app.add_middleware(HTTPMetricsMiddleware)
    
    print("OpenTelemetry instrumentation enabled with HTTP metrics, sending data to LGTM stack")
