
import torch

from pathlib import Path
from functools import lru_cache
from monai.networks.nets import SegResNet


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    ROOT
    / "pretrained_models"
    / "brats_mri_segmentation"
    / "models"
    / "model.pt"
)


def get_device():
    """Select CUDA when available, otherwise CPU."""
    return torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )


@lru_cache(maxsize=1)
def load_model():
    """
    Load the existing pretrained SegResNet once.

    No training, fine-tuning or weight updates.
    """

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Pretrained model not found: {MODEL_PATH}"
        )

    device = get_device()

    model = SegResNet(
        blocks_down=(1, 2, 2, 4),
        blocks_up=(1, 1, 1),
        init_filters=16,
        in_channels=4,
        out_channels=3,
        dropout_prob=0.2
    )

    try:
        state_dict = torch.load(
            str(MODEL_PATH),
            map_location="cpu",
            weights_only=True
        )

        model.load_state_dict(
            state_dict,
            strict=True
        )

    except Exception as error:
        raise RuntimeError(
            f"Failed to load pretrained model: {error}"
        ) from error

    model.to(device)
    model.eval()

    return model, device


def get_model_info():
    """Return pretrained model information."""

    model, device = load_model()

    return {
        "model_name": "MONAI SegResNet",
        "bundle": "brats_mri_segmentation",
        "version": "0.5.2",
        "device": str(device),
        "cuda_available": torch.cuda.is_available(),
        "parameters": sum(
            parameter.numel()
            for parameter in model.parameters()
        ),
        "input_channels": 4,
        "output_channels": 3,
        "architecture": "SegResNet",
        "status": "loaded",
        "trained": True,
        "fine_tuning": False,
        "training_enabled": False,
        "cached": load_model.cache_info().currsize == 1
    }
