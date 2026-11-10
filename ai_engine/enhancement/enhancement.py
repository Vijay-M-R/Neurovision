
import cv2
import nibabel as nib
import numpy as np

from pathlib import Path


def enhance_mri_slice(
    image,
    clip_limit=2.0,
    tile_grid_size=(8, 8)
):
    """Enhance one MRI slice using CLAHE."""

    image = np.asarray(image, dtype=np.float32)

    if image.ndim != 2:
        raise ValueError("Expected a 2D MRI slice.")

    if not np.isfinite(image).all():
        raise ValueError("MRI contains invalid values.")

    if clip_limit <= 0:
        raise ValueError("clip_limit must be positive.")

    nonzero = image != 0

    if not np.any(nonzero):
        return np.zeros(image.shape, dtype=np.uint8)

    low, high = np.percentile(image[nonzero], [1, 99])

    if high <= low:
        return np.zeros(image.shape, dtype=np.uint8)

    normalized = np.zeros(image.shape, dtype=np.uint8)

    scaled = np.clip((image - low) / (high - low), 0, 1)

    normalized[nonzero] = (
        scaled[nonzero] * 255
    ).astype(np.uint8)

    clahe = cv2.createCLAHE(
        clipLimit=clip_limit,
        tileGridSize=tile_grid_size
    )

    enhanced = clahe.apply(normalized)
    enhanced[~nonzero] = 0

    return enhanced


def enhance_mri_volume(volume, clip_limit=2.0):
    """Enhance a 3D volume slice by slice."""

    volume = np.asarray(volume, dtype=np.float32)

    if volume.ndim != 3:
        raise ValueError("Expected a 3D MRI volume.")

    if not np.isfinite(volume).all():
        raise ValueError("MRI volume contains invalid values.")

    enhanced_volume = np.zeros(volume.shape, dtype=np.uint8)

    for index in range(volume.shape[2]):
        enhanced_volume[:, :, index] = enhance_mri_slice(
            volume[:, :, index],
            clip_limit=clip_limit
        )

    return enhanced_volume


def export_enhanced_mri_previews(
    mri_path,
    output_dir=None,
    modality=0,
    slice_indices=None,
    clip_limit=2.0
):
    """
    Export enhanced axial, coronal and sagittal MRI previews.

    Modality order in the input dataset:
    0 = FLAIR
    1 = T1
    2 = T1ce
    3 = T2

    Original MRI is never modified.
    """

    mri_path = Path(mri_path)

    if not mri_path.exists():
        raise FileNotFoundError(f"MRI not found: {mri_path}")

    nii = nib.load(str(mri_path))
    mri = nii.get_fdata(dtype=np.float32)

    if mri.ndim != 4 or mri.shape[3] != 4:
        raise ValueError("Expected a four-modality 4D MRI.")

    if not 0 <= modality < 4:
        raise ValueError("Modality must be between 0 and 3.")

    if output_dir is None:
        output_dir = (
            Path(__file__).resolve().parents[2] / "outputs"
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    patient_id = mri_path.name.replace(".nii.gz", "").replace(".nii", "")

    volume = mri[:, :, :, modality]

    if slice_indices is None:
        slices = {
            "axial": volume.shape[2] // 2,
            "coronal": volume.shape[1] // 2,
            "sagittal": volume.shape[0] // 2
        }
    else:
        slices = {
            "axial": int(slice_indices["axial"]),
            "coronal": int(slice_indices["coronal"]),
            "sagittal": int(slice_indices["sagittal"])
        }

    slice_data = {
        "axial": volume[:, :, slices["axial"]],
        "coronal": volume[:, slices["coronal"], :],
        "sagittal": volume[slices["sagittal"], :, :]
    }

    output_paths = {}

    for view, image in slice_data.items():

        enhanced = enhance_mri_slice(
            np.rot90(image),
            clip_limit=clip_limit
        )

        output_path = (
            output_dir / f"{patient_id}_{view}_enhanced.png"
        )

        if not cv2.imwrite(str(output_path), enhanced):
            raise IOError(f"Could not save {view} preview.")

        output_paths[view] = str(output_path)

    return {
        "status": "completed",
        "patient_id": patient_id,
        "modality": ["FLAIR", "T1", "T1ce", "T2"][modality],
        "enhanced_previews": output_paths,
        "slices": slices
    }
