from fastapi.middleware.cors import CORSMiddleware
from api import endpoints
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from fastapi import FastAPI, Response
from core.telemetry import configure_telemetry, instrument_app

app = FastAPI(title="FastAPI App", version="1.0.0")

# Initialize OpenTelemetry first
configure_telemetry("fastapi-backend")
instrument_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router)
app.include_router(endpoints.api_router)


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
