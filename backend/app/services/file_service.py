import re
import uuid
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List

import nibabel as nib
import numpy as np
from fastapi import UploadFile

from backend.app.config import settings
from backend.app.utils.errors import (
    NeuroVisionException,
    InvalidMRIError,
    FileTooLargeError,
    JobNotFoundError
)
from ai_engine.preprocessing.mri_preprocessor import validate_mri

logger = logging.getLogger("neurovision.file_service")

# UUID validation pattern to prevent path traversal
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE)


class FileService:
    @staticmethod
    def validate_job_id(job_id: str) -> str:
        """Validate that job_id is a valid UUID to protect against path traversal."""
        if not job_id or not UUID_PATTERN.match(job_id.strip()):
            raise JobNotFoundError(f"Invalid job ID format: '{job_id}'")
        return job_id.strip()

    @classmethod
    def get_upload_dir(cls, job_id: str) -> Path:
        clean_id = cls.validate_job_id(job_id)
        path = (settings.uploads_dir / clean_id).resolve()
        # Path traversal guard
        if not str(path).startswith(str(settings.uploads_dir.resolve())):
            raise JobNotFoundError("Invalid upload directory path.")
        return path

    @classmethod
    def get_upload_mri_path(cls, job_id: str) -> Path:
        """Locate the uploaded original MRI file for a given job."""
        upload_dir = cls.get_upload_dir(job_id)
        if not upload_dir.exists() or not upload_dir.is_dir():
            raise JobNotFoundError(f"No upload found for job ID: {job_id}")

        for candidate in ["original_mri.nii.gz", "original_mri.nii"]:
            file_path = upload_dir / candidate
            if file_path.is_file():
                return file_path

        raise JobNotFoundError(f"Original MRI file not found for job ID: {job_id}")

    @classmethod
    def get_upload_metadata(cls, job_id: str) -> Dict[str, Any]:
        """Read saved metadata for an uploaded MRI."""
        upload_dir = cls.get_upload_dir(job_id)
        metadata_file = upload_dir / "metadata.json"
        if not metadata_file.exists():
            raise JobNotFoundError(f"Metadata not found for job ID: {job_id}")

        with metadata_file.open("r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    async def save_and_validate_upload(cls, file: UploadFile) -> Dict[str, Any]:
        """
        Stream uploaded file, enforce size limits, save to dedicated job directory,
        and validate 4D four-modality NIfTI integrity.
        """
        original_filename = file.filename or "unknown.nii.gz"
        lower_name = original_filename.lower()

        # 1. Validate file extension
        if lower_name.endswith(".nii.gz"):
            saved_filename = "original_mri.nii.gz"
        elif lower_name.endswith(".nii"):
            saved_filename = "original_mri.nii"
        else:
            raise NeuroVisionException(
                status_code=400,
                detail="Invalid file format. Only .nii and .nii.gz medical image files are supported."
            )

        # 2. Allocate unique job ID and directory
        job_id = str(uuid.uuid4())
        job_dir = settings.uploads_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        file_path = job_dir / saved_filename

        # 3. Stream upload in chunks to prevent unbounded memory usage
        bytes_read = 0
        chunk_size = 1024 * 1024  # 1 MB chunk
        max_bytes = settings.max_upload_size_bytes

        try:
            with file_path.open("wb") as buffer:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    if bytes_read > max_bytes:
                        raise FileTooLargeError(
                            f"Uploaded file exceeds maximum allowed size of {settings.max_upload_size_mb} MB."
                        )
                    buffer.write(chunk)

            if bytes_read == 0:
                raise InvalidMRIError("Uploaded file is empty (0 bytes).")

            # 4. Validate NIfTI readability and spatial/channel structure
            try:
                nii = nib.load(str(file_path))
                image = nii.get_fdata(dtype=np.float32)
            except Exception as read_err:
                raise InvalidMRIError(f"Corrupt or unreadable NIfTI file: {str(read_err)}")

            # Validate using existing AI engine preprocessor rule
            try:
                validate_mri(image)
            except Exception as val_err:
                raise InvalidMRIError(f"MRI validation failed: {str(val_err)}")

            shape = list(image.shape)
            modalities = int(shape[3])

            # 5. Persist job metadata
            metadata = {
                "job_id": job_id,
                "original_filename": original_filename,
                "saved_filename": saved_filename,
                "file_size_bytes": bytes_read,
                "dimensions": shape,
                "modalities": modalities,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "status": "uploaded"
            }

            metadata_path = job_dir / "metadata.json"
            with metadata_path.open("w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4)

            logger.info("Successfully uploaded and validated MRI for job %s (%s, %d bytes)", job_id, shape, bytes_read)
            return metadata

        except Exception:
            # Clean up on failure so no partial/corrupt files linger
            if job_dir.exists():
                shutil.rmtree(job_dir, ignore_errors=True)
            raise


file_service = FileService()
