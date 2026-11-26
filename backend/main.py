from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import api_router
from backend.config import settings
from backend.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown routines."""
    print("Starting RetailMind AI Backend Engine...")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Initializing database schemas on: {settings.DATABASE_URL.split('///')[-1]}")
    await init_db()
    print("Database schemas initialized.")
    yield
    print("Shutting down RetailMind AI Backend Engine...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Intelligent Retail Inventory, Visible Shelf Stock Tracking & Demand Intelligence Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Ensure detection results directory exists and mount static files
results_dir = Path(settings.DETECTION_RESULTS_DIR)
results_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/detections", StaticFiles(directory=str(results_dir)), name="detections")

samples_dir = Path("sample_data")
if samples_dir.exists():
    app.mount("/static/samples", StaticFiles(directory=str(samples_dir)), name="samples")

# Mount Master API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["System"])
async def root():
    """System root status and navigation."""
    return {
        "project": settings.PROJECT_NAME,
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health", tags=["System"])
async def root_health():
    """Root level health endpoint for container health probes."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
