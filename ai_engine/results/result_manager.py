
import json
from pathlib import Path
from datetime import datetime, timezone


def save_result(
    segmentation_result,
    evaluation_metrics=None,
    visualization_result=None,
    output_dir=None
):
    """Save structured NeuroVision results as JSON."""

    root = Path(__file__).resolve().parents[2]

    if output_dir is None:
        output_dir = root / "outputs"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "project": "NeuroVision",
        "patient_id": segmentation_result["patient_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": segmentation_result["status"],
        "model": segmentation_result["model"],
        "device": segmentation_result["device"],
        "processing_time_seconds":
            segmentation_result["processing_time_seconds"],
        "prediction_path":
            segmentation_result["prediction_path"],
        "mask_paths":
            segmentation_result["mask_paths"],
        "shape": segmentation_result["shape"],
        "tumor_voxels": segmentation_result["tumor_voxels"],
        "region_voxels": segmentation_result["region_voxels"],
        "evaluation_metrics": evaluation_metrics,
        "visualization": visualization_result
    }

    result_path = output_dir / (
        f"{segmentation_result['patient_id']}_result.json"
    )

    with result_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    return {
        "result_path": str(result_path),
        "result": result
    }


def load_result(result_path):
    """Load a previously saved NeuroVision result."""

    path = Path(result_path)

    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
