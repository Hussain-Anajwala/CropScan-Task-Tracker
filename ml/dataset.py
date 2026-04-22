"""Dataset utilities for CropScan Phase 1."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
from loguru import logger
from torch import Tensor
from torch.utils.data import Dataset

from ml.transforms import get_validation_transforms


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@dataclass(frozen=True)
class SampleRecord:
    """Single dataset record."""

    image_path: Path
    class_name: str
    label: int


def get_class_names(root_dir: str | Path) -> list[str]:
    """Return sorted class directory names.

    Args:
        root_dir: Dataset root directory with one folder per class.

    Returns:
        Sorted class names.
    """
    root_path = Path(root_dir)
    if not root_path.exists():
        raise FileNotFoundError(f"Dataset root does not exist: {root_path}")

    class_names = sorted(
        entry.name for entry in root_path.iterdir() if entry.is_dir() and not entry.name.startswith(".")
    )
    if not class_names:
        raise ValueError(f"No class directories found in {root_path}")
    return class_names


class PlantDiseaseDataset(Dataset[tuple[Tensor, int, str]]):
    """Dataset for leaf disease images arranged as class_name/image.jpg."""

    def __init__(
        self,
        root_dir: str | Path,
        transform: Callable | None = None,
    ) -> None:
        """Initialize the dataset.

        Args:
            root_dir: Dataset root path.
            transform: Albumentations transform applied to RGB images.
        """
        self.root_dir = Path(root_dir)
        self.transform = transform or get_validation_transforms()
        self.class_names = get_class_names(self.root_dir)
        self.class_to_idx = {class_name: idx for idx, class_name in enumerate(self.class_names)}
        self.samples = self._discover_samples()

        if not self.samples:
            raise ValueError(f"No image files found in dataset root {self.root_dir}")

    def _discover_samples(self) -> list[SampleRecord]:
        """Scan root directory for supported image files."""
        samples: list[SampleRecord] = []
        for class_name in self.class_names:
            class_dir = self.root_dir / class_name
            label = self.class_to_idx[class_name]
            for image_path in sorted(class_dir.rglob("*")):
                if image_path.suffix.lower() in IMAGE_EXTENSIONS and image_path.is_file():
                    samples.append(SampleRecord(image_path=image_path, class_name=class_name, label=label))
        return samples

    def __len__(self) -> int:
        """Return dataset size."""
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[Tensor, int, str]:
        """Load a single example.

        Args:
            index: Dataset index.

        Returns:
            Tuple of image tensor, integer label, and original image path.
        """
        sample = self.samples[index]
        image = cv2.imread(str(sample.image_path))
        if image is None:
            raise ValueError(f"Failed to read image: {sample.image_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        transformed = self.transform(image=image)
        image_tensor = transformed["image"]
        return image_tensor, sample.label, str(sample.image_path)


def compute_class_distribution(root_dir: str | Path) -> dict[str, int]:
    """Compute per-class image counts.

    Args:
        root_dir: Dataset root path.

    Returns:
        Mapping of class names to image counts.
    """
    dataset = PlantDiseaseDataset(root_dir=root_dir, transform=get_validation_transforms())
    distribution = Counter(sample.class_name for sample in dataset.samples)
    return {class_name: distribution[class_name] for class_name in dataset.class_names}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CropScan dataset inspection utilities.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/processed/train"),
        help="Path to a class-structured dataset split.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print dataset size and class distribution.",
    )
    return parser


def main() -> None:
    """CLI entry point for dataset utilities."""
    args = _build_arg_parser().parse_args()
    if not args.stats:
        raise SystemExit("Nothing to do. Pass --stats to print dataset statistics.")

    distribution = compute_class_distribution(args.data_dir)
    total_images = sum(distribution.values())
    logger.info("Dataset root: {}", args.data_dir)
    logger.info("Class count: {}", len(distribution))
    logger.info("Image count: {}", total_images)
    for class_name, count in distribution.items():
        logger.info("{}: {}", class_name, count)


if __name__ == "__main__":
    main()
