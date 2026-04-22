"""Phase 2 smoke tests for classifier, Grad-CAM, and evaluation utilities."""

from __future__ import annotations

from pathlib import Path
import shutil
from uuid import uuid4

import numpy as np
from PIL import Image
import torch

from backend.models.classifier import load_model
from backend.services.gradcam import generate_heatmap, heatmap_to_base64, overlay_heatmap
from ml.evaluate import benchmark_inference, save_confusion_matrix, save_gradcam_gallery
from ml.train import CropDiseaseModule
from ml.transforms import get_validation_transforms


def _workspace_tmp_dir(test_name: str) -> Path:
    root = Path(".tmp") / "tests" / f"{test_name}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_synthetic_dataset(root_dir: Path, images_per_class: int = 3) -> None:
    for class_name in ["healthy", "late_blight"]:
        class_dir = root_dir / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        for index in range(images_per_class):
            image = np.full((224, 224, 3), fill_value=50 + index, dtype=np.uint8)
            if class_name == "late_blight":
                image[:, :, 0] = 200
            Image.fromarray(image).save(class_dir / f"{class_name}_{index}.png")


def test_classifier_predict_returns_valid_output() -> None:
    classifier = load_model("efficientnet_b4", None, 2, ["healthy", "late_blight"])
    image = torch.randn(3, 224, 224)
    class_idx, confidence, class_name = classifier.predict(image)
    assert class_idx in {0, 1}
    assert 0.0 <= confidence <= 1.0
    assert class_name in {"healthy", "late_blight"}


def test_gradcam_generates_overlay_and_base64() -> None:
    classifier = load_model("efficientnet_b4", None, 2, ["healthy", "late_blight"])
    image_tensor = torch.randn(3, 224, 224)
    heatmap = generate_heatmap(classifier, image_tensor, class_idx=0)
    overlay = overlay_heatmap(np.zeros((224, 224, 3), dtype=np.uint8), heatmap)
    encoded = heatmap_to_base64(overlay)
    assert heatmap.shape == (224, 224)
    assert overlay.shape == (224, 224, 3)
    assert isinstance(encoded, str)
    assert len(encoded) > 10


def test_training_module_configures_optimizer() -> None:
    module = CropDiseaseModule("efficientnet_b4", num_classes=2)
    config = module.configure_optimizers()
    assert "optimizer" in config
    assert "lr_scheduler" in config


def test_evaluation_helpers_write_outputs() -> None:
    root_dir = _workspace_tmp_dir("phase2_eval")
    try:
        dataset_dir = root_dir / "test"
        _write_synthetic_dataset(dataset_dir)
        results = benchmark_inference(
            data_dir=dataset_dir,
            models=["efficientnet_b4"],
            weights_dir=root_dir,
            max_images=2,
        )
        assert "efficientnet_b4" in results

        confusion_path = root_dir / "confusion.png"
        save_confusion_matrix([0, 1], [0, 1], ["healthy", "late_blight"], confusion_path)
        assert confusion_path.exists()

        gradcam_dir = root_dir / "gradcam"
        save_gradcam_gallery(
            data_dir=dataset_dir,
            model_type="efficientnet_b4",
            weights_path=None,
            output_dir=gradcam_dir,
            max_images=2,
        )
        generated = list(gradcam_dir.glob("*.png"))
        assert len(generated) == 2
    finally:
        shutil.rmtree(root_dir, ignore_errors=True)
