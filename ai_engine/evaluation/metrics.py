
import nibabel as nib
import numpy as np

from pathlib import Path


def calculate_metrics(prediction, ground_truth):
    """Calculate binary segmentation metrics."""

    prediction = np.asarray(prediction, dtype=bool)
    ground_truth = np.asarray(ground_truth, dtype=bool)

    if prediction.shape != ground_truth.shape:
        raise ValueError("Prediction and ground truth shapes differ.")

    tp = int(np.count_nonzero(prediction & ground_truth))
    fp = int(np.count_nonzero(prediction & ~ground_truth))
    fn = int(np.count_nonzero(~prediction & ground_truth))
    tn = int(np.count_nonzero(~prediction & ~ground_truth))

    dice_denominator = 2 * tp + fp + fn
    union = tp + fp + fn

    return {
        "dice": 2 * tp / dice_denominator if dice_denominator else 1.0,
        "iou": tp / union if union else 1.0,
        "precision": tp / (tp + fp) if (tp + fp) else 1.0,
        "recall": tp / (tp + fn) if (tp + fn) else 1.0,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn
    }


def load_segmentation(path, allowed_labels, name):
    """Load and validate a segmentation NIfTI file."""

    path = Path(path)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"{name} file not found: {path}")

    if not (
        path.name.lower().endswith(".nii")
        or path.name.lower().endswith(".nii.gz")
    ):
        raise ValueError(f"{name} must be a NIfTI file.")

    try:
        nii = nib.load(str(path))
        data = nii.get_fdata(dtype=np.float32)
    except Exception as error:
        raise ValueError(
            f"Unable to read {name}: {error}"
        ) from error

    if data.ndim != 3:
        raise ValueError(f"{name} must be a 3D volume.")

    if not np.isfinite(data).all():
        raise ValueError(f"{name} contains invalid values.")

    if not np.allclose(data, np.round(data)):
        raise ValueError(f"{name} contains non-integer labels.")

    labels = np.unique(data)

    if not np.isin(labels, allowed_labels).all():
        raise ValueError(
            f"{name} contains unexpected labels: {labels.tolist()}"
        )

    return data.astype(np.uint8), nii


def evaluate_segmentation(prediction_path, ground_truth_path):
    """
    Evaluate WT, TC and ET against BraTS-style ground truth.

    Prediction:
    0 = Background
    1 = Tumor Core
    2 = Whole Tumor outside Core
    4 = Enhancing Tumor

    Ground truth:
    0 = Background
    1 = Edema
    2 = Non-enhancing tumor
    3 = Enhancing tumor
    """

    prediction, pred_nii = load_segmentation(
        prediction_path, [0, 1, 2, 4], "Prediction"
    )

    ground_truth, gt_nii = load_segmentation(
        ground_truth_path, [0, 1, 2, 3], "Ground truth"
    )

    if prediction.shape != ground_truth.shape:
        raise ValueError("Segmentation dimensions do not match.")

    if not np.allclose(pred_nii.affine, gt_nii.affine):
        raise ValueError("Prediction and ground truth are not aligned.")

    regions = {
        "WT": (
            np.isin(prediction, [1, 2, 4]),
            np.isin(ground_truth, [1, 2, 3])
        ),
        "TC": (
            np.isin(prediction, [1, 4]),
            np.isin(ground_truth, [2, 3])
        ),
        "ET": (
            prediction == 4,
            ground_truth == 3
        )
    }

    return {
        region: calculate_metrics(pred_mask, gt_mask)
        for region, (pred_mask, gt_mask) in regions.items()
    }
