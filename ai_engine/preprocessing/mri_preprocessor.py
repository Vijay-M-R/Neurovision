
import nibabel as nib
import numpy as np
import torch

from pathlib import Path
from monai.transforms import NormalizeIntensity


EXPECTED_MODALITIES = 4
CHANNEL_ORDER = [2, 1, 3, 0]


def validate_mri(image):
    """Validate a four-modality MRI volume."""

    if not isinstance(image, np.ndarray):
        raise TypeError("MRI must be a NumPy array.")

    if image.ndim != 4:
        raise ValueError(
            f"Expected a 4D MRI, received {image.ndim} dimensions."
        )

    if image.shape[3] != EXPECTED_MODALITIES:
        raise ValueError(
            f"Expected 4 modalities (FLAIR,T1,T1ce,T2), "
            f"received {image.shape[3]}."
        )

    if any(dimension <= 0 for dimension in image.shape[:3]):
        raise ValueError("MRI contains an invalid spatial dimension.")

    if not np.isfinite(image).all():
        raise ValueError("MRI contains NaN or infinite values.")

    if not np.any(image):
        raise ValueError("MRI contains no nonzero voxel values.")

    for channel in range(EXPECTED_MODALITIES):
        if not np.any(image[..., channel] != 0):
            raise ValueError(
                f"MRI modality {channel} contains only zeros."
            )

    return True


def load_mri(mri_path):
    """Load and validate a four-modality NIfTI MRI."""

    path = Path(mri_path)

    if not path.exists():
        raise FileNotFoundError(f"MRI not found: {path}")

    if not path.is_file():
        raise ValueError("MRI path must point to a file.")

    if not (
        path.name.lower().endswith(".nii")
        or path.name.lower().endswith(".nii.gz")
    ):
        raise ValueError("Only .nii and .nii.gz files are supported.")

    try:
        nii = nib.load(str(path))
        image = nii.get_fdata(dtype=np.float32)
    except Exception as error:
        raise ValueError(
            f"Unable to read MRI NIfTI file: {error}"
        ) from error

    validate_mri(image)

    return image, nii


def preprocess_mri(image, device="cpu"):
    """
    Reorder and normalize MRI channels.

    Dataset order: FLAIR, T1, T1ce, T2
    Model order: T1ce, T1, T2, FLAIR
    """

    validate_mri(image)

    if isinstance(device, str):
        device = torch.device(device)

    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable.")

    # Dataset channels to model channels.
    image = image[..., CHANNEL_ORDER]

    # (X,Y,Z,C) -> (C,X,Y,Z)
    image = np.transpose(image, (3, 0, 1, 2)).copy()

    tensor = torch.from_numpy(image)

    normalizer = NormalizeIntensity(
        nonzero=True,
        channel_wise=True
    )

    tensor = normalizer(tensor)

    tensor = tensor.unsqueeze(0)

    if not torch.isfinite(tensor).all():
        raise ValueError("Preprocessed MRI contains invalid values.")

    return tensor.to(device)


def prepare_mri(mri_path, device="cpu"):
    """Complete MRI loading and preprocessing pipeline."""

    image, nii = load_mri(mri_path)

    tensor = preprocess_mri(image, device)

    return {
        "image": tensor,
        "affine": nii.affine.copy(),
        "header": nii.header.copy(),
        "original_shape": image.shape[:3],
        "source_path": str(mri_path),
        "modality_order": ["T1ce", "T1", "T2", "FLAIR"]
    }
