import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.db.database import init_db

app = FastAPI(title="NSE Signal Engine", version="2.1.0")

# Set SMKD_CORS_ORIGINS to a comma-separated list of trusted frontend origins.
_raw_origins = os.getenv(
    "SMKD_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,https://localhost,capacitor://localhost",
)
_allowed_origins = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
def initialize_runtime_database() -> None:
    """Create the runtime SQLite schema when the service starts."""
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("SMKD_HOST", "127.0.0.1"),
        port=int(os.getenv("SMKD_PORT", "8000")),
        reload=os.getenv("SMKD_RELOAD", "false").lower() == "true",
    )
