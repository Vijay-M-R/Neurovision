
import nibabel as nib
import numpy as np

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PRED_PATH = ROOT / "outputs" / "BRATS_001_prediction.nii.gz"
GT_PATH = ROOT / "Task01_BrainTumour" / "labelsTr" / "BRATS_001.nii.gz"

# Load prediction and ground truth
prediction = nib.load(str(PRED_PATH)).get_fdata().astype(np.uint8)
ground_truth = nib.load(str(GT_PATH)).get_fdata().astype(np.uint8)

# Verify spatial alignment
if prediction.shape != ground_truth.shape:
    raise ValueError("Prediction and ground truth shapes differ.")

# Define equivalent tumor regions
regions = {
    "Whole Tumor": (
        np.isin(prediction, [1, 2, 4]),
        np.isin(ground_truth, [1, 2, 3])
    ),
    "Tumor Core": (
        np.isin(prediction, [1, 4]),
        np.isin(ground_truth, [2, 3])
    ),
    "Enhancing Tumor": (
        prediction == 4,
        ground_truth == 3
    )
}

print("\nNEUROVISION SEGMENTATION EVALUATION")
print("=" * 75)

print(
    "{:<22} {:>10} {:>10} {:>12} {:>10}".format(
        "Region", "Dice", "IoU", "Precision", "Recall"
    )
)

print("-" * 75)

for name, (pred, true) in regions.items():

    tp = np.count_nonzero(pred & true)
    fp = np.count_nonzero(pred & ~true)
    fn = np.count_nonzero(~pred & true)

    dice = (2 * tp) / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0
    iou = tp / (tp + fp + fn) if (tp + fp + fn) else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0

    print(
        "{:<22} {:>10.4f} {:>10.4f} {:>12.4f} {:>10.4f}".format(
            name, dice, iou, precision, recall
        )
    )

print("=" * 75)
print("Evaluation completed for BRATS_001.")
