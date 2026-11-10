from fastapi import APIRouter, Path as FastApiPath
from backend.app.schemas.response import SegmentResponse, RegionVoxelCounts
from backend.app.schemas.request import SegmentRequest
from backend.app.services.ai_service import ai_service
from backend.app.services.file_service import file_service

router = APIRouter(prefix="/api", tags=["Segmentation"])


@router.post("/segment/{job_id}", response_model=SegmentResponse)
async def segment_mri(
    job_id: str = FastApiPath(..., description="UUID job ID of previously uploaded MRI"),
    body: SegmentRequest = SegmentRequest()
):
    """
    Run multi-region brain tumor segmentation on the uploaded MRI using the pretrained SegResNet.
    Serialized on GPU to protect VRAM. Returns status, region voxel counts, and artifact URLs.
    """
    file_service.validate_job_id(job_id)
    record = await ai_service.run_segmentation(
        job_id=job_id,
        generate_visualization=body.generate_visualization
    )

    regions_data = record.get("region_voxels", {"WT": 0, "TC": 0, "ET": 0})
    eval_metrics = record.get("evaluation_metrics")

    return SegmentResponse(
        job_id=job_id,
        status="completed",
        model=record.get("model", "MONAI SegResNet"),
        device=record.get("device", "cuda"),
        processing_time_seconds=float(record.get("processing_time_seconds", 0.0)),
        regions=RegionVoxelCounts(
            WT=regions_data.get("WT", 0),
            TC=regions_data.get("TC", 0),
            ET=regions_data.get("ET", 0)
        ),
        tumor_voxels=int(record.get("tumor_voxels", 0)),
        dimensions=record.get("shape", [240, 240, 155]),
        visualization_url=f"/api/results/{job_id}/visualization",
        results_url=f"/api/results/{job_id}",
        download_url=f"/api/results/{job_id}/download",
        evaluation_available=eval_metrics is not None,
        evaluation_message="Ground truth unavailable. Evaluation metrics cannot be calculated." if eval_metrics is None else None
    )
