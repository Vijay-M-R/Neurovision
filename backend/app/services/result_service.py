import re
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from backend.app.config import settings
from backend.app.utils.errors import (
    JobNotFoundError,
    ResourceNotFoundError
)

logger = logging.getLogger("neurovision.result_service")
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE)


class ResultService:
    @staticmethod
    def validate_job_id(job_id: str) -> str:
        if not job_id or not UUID_PATTERN.match(job_id.strip()):
            raise JobNotFoundError(f"Invalid job ID format: '{job_id}'")
        return job_id.strip()

    @classmethod
    def get_result_dir(cls, job_id: str) -> Path:
        clean_id = cls.validate_job_id(job_id)
        path = (settings.results_dir / clean_id).resolve()
        # Path traversal guard
        if not str(path).startswith(str(settings.results_dir.resolve())):
            raise JobNotFoundError("Invalid result directory path.")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_result_json_path(cls, job_id: str) -> Path:
        result_dir = cls.get_result_dir(job_id)
        # Look for standard result.json or original_mri_result.json
        for candidate in ["result.json", "original_mri_result.json"]:
            path = result_dir / candidate
            if path.is_file():
                return path
        raise ResourceNotFoundError(f"Segmentation results not found for job ID: {job_id}")

    @classmethod
    def load_result(cls, job_id: str) -> Dict[str, Any]:
        result_path = cls.get_result_json_path(job_id)
        with result_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def get_visualization_path(cls, job_id: str) -> Path:
        result_dir = cls.get_result_dir(job_id)
        for candidate in ["comparison.png", "original_mri_orthogonal.png", "orthogonal.png"]:
            path = result_dir / candidate
            if path.is_file():
                return path
        raise ResourceNotFoundError(f"Visualization not found for job ID: {job_id}")

    @classmethod
    def get_mask_path(cls, job_id: str, region: str) -> Path:
        region_clean = region.strip().upper()
        if region_clean not in ["WT", "TC", "ET"]:
            raise ResourceNotFoundError(f"Unsupported mask region: '{region}'. Supported regions: WT, TC, ET")

        result_dir = cls.get_result_dir(job_id)
        for candidate in [f"{region_clean}.nii.gz", f"original_mri_{region_clean}.nii.gz"]:
            path = result_dir / candidate
            if path.is_file():
                return path
        raise ResourceNotFoundError(f"Mask '{region_clean}' not found for job ID: {job_id}")

    @classmethod
    def get_enhanced_preview_path(cls, job_id: str, view: str) -> Path:
        view_clean = view.strip().lower()
        if view_clean not in ["axial", "coronal", "sagittal"]:
            raise ResourceNotFoundError(f"Unsupported view: '{view}'. Supported: axial, coronal, sagittal")

        result_dir = cls.get_result_dir(job_id)
        for candidate in [f"{view_clean}_enhanced.png", f"original_mri_{view_clean}_enhanced.png"]:
            path = result_dir / candidate
            if path.is_file():
                return path
        raise ResourceNotFoundError(f"Enhanced preview for '{view_clean}' not found for job ID: {job_id}")

    @classmethod
    def standardize_job_artifacts(cls, job_id: str, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Organize and alias pipeline outputs to the canonical backend storage schema:
        prediction.nii.gz, WT.nii.gz, TC.nii.gz, ET.nii.gz, comparison.png, result.json
        """
        result_dir = cls.get_result_dir(job_id)
        seg = pipeline_result["segmentation"]

        # Alias combined prediction
        src_pred = Path(seg["prediction_path"])
        dst_pred = result_dir / "prediction.nii.gz"
        if src_pred.is_file() and not dst_pred.is_file():
            shutil.copyfile(src_pred, dst_pred)

        # Alias individual masks
        for region in ["WT", "TC", "ET"]:
            if region in seg["mask_paths"]:
                src_mask = Path(seg["mask_paths"][region])
                dst_mask = result_dir / f"{region}.nii.gz"
                if src_mask.is_file() and not dst_mask.is_file():
                    shutil.copyfile(src_mask, dst_mask)

        # Alias visualization
        if pipeline_result.get("visualization"):
            src_vis = Path(pipeline_result["visualization"]["visualization_path"])
            dst_vis = result_dir / "comparison.png"
            if src_vis.is_file() and not dst_vis.is_file():
                shutil.copyfile(src_vis, dst_vis)

        # Standardize result.json
        src_json = Path(pipeline_result["result_json"])
        dst_json = result_dir / "result.json"
        
        # Load, augment with job_id and URLs, and save canonical result.json
        with src_json.open("r", encoding="utf-8") as f:
            record = json.load(f)

        record["job_id"] = job_id
        record["urls"] = {
            "results": f"/api/results/{job_id}",
            "visualization": f"/api/results/{job_id}/visualization",
            "masks": {
                "WT": f"/api/results/{job_id}/masks/WT",
                "TC": f"/api/results/{job_id}/masks/TC",
                "ET": f"/api/results/{job_id}/masks/ET"
            },
            "download": f"/api/results/{job_id}/download"
        }

        with dst_json.open("w", encoding="utf-8") as f:
            json.dump(record, f, indent=4)

        return record


result_service = ResultService()
