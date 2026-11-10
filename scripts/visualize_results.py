
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.colors import ListedColormap

# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

MRI_PATH = ROOT / "Task01_BrainTumour" / "imagesTr" / "BRATS_001.nii.gz"

GT_PATH = ROOT / "Task01_BrainTumour" / "labelsTr" / "BRATS_001.nii.gz"

PRED_PATH = ROOT / "outputs" / "BRATS_001_prediction.nii.gz"

OUTPUT_PATH = ROOT / "outputs" / "BRATS_001_comparison.png"

# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------

print("Loading MRI and segmentation files...")

mri_nii = nib.load(str(MRI_PATH))
gt_nii = nib.load(str(GT_PATH))
pred_nii = nib.load(str(PRED_PATH))

mri = mri_nii.get_fdata(dtype=np.float32)
ground_truth = gt_nii.get_fdata().astype(np.uint8)
prediction = pred_nii.get_fdata().astype(np.uint8)

# Dataset channel 0 = FLAIR
flair = mri[:, :, :, 0]

if flair.shape != ground_truth.shape or flair.shape != prediction.shape:
    raise ValueError("MRI and segmentation dimensions do not match.")

# --------------------------------------------------
# 3. SELECT A REPRESENTATIVE AXIAL SLICE
# --------------------------------------------------

# Select the slice containing the largest ground-truth
# tumor area, rather than choosing an arbitrary slice.

tumor_area = np.count_nonzero(ground_truth, axis=(0, 1))
slice_index = int(np.argmax(tumor_area))

print("Selected MRI slice:", slice_index)

mri_slice = flair[:, :, slice_index]
gt_slice = ground_truth[:, :, slice_index]
pred_slice = prediction[:, :, slice_index]

# Rotate for a conventional axial display orientation.
mri_slice = np.rot90(mri_slice)
gt_slice = np.rot90(gt_slice)
pred_slice = np.rot90(pred_slice)

# --------------------------------------------------
# 4. PREPARE SEGMENTATION COLORS
# --------------------------------------------------

# Ground truth:
# 0 = Background
# 1 = Edema
# 2 = Non-enhancing tumor
# 3 = Enhancing tumor

gt_colors = ListedColormap([
    "black",
    "lime",
    "yellow",
    "red"
])

# Prediction:
# 0 = Background
# 1 = Tumor core
# 2 = Whole tumor outside core
# 4 = Enhancing tumor

pred_display = np.zeros_like(pred_slice, dtype=np.uint8)
pred_display[pred_slice == 2] = 1
pred_display[pred_slice == 1] = 2
pred_display[pred_slice == 4] = 3

pred_colors = ListedColormap([
    "black",
    "lime",
    "yellow",
    "red"
])

# --------------------------------------------------
# 5. CREATE THREE-PANEL VISUALIZATION
# --------------------------------------------------

fig, axes = plt.subplots(
    1,
    3,
    figsize=(18, 6)
)

fig.suptitle(
    "NEUROVISION - Brain Tumor Segmentation",
    fontsize=17,
    fontweight="bold"
)

# Original MRI
axes[0].imshow(
    mri_slice,
    cmap="gray"
)

axes[0].set_title("Original FLAIR MRI")

# Ground truth
axes[1].imshow(
    mri_slice,
    cmap="gray"
)

axes[1].imshow(
    gt_slice,
    cmap=gt_colors,
    alpha=0.45,
    vmin=0,
    vmax=3
)

axes[1].set_title("Ground Truth Segmentation")

# Prediction
axes[2].imshow(
    mri_slice,
    cmap="gray"
)

axes[2].imshow(
    pred_display,
    cmap=pred_colors,
    alpha=0.45,
    vmin=0,
    vmax=3
)

axes[2].set_title("NeuroVision Prediction")

for ax in axes:
    ax.axis("off")

# --------------------------------------------------
# 6. ADD LEGEND
# --------------------------------------------------

from matplotlib.patches import Patch

legend_items = [
    Patch(facecolor="lime", label="Edema / WT outside core"),
    Patch(facecolor="yellow", label="Non-enhancing tumor / TC"),
    Patch(facecolor="red", label="Enhancing tumor / ET")
]

fig.legend(
    handles=legend_items,
    loc="lower center",
    ncol=3,
    frameon=False
)

plt.tight_layout(rect=[0, 0.12, 1, 0.92])

# --------------------------------------------------
# 7. SAVE IMAGE
# --------------------------------------------------

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

plt.savefig(
    OUTPUT_PATH,
    dpi=300,
    bbox_inches="tight"
)

print("\nVisualization completed.")
print("Selected slice:", slice_index)
print("Saved image:", OUTPUT_PATH)

plt.show()
