
import time
import numpy as np
import nibabel as nib
import torch

from pathlib import Path
from monai.inferers import SlidingWindowInferer

from ai_engine.model.loader import load_model
from ai_engine.preprocessing.mri_preprocessor import prepare_mri


def segment_mri(
    mri_path,
    output_dir=None,
    roi_size=(240, 240, 160),
    overlap=0.5
):
    """
    Run pretrained MONAI SegResNet inference.

    Prediction labels:
    0 = Background
    1 = Tumor Core
    2 = Whole Tumor outside Core
    4 = Enhancing Tumor

    No training or fine-tuning is performed.
    """

    start_time = time.perf_counter()
    mri_path = Path(mri_path)

    if not mri_path.exists() or not mri_path.is_file():
        raise FileNotFoundError(f"MRI file not found: {mri_path}")

    if not isinstance(overlap, (int, float)) or not 0 <= overlap < 1:
        raise ValueError("Overlap must be between 0 and 1.")

    if len(roi_size) != 3 or any(
        not isinstance(x, int) or x <= 0 for x in roi_size
    ):
        raise ValueError("roi_size must contain three positive integers.")

    if output_dir is None:
        root = Path(__file__).resolve().parents[2]
        output_dir = root / "outputs"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load cached pretrained model.
    model, device = load_model()

    # Validate and prepare MRI.
    prepared = prepare_mri(mri_path, device)
    image_tensor = prepared["image"]

    inferer = SlidingWindowInferer(
        roi_size=roi_size,
        sw_batch_size=1,
        overlap=overlap
    )

    try:
        with torch.inference_mode():

            if device.type == "cuda":
                with torch.autocast(
                    device_type="cuda",
                    dtype=torch.float16
                ):
                    logits = inferer(image_tensor, model)
            else:
                logits = inferer(image_tensor, model)

            probabilities = torch.sigmoid(logits)

            if not torch.isfinite(probabilities).all():
                raise RuntimeError("Model produced invalid predictions.")

            channels = probabilities[0] >= 0.5

            # Model output channels:
            # 0 = TC, 1 = WT, 2 = ET
            tc = channels[0].cpu().numpy()
            wt = channels[1].cpu().numpy()
            et = channels[2].cpu().numpy()

        # Combined label map.
        prediction = np.zeros(wt.shape, dtype=np.uint8)
        prediction[wt] = 2
        prediction[tc] = 1
        prediction[et] = 4

        patient_id = (
            mri_path.name[:-7]
            if mri_path.name.lower().endswith(".nii.gz")
            else mri_path.stem
        )

        header = prepared["header"].copy()
        header.set_data_dtype(np.uint8)

        combined_path = output_dir / f"{patient_id}_prediction.nii.gz"

        nib.save(
            nib.Nifti1Image(
                prediction,
                prepared["affine"],
                header
            ),
            str(combined_path)
        )

        masks = {
            "WT": wt.astype(np.uint8),
            "TC": tc.astype(np.uint8),
            "ET": et.astype(np.uint8)
        }

        mask_paths = {}

        for name, mask in masks.items():
            mask_path = output_dir / f"{patient_id}_{name}.nii.gz"

            nib.save(
                nib.Nifti1Image(
                    mask,
                    prepared["affine"],
                    header
                ),
                str(mask_path)
            )

            mask_paths[name] = str(mask_path)

        elapsed = time.perf_counter() - start_time

        return {
            "patient_id": patient_id,
            "status": "completed",
            "model": "MONAI SegResNet",
            "device": str(device),
            "processing_time_seconds": round(elapsed, 2),
            "prediction_path": str(combined_path),
            "mask_paths": mask_paths,
            "shape": list(prediction.shape),
            "labels": np.unique(prediction).tolist(),
            "tumor_voxels": int(np.count_nonzero(prediction)),
            "region_voxels": {
                "WT": int(np.count_nonzero(wt)),
                "TC": int(np.count_nonzero(tc)),
                "ET": int(np.count_nonzero(et))
            }
        }

    finally:
        if device.type == "cuda":
            torch.cuda.empty_cache()
