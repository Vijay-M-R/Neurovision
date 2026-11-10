import io
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Path as FastApiPath
from fastapi.responses import FileResponse, StreamingResponse

from backend.app.services.result_service import result_service
from backend.app.services.file_service import file_service
from backend.app.utils.errors import ResourceNotFoundError

router = APIRouter(prefix="/api/results", tags=["Results & Downloads"])


@router.get("/{job_id}")
async def get_results(
    job_id: str = FastApiPath(..., description="UUID job ID")
):
    """
    Retrieve stored analysis results and metadata as JSON.
    Local paths are masked and translated into secure API endpoints.
    """
    file_service.validate_job_id(job_id)
    return result_service.load_result(job_id)


@router.get("/{job_id}/visualization")
async def get_visualization(
    job_id: str = FastApiPath(..., description="UUID job ID")
):
    """
    Retrieve the generated 3x3 orthogonal comparison PNG image.
    """
    file_service.validate_job_id(job_id)
    vis_path = result_service.get_visualization_path(job_id)
    return FileResponse(
        path=str(vis_path),
        media_type="image/png",
        filename=f"neurovision_{job_id}_visualization.png"
    )


@router.get("/{job_id}/masks/{region}")
async def get_individual_mask(
    job_id: str = FastApiPath(..., description="UUID job ID"),
    region: str = FastApiPath(..., description="Tumor region mask: WT, TC, or ET")
):
    """
    Retrieve an individual binary mask volume (NIfTI format).
    Supported regions:
    - WT (Whole Tumor)
    - TC (Tumor Core)
    - ET (Enhancing Tumor)
    """
    file_service.validate_job_id(job_id)
    region_clean = region.strip().upper()
    mask_path = result_service.get_mask_path(job_id, region_clean)
    
    return FileResponse(
        path=str(mask_path),
        media_type="application/gzip",
        filename=f"{job_id}_{region_clean}.nii.gz"
    )


@router.get("/{job_id}/previews/{view}")
async def get_enhanced_preview(
    job_id: str = FastApiPath(..., description="UUID job ID"),
    view: str = FastApiPath(..., description="Preview slice view: axial, coronal, or sagittal")
):
    """
    Retrieve a CLAHE contrast-enhanced slice preview image (PNG).
    """
    file_service.validate_job_id(job_id)
    preview_path = result_service.get_enhanced_preview_path(job_id, view)
    return FileResponse(
        path=str(preview_path),
        media_type="image/png",
        filename=f"{job_id}_{view.lower()}_enhanced.png"
    )


@router.get("/{job_id}/download")
async def download_results_bundle(
    job_id: str = FastApiPath(..., description="UUID job ID")
):
    """
    Download a structured ZIP archive containing all available analysis artifacts:
    - Combined prediction (prediction.nii.gz)
    - Individual masks (WT.nii.gz, TC.nii.gz, ET.nii.gz)
    - Orthogonal visualization (comparison.png)
    - Enhanced previews (if generated)
    - Analysis metadata JSON (result.json)
    """
    file_service.validate_job_id(job_id)
    result_dir = result_service.get_result_dir(job_id)
    
    if not (result_dir / "result.json").is_file() and not (result_dir / "original_mri_result.json").is_file():
        raise ResourceNotFoundError(f"No results available to download for job ID: {job_id}")

    # Build in-memory ZIP bundle
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Include all files under results/{job_id}
        for item in result_dir.iterdir():
            if item.is_file():
                # Store with clean archive names
                zf.write(item, arcname=item.name)

    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=neurovision_results_{job_id}.zip"
        }
    )
