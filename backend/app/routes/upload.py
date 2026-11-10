from fastapi import APIRouter, UploadFile, File
from backend.app.schemas.response import UploadResponse
from backend.app.services.file_service import file_service

router = APIRouter(prefix="/api", tags=["Upload"])


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_mri(file: UploadFile = File(..., description="4D NIfTI brain MRI file (.nii or .nii.gz)")):
    """
    Upload and validate a 4-modality brain MRI volume (FLAIR, T1, T1ce, T2).
    Generates a secure UUID job ID and creates isolated storage.
    """
    metadata = await file_service.save_and_validate_upload(file)
    
    return UploadResponse(
        job_id=metadata["job_id"],
        status=metadata["status"],
        filename=metadata["saved_filename"],
        file_size_bytes=metadata["file_size_bytes"],
        dimensions=metadata["dimensions"],
        modalities=metadata["modalities"],
        message="MRI uploaded and verified successfully."
    )
