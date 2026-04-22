"""Grad-CAM utilities for explainable crop disease predictions."""

from __future__ import annotations

import base64
from io import BytesIO

import cv2
import numpy as np
import torch
from PIL import Image
from pytorch_grad_cam import GradCAM, GradCAMPlusPlus
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

from backend.models.classifier import CropDiseaseClassifier


def _reshape_transform_vit(tensor: torch.Tensor, height: int = 14, width: int = 14) -> torch.Tensor:
    tensor = tensor[:, 1:, :].reshape(tensor.size(0), height, width, tensor.size(2))
    return tensor.permute(0, 3, 1, 2)


def _resolve_model(model_or_classifier: CropDiseaseClassifier | torch.nn.Module) -> tuple[torch.nn.Module, str]:
    if isinstance(model_or_classifier, CropDiseaseClassifier):
        return model_or_classifier.model, model_or_classifier.model_type
    architecture = getattr(model_or_classifier, "default_cfg", {}).get("architecture", "")
    model_type = architecture or model_or_classifier.__class__.__name__.lower()
    return model_or_classifier, model_type


def _get_target_layers(model: torch.nn.Module, model_type: str) -> tuple[list[torch.nn.Module], callable | None]:
    if "vit" in model_type:
        return [model.blocks[-1].norm1], _reshape_transform_vit
    if hasattr(model, "conv_head"):
        return [model.conv_head], None
    if hasattr(model, "blocks"):
        return [model.blocks[-1]], None
    raise ValueError(f"Unable to determine Grad-CAM target layer for model type: {model_type}")


def generate_heatmap(
    model_or_classifier: CropDiseaseClassifier | torch.nn.Module,
    image_tensor: torch.Tensor,
    class_idx: int | None = None,
    method: str = "gradcam",
) -> np.ndarray:
    """Generate a Grad-CAM heatmap.

    Args:
        model_or_classifier: Classifier wrapper or raw torch module.
        image_tensor: Input tensor in CHW or BCHW format.
        class_idx: Optional target class index.
        method: Grad-CAM method name, `gradcam` or `gradcam++`.

    Returns:
        Heatmap as a float32 HxW array in the range [0, 1].
    """
    model, model_type = _resolve_model(model_or_classifier)
    target_layers, reshape_transform = _get_target_layers(model, model_type)
    input_tensor = image_tensor.unsqueeze(0) if image_tensor.ndim == 3 else image_tensor
    if input_tensor.ndim != 4:
        raise ValueError("Expected image tensor with shape [C,H,W] or [B,C,H,W].")

    cam_class = GradCAMPlusPlus if method.lower() in {"gradcam++", "gradcamplusplus"} else GradCAM
    targets = None if class_idx is None else [ClassifierOutputTarget(class_idx)]
    with cam_class(model=model, target_layers=target_layers, reshape_transform=reshape_transform) as cam:
        grayscale_cam = cam(input_tensor=input_tensor, targets=targets)
    return grayscale_cam[0].astype(np.float32)


def overlay_heatmap(original_image: np.ndarray, heatmap: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """Overlay a heatmap on top of an RGB image.

    Args:
        original_image: Original RGB image in HWC format.
        heatmap: Heatmap in [0, 1].
        alpha: Overlay blend factor.

    Returns:
        RGB uint8 overlay image.
    """
    if original_image.dtype != np.uint8:
        original_image = np.clip(original_image, 0, 255).astype(np.uint8)

    resized_heatmap = cv2.resize(heatmap, (original_image.shape[1], original_image.shape[0]))
    colored = cv2.applyColorMap(np.uint8(resized_heatmap * 255), cv2.COLORMAP_JET)
    colored = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    blended = cv2.addWeighted(original_image, 1.0 - alpha, colored, alpha, 0)
    return blended


def heatmap_to_base64(heatmap_image: np.ndarray) -> str:
    """Encode a heatmap image as a base64 PNG string."""
    image = Image.fromarray(np.clip(heatmap_image, 0, 255).astype(np.uint8))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
