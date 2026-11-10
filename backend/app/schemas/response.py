from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Backend health status, e.g. 'ok'")
    ai_engine_available: bool = Field(..., description="Whether the AI engine is accessible")
    model_loaded: bool = Field(..., description="Whether the SegResNet model is loaded in memory")
    device: str = Field(..., description="Compute device ('cuda' or 'cpu')")
    cuda_available: bool = Field(..., description="Whether CUDA is supported and active")
    device_name: Optional[str] = Field(None, description="Name of the GPU device if CUDA is active")


class ModelInfoResponse(BaseModel):
    model_name: str
    architecture: str
    bundle: str
    version: str
    parameters: int
    input_channels: int
    output_channels: int
    device: str
    status: str
    training_disabled: bool
    fine_tuning_disabled: bool
    cached: bool


class UploadResponse(BaseModel):
    job_id: str
    status: str
    filename: str
    file_size_bytes: int
    dimensions: List[int]
    modalities: int
    message: Optional[str] = None


class RegionVoxelCounts(BaseModel):
    WT: int = Field(..., description="Whole Tumor voxel count")
    TC: int = Field(..., description="Tumor Core voxel count")
    ET: int = Field(..., description="Enhancing Tumor voxel count")


class SegmentResponse(BaseModel):
    job_id: str
    status: str
    model: str
    device: str
    processing_time_seconds: float
    regions: RegionVoxelCounts
    tumor_voxels: int
    dimensions: List[int]
    visualization_url: str
    results_url: str
    download_url: str
    evaluation_available: bool = False
    evaluation_message: Optional[str] = None


class EnhanceResponse(BaseModel):
    job_id: str
    status: str
    modality: str
    slices: Dict[str, int]
    preview_urls: Dict[str, str]


class ErrorResponse(BaseModel):
    detail: str
    error_type: Optional[str] = None
