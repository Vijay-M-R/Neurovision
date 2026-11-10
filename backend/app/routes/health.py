import torch
from fastapi import APIRouter
from backend.app.schemas.response import HealthResponse
from ai_engine.model.loader import load_model

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def check_health():
    """
    Check backend, AI engine, and GPU health without executing inference.
    """
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else None
    
    # Check if model has been loaded into lru_cache
    model_cached = load_model.cache_info().currsize > 0
    device_str = "cuda" if cuda_available else "cpu"

    return HealthResponse(
        status="ok",
        ai_engine_available=True,
        model_loaded=model_cached,
        device=device_str,
        cuda_available=cuda_available,
        device_name=device_name
    )
