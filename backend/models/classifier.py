"""Classifier loading and inference utilities for CropScan."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import timm
import torch
from loguru import logger
from PIL import Image
from torch import Tensor, nn

from ml.dataset import get_class_names
from ml.transforms import get_validation_transforms


SUPPORTED_MODELS = {
    "efficientnet_b4": "efficientnet_b4",
    "vit_base_patch16_224": "vit_base_patch16_224",
}

_CLASSIFIER_CACHE: dict[tuple[str, str, int, tuple[str, ...]], "CropDiseaseClassifier"] = {}


def load_class_names(source: str | Path | None, fallback_dir: str | Path | None = None) -> list[str]:
    """Load class names from a JSON file or a class-structured training directory."""
    if source:
        source_path = Path(source)
        if source_path.is_file():
            class_names = json.loads(source_path.read_text(encoding="utf-8"))
            if not isinstance(class_names, list) or not all(isinstance(item, str) for item in class_names):
                raise ValueError(f"Invalid class names file: {source_path}")
            return class_names
        if source_path.is_dir():
            return get_class_names(source_path)

    if fallback_dir:
        return get_class_names(fallback_dir)

    raise FileNotFoundError("No valid class name source was found.")


class CropDiseaseClassifier:
    """Thin wrapper around a timm classification model."""

    def __init__(
        self,
        model_type: str,
        weights_path: str | Path | None,
        num_classes: int,
        class_names: list[str] | None = None,
        device: str | None = None,
    ) -> None:
        """Initialize the classifier.

        Args:
            model_type: Supported timm model identifier.
            weights_path: Optional checkpoint path.
            num_classes: Number of output classes.
            class_names: Optional ordered class name list.
            device: Optional torch device override.
        """
        if model_type not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model_type: {model_type}")

        self.model_type = model_type
        self.weights_path = Path(weights_path) if weights_path else None
        self.num_classes = num_classes
        self.class_names = class_names or [f"class_{index}" for index in range(num_classes)]
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.transform = get_validation_transforms()
        self.model = self._build_model()
        self._load_weights_if_available()
        self.model.to(self.device)
        self.model.eval()

    def _build_model(self) -> nn.Module:
        """Create the underlying timm model."""
        logger.info("Creating classifier model {} with {} classes", self.model_type, self.num_classes)
        return timm.create_model(SUPPORTED_MODELS[self.model_type], pretrained=False, num_classes=self.num_classes)

    def _load_weights_if_available(self) -> None:
        """Load a checkpoint when one is available."""
        if not self.weights_path:
            logger.info("No weights path provided. Using randomly initialized model.")
            return
        if not self.weights_path.exists():
            logger.warning("Weights path does not exist: {}", self.weights_path)
            return

        checkpoint = torch.load(self.weights_path, map_location="cpu")
        if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
            cleaned_state_dict = {key.removeprefix("model."): value for key, value in state_dict.items()}
        else:
            cleaned_state_dict = checkpoint

        self.model.load_state_dict(cleaned_state_dict, strict=False)
        logger.info("Loaded classifier weights from {}", self.weights_path)

    @staticmethod
    def _format_label(label: str) -> dict[str, str]:
        if "___" in label:
            crop, disease = label.split("___", 1)
        else:
            crop, disease = label, label
        return {
            "class": label,
            "crop": crop,
            "disease": disease,
        }

    def prepare_image(self, image: Image.Image) -> Tensor:
        """Convert a PIL image into the validation tensor expected by the model."""
        rgb_image = image.convert("RGB")
        array = np.array(rgb_image)
        transformed = self.transform(image=array)
        return transformed["image"]

    @torch.inference_mode()
    def predict(self, image_tensor: Tensor) -> tuple[int, float, str]:
        """Run inference on an image tensor.

        Args:
            image_tensor: Image tensor in CHW or BCHW format.

        Returns:
            Predicted class index, confidence score, and class name.
        """
        if image_tensor.ndim == 3:
            image_tensor = image_tensor.unsqueeze(0)
        if image_tensor.ndim != 4:
            raise ValueError("Expected image tensor with shape [C,H,W] or [B,C,H,W].")

        image_tensor = image_tensor.to(self.device)
        logits = self.model(image_tensor)
        probabilities = torch.softmax(logits, dim=1)
        confidence, predicted_index = probabilities.max(dim=1)
        class_idx = int(predicted_index.item())
        return class_idx, float(confidence.item()), self.class_names[class_idx]

    @torch.inference_mode()
    def predict_top_k(self, image_tensor: Tensor, k: int = 3) -> dict[str, Any]:
        """Run inference and return the top-k ranked classes."""
        if image_tensor.ndim == 3:
            image_tensor = image_tensor.unsqueeze(0)
        if image_tensor.ndim != 4:
            raise ValueError("Expected image tensor with shape [C,H,W] or [B,C,H,W].")

        image_tensor = image_tensor.to(self.device)
        start = time.perf_counter()
        logits = self.model(image_tensor)
        probabilities = torch.softmax(logits, dim=1)
        inference_time_ms = (time.perf_counter() - start) * 1000.0
        top_confidences, top_indices = torch.topk(probabilities, k=min(k, self.num_classes), dim=1)

        top_k: list[dict[str, Any]] = []
        for confidence, index in zip(top_confidences[0], top_indices[0], strict=True):
            class_idx = int(index.item())
            formatted = self._format_label(self.class_names[class_idx])
            top_k.append(
                {
                    "class": formatted["class"],
                    "confidence": float(confidence.item()),
                    "crop": formatted["crop"],
                    "disease": formatted["disease"],
                    "index": class_idx,
                }
            )

        best = top_k[0]
        return {
            "class": best["class"],
            "confidence": best["confidence"],
            "crop": best["crop"],
            "disease": best["disease"],
            "class_idx": best["index"],
            "top_k": [{key: value for key, value in item.items() if key != "index"} for item in top_k],
            "inference_time_ms": inference_time_ms,
        }

    def predict_image(self, image: Image.Image, top_k: int = 3) -> dict[str, Any]:
        """Run inference directly from a PIL image."""
        tensor = self.prepare_image(image)
        return self.predict_top_k(tensor, k=top_k)


def predict(image: Image.Image, top_k: int = 3) -> dict[str, Any]:
    """Convenience inference entry point for the default backend model."""
    from backend.config import settings

    class_names_path = settings.resolve_path(settings.model_class_names_path)
    weights_path = settings.resolve_path(settings.model_weights_path)
    exported_class_names = weights_path.parent / "class_names.json"
    class_names = load_class_names(
        exported_class_names if exported_class_names.exists() else class_names_path,
        fallback_dir=class_names_path,
    )
    classifier = load_model(
        model_type=settings.model_type,
        weights_path=weights_path,
        num_classes=len(class_names),
        class_names=class_names,
    )
    return classifier.predict_image(image=image, top_k=top_k)


def load_model(
    model_type: str,
    weights_path: str | Path | None,
    num_classes: int,
    class_names: list[str] | None = None,
    device: str | None = None,
) -> CropDiseaseClassifier:
    """Load and cache a classifier model instance.

    Args:
        model_type: Supported model identifier.
        weights_path: Optional checkpoint path.
        num_classes: Number of output classes.
        class_names: Optional class name mapping.
        device: Optional torch device override.

    Returns:
        Cached classifier instance.
    """
    cache_key = (model_type, str(weights_path or ""), num_classes, tuple(class_names or ()))
    classifier = _CLASSIFIER_CACHE.get(cache_key)
    if classifier is None:
        classifier = CropDiseaseClassifier(
            model_type=model_type,
            weights_path=weights_path,
            num_classes=num_classes,
            class_names=class_names,
            device=device,
        )
        _CLASSIFIER_CACHE[cache_key] = classifier
    return classifier
