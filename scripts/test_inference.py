
import torch
import nibabel as nib
import numpy as np

from pathlib import Path
from monai.networks.nets import SegResNet
from monai.inferers import SlidingWindowInferer
from monai.transforms import NormalizeIntensity


# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

MRI_PATH = (
    ROOT
    / "Task01_BrainTumour"
    / "imagesTr"
    / "BRATS_001.nii.gz"
)

MODEL_PATH = (
    ROOT
    / "pretrained_models"
    / "brats_mri_segmentation"
    / "models"
    / "model.pt"
)

OUTPUT_PATH = (
    ROOT
    / "outputs"
    / "BRATS_001_prediction.nii.gz"
)


# --------------------------------------------------
# 2. DEVICE CONFIGURATION
# --------------------------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 55)
print("NEUROVISION - BRAIN MRI SEGMENTATION")
print("=" * 55)

print("Device:", device)

if device.type == "cuda":
    print("GPU:", torch.cuda.get_device_name(0))
    torch.cuda.reset_peak_memory_stats()


# --------------------------------------------------
# 3. CHECK REQUIRED FILES
# --------------------------------------------------

if not MRI_PATH.exists():
    raise FileNotFoundError(
        f"MRI file not found: {MRI_PATH}"
    )

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Pretrained model not found: {MODEL_PATH}"
    )


# --------------------------------------------------
# 4. LOAD MRI IMAGE
# --------------------------------------------------

print("\n[1/6] Loading MRI image...")

nii = nib.load(str(MRI_PATH))

image = nii.get_fdata(dtype=np.float32)

print("Original MRI shape:", image.shape)

if image.ndim != 4 or image.shape[3] != 4:
    raise ValueError(
        f"Expected MRI shape (X,Y,Z,4), got {image.shape}"
    )


# --------------------------------------------------
# 5. REORDER MRI CHANNELS
# --------------------------------------------------

print("\n[2/6] Reordering MRI channels...")

# Dataset channel order:
# 0 = FLAIR
# 1 = T1
# 2 = T1ce
# 3 = T2

# Model channel order:
# 0 = T1ce
# 1 = T1
# 2 = T2
# 3 = FLAIR

image = image[..., [2, 1, 3, 0]]

# Convert (X,Y,Z,C) to (C,X,Y,Z)
image = np.transpose(
    image,
    (3, 0, 1, 2)
).copy()

print("Reordered MRI shape:", image.shape)


# --------------------------------------------------
# 6. NORMALIZE MRI INTENSITIES
# --------------------------------------------------

print("\n[3/6] Normalizing MRI channels...")

image_tensor = torch.from_numpy(image)

normalizer = NormalizeIntensity(
    nonzero=True,
    channel_wise=True
)

image_tensor = normalizer(image_tensor)

# Add batch dimension:
# (C,X,Y,Z) -> (1,C,X,Y,Z)

image_tensor = image_tensor.unsqueeze(0)

image_tensor = image_tensor.to(device)

print("Model input shape:", image_tensor.shape)


# --------------------------------------------------
# 7. LOAD PRETRAINED SEGRESNET
# --------------------------------------------------

print("\n[4/6] Loading pretrained SegResNet...")

model = SegResNet(
    blocks_down=(1, 2, 2, 4),
    blocks_up=(1, 1, 1),
    init_filters=16,
    in_channels=4,
    out_channels=3,
    dropout_prob=0.2
)

state = torch.load(
    str(MODEL_PATH),
    map_location="cpu",
    weights_only=True
)

model.load_state_dict(
    state,
    strict=True
)

model = model.to(device)

model.eval()

print("Pretrained weights loaded successfully.")


# --------------------------------------------------
# 8. SLIDING WINDOW INFERENCE
# --------------------------------------------------

print("\n[5/6] Running MRI segmentation...")

inferer = SlidingWindowInferer(
    roi_size=(240, 240, 160),
    sw_batch_size=1,
    overlap=0.5
)

try:
    with torch.inference_mode():

        if device.type == "cuda":

            with torch.autocast(
                device_type="cuda",
                dtype=torch.float16
            ):
                logits = inferer(
                    image_tensor,
                    model
                )

        else:
            logits = inferer(
                image_tensor,
                model
            )

except torch.cuda.OutOfMemoryError:

    print("\nGPU memory exhausted.")
    print("Please reduce the inference ROI or use CPU.")
    raise

print("Inference completed.")
print("Raw output shape:", logits.shape)


# --------------------------------------------------
# 9. CONVERT OUTPUT INTO TUMOR MASKS
# --------------------------------------------------

print("\n[6/6] Generating tumor segmentation masks...")

probabilities = torch.sigmoid(logits)

channels = probabilities[0] >= 0.5

# Model output channels:
# Channel 0 = Tumor Core (TC)
# Channel 1 = Whole Tumor (WT)
# Channel 2 = Enhancing Tumor (ET)

tc = channels[0].cpu().numpy()
wt = channels[1].cpu().numpy()
et = channels[2].cpu().numpy()


# --------------------------------------------------
# 10. CREATE FINAL LABEL MAP
# --------------------------------------------------

# Final labels:
# 0 = Background
# 1 = Tumor Core
# 2 = Whole Tumor outside Tumor Core
# 4 = Enhancing Tumor

prediction = np.zeros(
    wt.shape,
    dtype=np.uint8
)

prediction[wt] = 2
prediction[tc] = 1
prediction[et] = 4


# --------------------------------------------------
# 11. SAVE PREDICTION AS NIFTI
# --------------------------------------------------

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

header = nii.header.copy()

header.set_data_dtype(np.uint8)

result_nii = nib.Nifti1Image(
    prediction,
    nii.affine,
    header
)

nib.save(
    result_nii,
    str(OUTPUT_PATH)
)


# --------------------------------------------------
# 12. DISPLAY RESULTS
# --------------------------------------------------

print("\n" + "=" * 55)
print("SEGMENTATION RESULTS")
print("=" * 55)

print("Patient: BRATS_001")

print("Prediction shape:", prediction.shape)

print("Predicted labels:", np.unique(prediction))

print(
    "Predicted tumor voxels:",
    int(np.count_nonzero(prediction))
)

print(
    "Tumor Core voxels:",
    int(np.count_nonzero(prediction == 1))
)

print(
    "Whole Tumor-only voxels:",
    int(np.count_nonzero(prediction == 2))
)

print(
    "Enhancing Tumor voxels:",
    int(np.count_nonzero(prediction == 4))
)

if device.type == "cuda":
    print(
        "GPU peak memory (MB):",
        round(
            torch.cuda.max_memory_allocated() / 1024**2,
            2
        )
    )

print("\nSaved prediction:")
print(OUTPUT_PATH)

print("\nNEUROVISION INFERENCE FINISHED.")
print("=" * 55)
