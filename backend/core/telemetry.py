import os
import time
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


def configure_telemetry(app_name: str = "fastapi-app"):
    """
    Configure OpenTelemetry for traces and metrics.
    All data goes to self-hosted LGTM stack - NO external services.
    """
    
    tempo_endpoint = os.getenv('TEMPO_ENDPOINT', 'http://tempo:4317')
    trace_provider = TracerProvider(
        resource=Resource.create({"service.name": app_name})
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
        resource=Resource.create({"service.name": app_name}),
        metric_readers=[prometheus_reader]
    )
    
    metrics.set_meter_provider(metric_provider)
    
    return trace_provider, metric_provider


# Global metrics instruments
meter = None
http_requests_total = None
http_request_duration = None
http_request_size = None
http_response_size = None


def init_http_metrics():
    """Initialize HTTP metrics after meter provider is set up"""
    global meter, http_requests_total, http_request_duration, http_request_size, http_response_size
    
    meter = metrics.get_meter(__name__)
    
    # HTTP request counter
    http_requests_total = meter.create_counter(
        name="http_requests_total",
        description="Total number of HTTP requests",
        unit="1"
    )
    
    # HTTP request duration histogram
    http_request_duration = meter.create_histogram(
        name="http_request_duration_seconds",
        description="HTTP request duration in seconds",
        unit="s"
    )
    
    # HTTP request size histogram
    http_request_size = meter.create_histogram(
        name="http_request_size_bytes",
        description="HTTP request size in bytes",
        unit="By"
    )
    
    # HTTP response size histogram
    http_response_size = meter.create_histogram(
        name="http_response_size_bytes",
        description="HTTP response size in bytes",
        unit="By"
    )


class HTTPMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get request size
        request_size = 0
        if hasattr(request, 'headers'):
            content_length = request.headers.get('content-length')
            if content_length:
                request_size = int(content_length)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get response size
        response_size = 0
        if hasattr(response, 'headers'):
            content_length = response.headers.get('content-length')
            if content_length:
                response_size = int(content_length)
        
        # Extract labels
        method = request.method
        path = request.url.path
        status_code = str(response.status_code)
        
        # Record metrics
        if http_requests_total:
            http_requests_total.add(1, {
                "method": method,
                "endpoint": path,
                "status": status_code
            })
        
        if http_request_duration:
            http_request_duration.record(duration, {
                "method": method,
                "endpoint": path,
                "status": status_code
            })
        
        if http_request_size and request_size > 0:
            http_request_size.record(request_size, {
                "method": method,
                "endpoint": path
            })
        
        if http_response_size and response_size > 0:
            http_response_size.record(response_size, {
                "method": method,
                "endpoint": path,
                "status": status_code
            })
        
        return response


def instrument_app(app):
    """
    Auto-instrument FastAPI app and database connections.
    """
    
    # Initialize HTTP metrics first
    init_http_metrics()
    
    # Add HTTP metrics middleware
    app.add_middleware(HTTPMetricsMiddleware)
    
    # Auto instrument FastAPI - traces all HTTP requests
    FastAPIInstrumentor.instrument_app(app)
    
    # Auto instrument PostgreSQL queries
    Psycopg2Instrumentor().instrument()
    
    # Auto instrument Redis operations
    RedisInstrumentor().instrument()
    
    print("OpenTelemetry instrumentation enabled with HTTP metrics, sending data to LGTM stack")
