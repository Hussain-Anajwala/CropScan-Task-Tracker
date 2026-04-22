"""Prediction API router."""

from __future__ import annotations

from io import BytesIO

import numpy as np
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from PIL import Image

from backend.config import settings
from backend.models.classifier import load_class_names, load_model
from backend.schemas import PredictResponse
from backend.services.gradcam import generate_heatmap, heatmap_to_base64, overlay_heatmap


router = APIRouter(prefix="/predict", tags=["predict"])


def _load_class_names() -> list[str]:
    try:
        class_names_path = settings.resolve_path(settings.model_class_names_path)
        weights_path = settings.resolve_path(settings.model_weights_path)
        exported_class_names = weights_path.parent / "class_names.json"
        return load_class_names(
            exported_class_names if exported_class_names.exists() else class_names_path,
            fallback_dir=class_names_path,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to load class names: {exc}") from exc


async def _read_upload_as_image(file: UploadFile) -> Image.Image:
    try:
        content = await file.read()
        if not content:
            raise ValueError("Uploaded file is empty.")
        return Image.open(BytesIO(content)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image upload: {exc}") from exc


@router.post("", response_model=PredictResponse)
async def predict(request: Request, file: UploadFile = File(...)) -> PredictResponse:
    """Decode an uploaded image, classify it, and return a heatmap."""
    if file.content_type not in {"image/jpeg", "image/png", "image/webp", "image/jpg"}:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use JPG, PNG, or WEBP.")
    image = await _read_upload_as_image(file)
    image_array = np.array(image)
    class_names = _load_class_names()
    classifier = load_model(
        model_type=settings.model_type,
        weights_path=settings.resolve_path(settings.model_weights_path),
        num_classes=len(class_names),
        class_names=class_names,
    )
    tensor = classifier.prepare_image(image)
    result = classifier.predict_top_k(tensor, k=3)
    heatmap = generate_heatmap(classifier, tensor, class_idx=result["class_idx"])
    overlay = overlay_heatmap(image_array, heatmap)

    return PredictResponse(
        class_name=result["class"],
        disease=result["disease"],
        confidence=result["confidence"],
        crop=result["crop"],
        top_k=result["top_k"],
        heatmap=heatmap_to_base64(overlay),
        inference_time_ms=result["inference_time_ms"],
        environmental_stats={
            "temperature": 28.4,
            "humidity": 82,
            "sensor": "Field Sensor B4"
        }
    )
