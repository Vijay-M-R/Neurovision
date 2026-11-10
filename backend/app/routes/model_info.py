from fastapi import APIRouter
from backend.app.schemas.response import ModelInfoResponse
from ai_engine.model.loader import get_model_info

router = APIRouter(prefix="/api", tags=["Model"])


@router.get("/model-info", response_model=ModelInfoResponse)
async def get_info():
    """
    Retrieve architecture, bundle version, parameters, and operational device info.
    """
    raw_info = get_model_info()
    return ModelInfoResponse(
        model_name=raw_info.get("model_name", "MONAI SegResNet"),
        architecture=raw_info.get("architecture", "SegResNet"),
        bundle=raw_info.get("bundle", "brats_mri_segmentation"),
        version=raw_info.get("version", "0.5.2"),
        parameters=raw_info.get("parameters", 4702227),
        input_channels=raw_info.get("input_channels", 4),
        output_channels=raw_info.get("output_channels", 3),
        device=raw_info.get("device", "cuda"),
        status=raw_info.get("status", "loaded"),
        training_disabled=not raw_info.get("training_enabled", False),
        fine_tuning_disabled=not raw_info.get("fine_tuning", False),
        cached=raw_info.get("cached", True)
    )
