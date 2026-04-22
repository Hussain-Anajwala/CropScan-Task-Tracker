"""Image preprocessing utilities for CropScan."""

from __future__ import annotations

from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from loguru import logger
from rembg import remove


IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def _ensure_rgb_uint8(image: np.ndarray) -> np.ndarray:
    """Validate and normalize image input to an RGB uint8 numpy array.

    Args:
        image: Image array in HWC layout.

    Returns:
        RGB image as uint8 numpy array.

    Raises:
        ValueError: If the image has an unsupported shape.
    """
    if image.ndim == 2:
        image = np.stack([image] * 3, axis=-1)
    if image.ndim != 3:
        raise ValueError("Expected image with 2 or 3 dimensions.")
    if image.shape[2] == 4:
        image = image[:, :, :3]
    if image.shape[2] != 3:
        raise ValueError("Expected image with 3 RGB channels.")
    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)
    return image


def resize_image(image: np.ndarray, size: int = 224) -> np.ndarray:
    """Center crop an image to a square and resize it.

    Args:
        image: RGB image array.
        size: Output image width and height.

    Returns:
        Center-cropped and resized RGB image.
    """
    image = _ensure_rgb_uint8(image)
    height, width = image.shape[:2]
    crop_size = min(height, width)
    y_offset = (height - crop_size) // 2
    x_offset = (width - crop_size) // 2
    cropped = image[y_offset : y_offset + crop_size, x_offset : x_offset + crop_size]
    return cv2.resize(cropped, (size, size), interpolation=cv2.INTER_AREA)


def apply_clahe(image: np.ndarray) -> np.ndarray:
    """Apply CLAHE on the luminance channel to improve local contrast.

    Args:
        image: RGB image array.

    Returns:
        Contrast-enhanced RGB image.
    """
    image = _ensure_rgb_uint8(image)
    lab_image = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab_image)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l_channel)

    merged = cv2.merge((enhanced_l, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)


def remove_background(image: np.ndarray) -> np.ndarray:
    """Remove background with rembg and composite back to RGB.

    Args:
        image: RGB image array.

    Returns:
        Background-removed RGB image. If rembg fails, the original image is returned.
    """
    image = _ensure_rgb_uint8(image)
    pil_image = Image.fromarray(image)
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")

    try:
        output_bytes = remove(buffer.getvalue())
        output_image = Image.open(BytesIO(output_bytes)).convert("RGBA")
        white_background = Image.new("RGBA", output_image.size, (255, 255, 255, 255))
        composited = Image.alpha_composite(white_background, output_image).convert("RGB")
        return np.array(composited)
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning("Background removal failed, returning original image: {}", exc)
        return image


def normalize(image: np.ndarray) -> np.ndarray:
    """Normalize an RGB image using ImageNet mean and standard deviation.

    Args:
        image: RGB image array.

    Returns:
        Normalized float32 tensor-like array in CHW format.
    """
    image = _ensure_rgb_uint8(image).astype(np.float32) / 255.0
    normalized = (image - IMAGENET_MEAN) / IMAGENET_STD
    return np.transpose(normalized, (2, 0, 1)).astype(np.float32)
