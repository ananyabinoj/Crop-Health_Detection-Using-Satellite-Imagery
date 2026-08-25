"""
CropVision - Agricultural Technology Satellite Health Monitoring Backend
FastAPI Main Application
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import init_db
from backend.seed_data import seed_database
from backend.routers import fields, analysis, history, reports
from backend.services.satellite_pipeline import GEE_AVAILABLE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cropvision.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CropVision database and seeding demo fields...")
    seed_database()
    logger.info("CropVision Backend startup complete.")
    yield
    logger.info("Shutting down CropVision Backend.")


app = FastAPI(
    title="CropVision API",
    description="Satellite-Based Crop Health Monitoring System with Composite Crop Health Scoring (CCHS)",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(fields.router)
app.include_router(analysis.router)
app.include_router(history.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {
        "product": "CropVision",
        "tagline": "Satellite-Based Crop Health Monitoring System",
        "status": "online",
        "docs": "/docs",
        "gee_connected": GEE_AVAILABLE,
        "engine_mode": "Google Earth Engine + High-Fidelity Multi-Spectral Raster Pipeline",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "gee_status": "connected" if GEE_AVAILABLE else "simulation_fallback_ready",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
