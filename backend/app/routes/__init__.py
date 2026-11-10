from .health import router as health_router
from .model_info import router as model_info_router
from .upload import router as upload_router
from .segmentation import router as segmentation_router
from .enhancement import router as enhancement_router
from .results import router as results_router

__all__ = [
    "health_router",
    "model_info_router",
    "upload_router",
    "segmentation_router",
    "enhancement_router",
    "results_router"
]
