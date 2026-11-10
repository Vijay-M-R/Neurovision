
from pathlib import Path

from ai_engine.inference.segmentation import segment_mri
from ai_engine.evaluation.metrics import evaluate_segmentation
from ai_engine.visualization.mri_viewer import create_mri_visualization
from ai_engine.results.result_manager import save_result


def run_pipeline(
    mri_path,
    ground_truth_path=None,
    output_dir=None,
    generate_visualization=True
):
    """
    Run the complete NeuroVision AI pipeline.

    Training and fine-tuning are not performed.
    Ground truth is optional and used only for evaluation.
    """

    mri_path = Path(mri_path)

    if not mri_path.exists():
        raise FileNotFoundError(f"MRI file not found: {mri_path}")

    if ground_truth_path is not None:
        ground_truth_path = Path(ground_truth_path)

        if not ground_truth_path.exists():
            raise FileNotFoundError(
                f"Ground truth file not found: {ground_truth_path}"
            )

    if output_dir is None:
        output_dir = Path(__file__).resolve().parents[1] / "outputs"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Run pretrained tumor segmentation
    segmentation_result = segment_mri(
        mri_path=str(mri_path),
        output_dir=str(output_dir)
    )

    # 2. Evaluate only when ground truth is available
    evaluation_metrics = None

    if ground_truth_path is not None:
        evaluation_metrics = evaluate_segmentation(
            segmentation_result["prediction_path"],
            str(ground_truth_path)
        )

    # 3. Generate visualization
    visualization_result = None

    if generate_visualization:
        patient_id = segmentation_result["patient_id"]

        visualization_path = (
            output_dir / f"{patient_id}_orthogonal.png"
        )

        visualization_result = create_mri_visualization(
            mri_path=str(mri_path),
            prediction_path=segmentation_result["prediction_path"],
            output_path=str(visualization_path),
            ground_truth_path=(
                str(ground_truth_path)
                if ground_truth_path is not None
                else None
            )
        )

    # 4. Save complete pipeline result
    saved_result = save_result(
        segmentation_result=segmentation_result,
        evaluation_metrics=evaluation_metrics,
        visualization_result=visualization_result,
        output_dir=str(output_dir)
    )

    return {
        "status": "completed",
        "patient_id": segmentation_result["patient_id"],
        "segmentation": segmentation_result,
        "evaluation": evaluation_metrics,
        "visualization": visualization_result,
        "result_json": saved_result["result_path"]
    }
