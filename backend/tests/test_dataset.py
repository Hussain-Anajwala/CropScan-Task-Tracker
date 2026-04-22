"""Tests for CropScan Phase 1 dataset utilities."""

from __future__ import annotations

from pathlib import Path
import shutil
from uuid import uuid4

import numpy as np
from PIL import Image
from torch.utils.data import DataLoader

from ml.dataset import PlantDiseaseDataset, compute_class_distribution, get_class_names
from ml.split_dataset import stratified_split_dataset
from ml.transforms import get_train_transforms, get_validation_transforms


def _workspace_tmp_dir(test_name: str) -> Path:
    root = Path(".tmp") / "tests" / f"{test_name}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_synthetic_dataset(root_dir: Path, images_per_class: int = 6) -> None:
    class_names = ["healthy", "late_blight"]
    for class_name in class_names:
        class_dir = root_dir / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        for index in range(images_per_class):
            image = np.full((256, 256, 3), fill_value=30 + (index * 10), dtype=np.uint8)
            if class_name == "late_blight":
                image[:, :, 0] = 180
            Image.fromarray(image).save(class_dir / f"{class_name}_{index}.png")


def test_get_class_names_returns_sorted_names() -> None:
    root_dir = _workspace_tmp_dir("class_names")
    try:
        _write_synthetic_dataset(root_dir)
        assert get_class_names(root_dir) == ["healthy", "late_blight"]
    finally:
        shutil.rmtree(root_dir, ignore_errors=True)


def test_dataset_loads_five_batches_with_expected_shapes() -> None:
    root_dir = _workspace_tmp_dir("five_batches")
    try:
        _write_synthetic_dataset(root_dir, images_per_class=5)
        dataset = PlantDiseaseDataset(root_dir, transform=get_train_transforms())
        loader = DataLoader(dataset, batch_size=2, shuffle=False)

        observed_batches = 0
        for images, labels, paths in loader:
            assert images.shape[1:] == (3, 224, 224)
            assert labels.min().item() >= 0
            assert labels.max().item() < len(dataset.class_names)
            assert len(paths) == images.shape[0]
            observed_batches += 1

        assert observed_batches == 5
    finally:
        shutil.rmtree(root_dir, ignore_errors=True)


def test_compute_class_distribution_reports_counts() -> None:
    root_dir = _workspace_tmp_dir("distribution")
    try:
        _write_synthetic_dataset(root_dir, images_per_class=4)
        distribution = compute_class_distribution(root_dir)
        assert distribution == {"healthy": 4, "late_blight": 4}
    finally:
        shutil.rmtree(root_dir, ignore_errors=True)


def test_stratified_split_preserves_class_presence() -> None:
    root_dir = _workspace_tmp_dir("split")
    source_dir = root_dir / "raw"
    output_dir = root_dir / "processed"
    try:
        _write_synthetic_dataset(source_dir, images_per_class=12)
        stratified_split_dataset(source_dir, output_dir)

        for split_name in ("train", "val", "test"):
            dataset = PlantDiseaseDataset(output_dir / split_name, transform=get_validation_transforms())
            labels = [sample.class_name for sample in dataset.samples]
            assert set(labels) == {"healthy", "late_blight"}
    finally:
        shutil.rmtree(root_dir, ignore_errors=True)
