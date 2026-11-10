import asyncio
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

import torch
from starlette.concurrency import run_in_threadpool

from backend.app.services.file_service import file_service
from backend.app.services.result_service import result_service
from backend.app.utils.errors import (
    NeuroVisionException,
    GPUOutOfMemoryError,
    JobNotFoundError
)
from ai_engine.pipeline import run_pipeline
from ai_engine.enhancement.enhancement import export_enhanced_mri_previews

logger = logging.getLogger("neurovision.ai_service")


class AIService:
    def __init__(self):
        # Global asynchronous lock to serialize GPU inference requests
        self._gpu_lock = asyncio.Lock()

    async def run_segmentation(
        self,
        job_id: str,
        ground_truth_path: Optional[str] = None,
        generate_visualization: bool = True
    ) -> Dict[str, Any]:
        """
        Execute full SegResNet inference through the existing AI pipeline.
        Serialized by an asyncio lock to protect 6 GB VRAM.
        Non-blocking execution via run_in_threadpool.
        """
        # Validate upload existence
        mri_path = file_service.get_upload_mri_path(job_id)
        result_dir = result_service.get_result_dir(job_id)

        logger.info("Queuing segmentation inference for job %s (waiting for GPU lock)...", job_id)

        async with self._gpu_lock:
            logger.info("Acquired GPU lock for job %s. Starting inference...", job_id)
            try:
                pipeline_result = await run_in_threadpool(
                    run_pipeline,
                    mri_path=str(mri_path),
                    ground_truth_path=str(ground_truth_path) if ground_truth_path else None,
                    output_dir=str(result_dir),
                    generate_visualization=generate_visualization
                )
            except torch.cuda.OutOfMemoryError as oom_err:
                logger.error("CUDA Out of Memory during inference for job %s: %s", job_id, oom_err)
                torch.cuda.empty_cache()
                raise GPUOutOfMemoryError(
                    "CUDA out of memory during MRI segmentation. Please retry when GPU memory is freed."
                ) from oom_err
            except Exception as exc:
                logger.exception("Inference failed for job %s: %s", job_id, exc)
                raise NeuroVisionException(
                    status_code=500,
                    detail=f"MRI segmentation failed: {str(exc)}"
                ) from exc

        logger.info("Segmentation inference completed for job %s. Standardizing artifacts...", job_id)
        standardized_record = result_service.standardize_job_artifacts(job_id, pipeline_result)
        return standardized_record

    async def run_enhancement(
        self,
        job_id: str,
        modality: int = 0,
        clip_limit: float = 2.0,
        slice_indices: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Generate CLAHE contrast enhancement previews without touching original MRI or running segmentation.
        """
        mri_path = file_service.get_upload_mri_path(job_id)
        result_dir = result_service.get_result_dir(job_id)

        try:
            enhancement_result = await run_in_threadpool(
                export_enhanced_mri_previews,
                mri_path=str(mri_path),
                output_dir=str(result_dir),
                modality=modality,
                clip_limit=clip_limit,
                slice_indices=slice_indices
            )
        except Exception as exc:
            logger.exception("Enhancement failed for job %s: %s", job_id, exc)
            raise NeuroVisionException(
                status_code=500,
                detail=f"MRI contrast enhancement failed: {str(exc)}"
            ) from exc

        # Alias preview files to canonical names (e.g., axial_enhanced.png)
        for view, file_path_str in enhancement_result.get("enhanced_previews", {}).items():
            src = Path(file_path_str)
            dst = result_dir / f"{view}_enhanced.png"
            if src.is_file() and not dst.is_file():
                shutil.copyfile(src, dst)

        preview_urls = {
            view: f"/api/results/{job_id}/previews/{view}"
            for view in ["axial", "coronal", "sagittal"]
        }

        return {
            "job_id": job_id,
            "status": "completed",
            "modality": enhancement_result["modality"],
            "slices": enhancement_result["slices"],
            "preview_urls": preview_urls
        }


ai_service = AIService()
