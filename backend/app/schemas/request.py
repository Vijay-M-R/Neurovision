from typing import Optional, Dict
from pydantic import BaseModel, Field


class EnhanceRequest(BaseModel):
    modality: int = Field(
        default=0,
        ge=0,
        le=3,
        description="MRI modality index: 0=FLAIR, 1=T1, 2=T1ce, 3=T2"
    )
    clip_limit: float = Field(
        default=2.0,
        gt=0.0,
        le=10.0,
        description="CLAHE contrast clip limit"
    )
    slice_indices: Optional[Dict[str, int]] = Field(
        default=None,
        description="Optional manual slice indices dict: {'axial': int, 'coronal': int, 'sagittal': int}"
    )


class SegmentRequest(BaseModel):
    generate_visualization: bool = Field(
        default=True,
        description="Whether to generate the orthogonal 3x3 comparison PNG"
    )
