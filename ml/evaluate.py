"""Evaluation utilities for CropScan classifiers."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from loguru import logger
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix
from torch import Tensor
from torch.utils.data import DataLoader

from backend.models.classifier import load_model
from backend.services.gradcam import generate_heatmap, overlay_heatmap
from ml.dataset import PlantDiseaseDataset, get_class_names
from ml.transforms import IMAGENET_MEAN, IMAGENET_STD
from ml.transforms import get_validation_transforms


def evaluate_model(
    data_dir: str | Path,
    model_type: str,
    weights_path: str | Path | None,
    batch_size: int = 16,
) -> dict[str, object]:
    """Run evaluation on a dataset split.

    Args:
        data_dir: Dataset split directory.
        model_type: Supported classifier model name.
        weights_path: Optional checkpoint file.
        batch_size: Evaluation batch size.

    Returns:
        Dictionary containing predictions, labels, and the classification report.
    """
    class_names = get_class_names(data_dir)
    dataset = PlantDiseaseDataset(data_dir, transform=get_validation_transforms())
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    classifier = load_model(
        model_type=model_type,
        weights_path=weights_path,
        num_classes=len(class_names),
        class_names=class_names,
    )

    labels: list[int] = []
    predictions: list[int] = []

    for images, batch_labels, _ in dataloader:
        for image, label in zip(images, batch_labels, strict=True):
            class_idx, _, _ = classifier.predict(image)
            predictions.append(class_idx)
            labels.append(int(label.item()))

    report = classification_report(labels, predictions, target_names=class_names, output_dict=True, zero_division=0)
    per_class_accuracy = {}
    matrix = confusion_matrix(labels, predictions, labels=list(range(len(class_names))))
    for index, class_name in enumerate(class_names):
        total = int(matrix[index].sum())
        correct = int(matrix[index, index])
        per_class_accuracy[class_name] = (correct / total) if total else 0.0
    return {
        "labels": labels,
        "predictions": predictions,
        "class_names": class_names,
        "report": report,
        "per_class_accuracy": per_class_accuracy,
    }


def benchmark_inference(
    data_dir: str | Path,
    models: list[str],
    weights_dir: str | Path,
    batch_size: int = 1,
    max_images: int = 16,
) -> dict[str, dict[str, float]]:
    """Benchmark classifier inference time per image across models."""
    class_names = get_class_names(data_dir)
    dataset = PlantDiseaseDataset(data_dir, transform=get_validation_transforms())
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    benchmarks: dict[str, dict[str, float]] = {}

    for model_name in models:
        weight_path = Path(weights_dir) / f"{model_name}_best.pth"
        classifier = load_model(
            model_type=model_name,
            weights_path=weight_path if weight_path.exists() else None,
            num_classes=len(class_names),
            class_names=class_names,
        )

        measured_images = 0
        total_seconds = 0.0
        for images, _, _ in dataloader:
            for image in images:
                start_time = time.perf_counter()
                classifier.predict(image)
                total_seconds += time.perf_counter() - start_time
                measured_images += 1
                if measured_images >= max_images:
                    break
            if measured_images >= max_images:
                break

        benchmarks[model_name] = {
            "images_evaluated": float(measured_images),
            "avg_inference_ms": (total_seconds / max(measured_images, 1)) * 1000.0,
        }
    return benchmarks


def _tensor_to_rgb_image(image_tensor: Tensor) -> np.ndarray:
    image = image_tensor.detach().cpu().numpy()
    image = np.transpose(image, (1, 2, 0))
    image = (image * np.array(IMAGENET_STD)) + np.array(IMAGENET_MEAN)
    image = np.clip(image * 255.0, 0, 255).astype(np.uint8)
    return image


def save_gradcam_gallery(
    data_dir: str | Path,
    model_type: str,
    weights_path: str | Path | None,
    output_dir: str | Path,
    max_images: int = 20,
) -> None:
    """Generate Grad-CAM overlays for a subset of evaluation images."""
    class_names = get_class_names(data_dir)
    dataset = PlantDiseaseDataset(data_dir, transform=get_validation_transforms())
    classifier = load_model(
        model_type=model_type,
        weights_path=weights_path,
        num_classes=len(class_names),
        class_names=class_names,
    )
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for index in range(min(max_images, len(dataset))):
        image_tensor, label, source_path = dataset[index]
        class_idx, confidence, class_name = classifier.predict(image_tensor)
        original_image = _tensor_to_rgb_image(image_tensor)
        heatmap = generate_heatmap(classifier, image_tensor, class_idx=class_idx)
        overlay = overlay_heatmap(original_image, heatmap)
        target_file = output_path / f"{index:03d}_{Path(source_path).stem}_{class_name}_{confidence:.2f}.png"
        Image.fromarray(overlay).save(target_file)
        logger.info(
            "Saved Grad-CAM overlay {} (true={}, predicted={}, confidence={:.3f})",
            target_file,
            class_names[label],
            class_name,
            confidence,
        )


def save_confusion_matrix(
    labels: list[int],
    predictions: list[int],
    class_names: list[str],
    output_path: str | Path,
) -> None:
    """Save a confusion matrix heatmap image."""
    matrix = confusion_matrix(labels, predictions)
    figure, axis = plt.subplots(figsize=(12, 10))
    heatmap = axis.imshow(matrix, cmap="YlGn")
    figure.colorbar(heatmap, ax=axis)
    axis.set_xticks(np.arange(len(class_names)))
    axis.set_yticks(np.arange(len(class_names)))
    axis.set_xticklabels(class_names, rotation=90)
    axis.set_yticklabels(class_names)
    axis.set_xlabel("Predicted")
    axis.set_ylabel("True")
    axis.set_title("CropScan Confusion Matrix")
    figure.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def save_per_class_accuracy_chart(
    per_class_accuracy: dict[str, float],
    output_path: str | Path,
) -> None:
    """Save a horizontal bar chart for per-class accuracy."""
    items = sorted(per_class_accuracy.items(), key=lambda item: item[1], reverse=True)
    labels = [item[0] for item in items]
    values = [item[1] * 100.0 for item in items]

    figure_height = max(6, len(labels) * 0.45)
    figure, axis = plt.subplots(figsize=(12, figure_height))
    bars = axis.barh(labels, values, color="#65a30d")
    axis.set_xlim(0, 100)
    axis.set_xlabel("Accuracy (%)")
    axis.set_title("Per-Class Accuracy")
    axis.invert_yaxis()
    for bar, value in zip(bars, values, strict=True):
        axis.text(min(value + 1, 98), bar.get_y() + (bar.get_height() / 2), f"{value:.1f}%", va="center", fontsize=8)
    figure.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a CropScan classifier checkpoint.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed/test"))
    parser.add_argument("--model", type=str, default="efficientnet_b4")
    parser.add_argument("--weights", type=Path, default=Path("models/weights/efficientnet_b4_best.pth"))
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("models/evaluation/confusion_matrix.png"),
    )
    parser.add_argument("--per-class-chart", type=Path, default=Path("models/evaluation/per_class_accuracy.png"))
    parser.add_argument("--report-output", type=Path, default=Path("models/evaluation/classification_report.json"))
    parser.add_argument("--gradcam-dir", type=Path, default=None)
    parser.add_argument("--gradcam-images", type=int, default=20)
    parser.add_argument("--benchmark-models", nargs="*", default=None)
    parser.add_argument("--weights-dir", type=Path, default=Path("models/weights"))
    return parser.parse_args()


def main() -> None:
    """CLI entry point for model evaluation."""
    args = _parse_args()
    results = evaluate_model(
        data_dir=args.data_dir,
        model_type=args.model,
        weights_path=args.weights,
        batch_size=args.batch_size,
    )
    save_confusion_matrix(
        labels=results["labels"],
        predictions=results["predictions"],
        class_names=results["class_names"],
        output_path=args.output,
    )
    save_per_class_accuracy_chart(results["per_class_accuracy"], args.per_class_chart)

    report = results["report"]
    logger.info("Evaluation complete for {}", args.model)
    logger.info("Accuracy: {:.4f}", report["accuracy"])
    logger.info("Macro F1: {:.4f}", report["macro avg"]["f1-score"])
    logger.info("Saved per-class accuracy chart to {}", args.per_class_chart)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(
        json.dumps(
            {
                "accuracy": report["accuracy"],
                "macro_f1": report["macro avg"]["f1-score"],
                "per_class_accuracy": results["per_class_accuracy"],
                "classification_report": report,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("Saved evaluation report to {}", args.report_output)
    if args.gradcam_dir:
        save_gradcam_gallery(
            data_dir=args.data_dir,
            model_type=args.model,
            weights_path=args.weights,
            output_dir=args.gradcam_dir,
            max_images=args.gradcam_images,
        )
    if args.benchmark_models:
        benchmarks = benchmark_inference(
            data_dir=args.data_dir,
            models=args.benchmark_models,
            weights_dir=args.weights_dir,
        )
        for model_name, metrics in benchmarks.items():
            logger.info(
                "Benchmark {}: {:.2f} ms/image over {:.0f} images",
                model_name,
                metrics["avg_inference_ms"],
                metrics["images_evaluated"],
            )


if __name__ == "__main__":
    main()
