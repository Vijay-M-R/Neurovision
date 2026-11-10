
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.patches import Patch


def load_volume(path):
    """Load a NIfTI volume."""
    nii = nib.load(str(path))
    return nii.get_fdata(dtype=np.float32), nii


def create_mri_visualization(
    mri_path,
    prediction_path,
    output_path,
    ground_truth_path=None,
    slice_indices=None
):
    """
    Create a 3x3 MRI comparison:
    Row 1: Original FLAIR
    Row 2: Ground Truth
    Row 3: AI Prediction

    Display classes:
    0 = Background
    1 = Whole Tumor outside Core
    2 = Tumor Core
    3 = Enhancing Tumor
    """

    mri, mri_nii = load_volume(mri_path)
    prediction, pred_nii = load_volume(prediction_path)

    if mri.ndim != 4 or mri.shape[3] != 4:
        raise ValueError("Expected a four-modality MRI.")

    if prediction.ndim != 3:
        raise ValueError("Prediction must be a 3D volume.")

    if mri.shape[:3] != prediction.shape:
        raise ValueError("MRI and prediction dimensions differ.")

    if not np.allclose(mri_nii.affine, pred_nii.affine):
        raise ValueError("MRI and prediction are not aligned.")

    ground_truth = None

    if ground_truth_path is not None:
        ground_truth, gt_nii = load_volume(ground_truth_path)

        if ground_truth.shape != prediction.shape:
            raise ValueError("Ground truth dimensions differ.")

        if not np.allclose(gt_nii.affine, pred_nii.affine):
            raise ValueError("Ground truth is not aligned.")

        if not np.all(np.isin(np.unique(ground_truth), [0, 1, 2, 3])):
            raise ValueError("Unexpected ground truth labels.")

    if not np.all(np.isin(np.unique(prediction), [0, 1, 2, 4])):
        raise ValueError("Unexpected prediction labels.")

    # Original FLAIR modality
    flair = mri[:, :, :, 0]

    # Select slices containing the most predicted tumor.
    if slice_indices is None:
        axial = int(np.argmax(
            np.count_nonzero(prediction, axis=(0, 1))
        ))
        coronal = int(np.argmax(
            np.count_nonzero(prediction, axis=(0, 2))
        ))
        sagittal = int(np.argmax(
            np.count_nonzero(prediction, axis=(1, 2))
        ))
    else:
        axial = int(slice_indices["axial"])
        coronal = int(slice_indices["coronal"])
        sagittal = int(slice_indices["sagittal"])

    if not (0 <= axial < flair.shape[2]):
        raise ValueError("Axial slice index out of range.")

    if not (0 <= coronal < flair.shape[1]):
        raise ValueError("Coronal slice index out of range.")

    if not (0 <= sagittal < flair.shape[0]):
        raise ValueError("Sagittal slice index out of range.")

    # Convert prediction labels to display classes.
    # Prediction: 2 = WT-only, 1 = TC, 4 = ET
    pred_display = np.zeros_like(prediction, dtype=np.uint8)
    pred_display[prediction == 2] = 1
    pred_display[prediction == 1] = 2
    pred_display[prediction == 4] = 3

    # Convert ground truth labels to matching display classes.
    # Ground truth: 1 = edema, 2 = non-enhancing, 3 = enhancing
    gt_display = None

    if ground_truth is not None:
        gt_display = ground_truth.astype(np.uint8)

    # Consistent colors for both overlays.
    colors = ["#00D5FF", "#FFD43B", "#FF4B4B"]

    cmap = plt.matplotlib.colors.ListedColormap(colors)
    cmap.set_bad(alpha=0)

    views = [
        ("Axial", lambda volume: volume[:, :, axial]),
        ("Coronal", lambda volume: volume[:, coronal, :]),
        ("Sagittal", lambda volume: volume[sagittal, :, :])
    ]

    rows = 3 if ground_truth is not None else 2

    fig, axes = plt.subplots(
        rows, 3,
        figsize=(17, 11),
        facecolor="#151922"
    )

    axes = np.atleast_2d(axes)

    for column, (name, extractor) in enumerate(views):

        image = extractor(flair)

        axes[0, column].imshow(
            np.rot90(image),
            cmap="gray"
        )

        axes[0, column].set_title(
            f"{name} - Original FLAIR",
            color="white",
            fontsize=12,
            fontweight="bold"
        )

        if ground_truth is not None:
            gt_slice = extractor(gt_display)

            gt_overlay = np.ma.masked_where(
                gt_slice == 0, gt_slice
            )

            axes[1, column].imshow(
                np.rot90(image),
                cmap="gray"
            )

            axes[1, column].imshow(
                np.rot90(gt_overlay),
                cmap=cmap,
                vmin=1,
                vmax=3,
                alpha=0.65,
                interpolation="nearest"
            )

            axes[1, column].set_title(
                f"{name} - Ground Truth",
                color="white",
                fontsize=12,
                fontweight="bold"
            )

            prediction_row = 2

        else:
            prediction_row = 1

        pred_slice = extractor(pred_display)

        pred_overlay = np.ma.masked_where(
            pred_slice == 0, pred_slice
        )

        axes[prediction_row, column].imshow(
            np.rot90(image),
            cmap="gray"
        )

        axes[prediction_row, column].imshow(
            np.rot90(pred_overlay),
            cmap=cmap,
            vmin=1,
            vmax=3,
            alpha=0.65,
            interpolation="nearest"
        )

        axes[prediction_row, column].set_title(
            f"{name} - AI Prediction",
            color="white",
            fontsize=12,
            fontweight="bold"
        )

    for ax in axes.flat:
        ax.axis("off")
        ax.set_facecolor("#151922")

    legend_items = [
        Patch(facecolor=colors[0], label="WT - Whole Tumor"),
        Patch(facecolor=colors[1], label="TC - Tumor Core"),
        Patch(facecolor=colors[2], label="ET - Enhancing Tumor")
    ]

    fig.legend(
        handles=legend_items,
        loc="lower center",
        ncol=3,
        frameon=False,
        labelcolor="white",
        fontsize=11
    )

    fig.suptitle(
        "NEUROVISION | MRI SEGMENTATION ANALYSIS",
        fontsize=19,
        fontweight="bold",
        color="white",
        y=0.98
    )

    plt.tight_layout(rect=[0, 0.08, 1, 0.94])

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(
        output_path,
        dpi=250,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )

    plt.close(fig)

    return {
        "visualization_path": str(output_path),
        "slices": {
            "axial": axial,
            "coronal": coronal,
            "sagittal": sagittal
        },
        "ground_truth_available": ground_truth is not None,
        "layout": f"{rows}x3"
    }
