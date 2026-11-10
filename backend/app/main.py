import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set non-interactive Matplotlib backend for thread-safe server rendering
import matplotlib
matplotlib.use("Agg")

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.utils.errors import (
    NeuroVisionException,
    neurovision_exception_handler,
    global_exception_handler
)
from backend.app.routes import (
    health_router,
    model_info_router,
    upload_router,
    segmentation_router,
    enhancement_router,
    results_router
)
from ai_engine.model.loader import load_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("neurovision")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: Load and warm up model once at startup.
    Ensure storage directories exist.
    """
    logger.info("Initializing NeuroVision backend...")
    
    # Ensure storage paths exist
    settings.uploads_dir
    settings.results_dir
    
    # Load model once using existing LRU cache
    try:
        model, device = load_model()
        logger.info("AI model loaded successfully onto %s", device)
    except Exception as exc:
        logger.error("Failed to load AI model during startup: %s", exc)
        raise

    yield

    logger.info("Shutting down NeuroVision backend...")
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="NeuroVision Medical Image Processing System - FastAPI Backend",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(NeuroVisionException, neurovision_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include core routers
app.include_router(health_router)
app.include_router(model_info_router)
app.include_router(upload_router)
app.include_router(segmentation_router)
app.include_router(enhancement_router)
app.include_router(results_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "project": "NeuroVision",
        "description": "Brain MRI Enhancement and Multi-Region Tumor Segmentation",
        "version": settings.app_version,
        "docs_url": "/docs",
        "health_url": "/api/health"
    }
