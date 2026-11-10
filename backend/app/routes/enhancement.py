from fastapi import APIRouter, Path as FastApiPath
from backend.app.schemas.response import EnhanceResponse
from backend.app.schemas.request import EnhanceRequest
from backend.app.services.ai_service import ai_service
from backend.app.services.file_service import file_service

router = APIRouter(prefix="/api", tags=["Enhancement"])


@router.post("/enhance/{job_id}", response_model=EnhanceResponse)
async def enhance_mri(
    job_id: str = FastApiPath(..., description="UUID job ID of uploaded MRI"),
    body: EnhanceRequest = EnhanceRequest()
):
    """
    Generate CLAHE contrast-enhanced previews for axial, coronal, and sagittal views.
    Independent from segmentation; leaves the original MRI intact.
    """
    file_service.validate_job_id(job_id)
    result = await ai_service.run_enhancement(
        job_id=job_id,
        modality=body.modality,
        clip_limit=body.clip_limit,
        slice_indices=body.slice_indices
    )

    return EnhanceResponse(
        job_id=job_id,
        status="completed",
        modality=result["modality"],
        slices=result["slices"],
        preview_urls=result["preview_urls"]
    )
