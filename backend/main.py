from api import endpoints
from core.telemetry import configure_telemetry, instrument_app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
