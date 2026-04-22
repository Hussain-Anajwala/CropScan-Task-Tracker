"""Stratified dataset split utility for CropScan."""

from __future__ import annotations

import argparse
import shutil
from collections import Counter
from pathlib import Path

from loguru import logger
from sklearn.model_selection import train_test_split

from ml.dataset import IMAGE_EXTENSIONS, get_class_names


def _collect_samples(input_dir: Path) -> tuple[list[Path], list[str]]:
    image_paths: list[Path] = []
    labels: list[str] = []

    for class_name in get_class_names(input_dir):
        class_dir = input_dir / class_name
        for image_path in sorted(class_dir.rglob("*")):
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS:
                image_paths.append(image_path)
                labels.append(class_name)

    if not image_paths:
        raise ValueError(f"No image files found in {input_dir}")
    return image_paths, labels


def _prepare_output_dirs(output_dir: Path, class_names: list[str]) -> None:
    for split_name in ("train", "val", "test"):
        for class_name in class_names:
            (output_dir / split_name / class_name).mkdir(parents=True, exist_ok=True)


def _copy_split(split_name: str, paths: list[Path], labels: list[str], output_dir: Path) -> None:
    for image_path, class_name in zip(paths, labels, strict=True):
        destination = output_dir / split_name / class_name / image_path.name
        shutil.copy2(image_path, destination)


def _log_split_distribution(split_name: str, labels: list[str]) -> None:
    distribution = Counter(labels)
    logger.info("{} split: {} images", split_name, len(labels))
    for class_name in sorted(distribution):
        logger.info("  {} -> {}", class_name, distribution[class_name])


def stratified_split_dataset(
    input_dir: str | Path,
    output_dir: str | Path,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
) -> None:
    """Create a stratified train/validation/test split.

    Args:
        input_dir: Source dataset root.
        output_dir: Destination root for split output.
        train_ratio: Train split ratio.
        val_ratio: Validation split ratio.
        test_ratio: Test split ratio.
        random_state: Random seed.
    """
    total_ratio = train_ratio + val_ratio + test_ratio
    if abs(total_ratio - 1.0) > 1e-6:
        raise ValueError("train_ratio + val_ratio + test_ratio must sum to 1.0")

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    image_paths, labels = _collect_samples(input_path)
    class_names = get_class_names(input_path)

    train_paths, temp_paths, train_labels, temp_labels = train_test_split(
        image_paths,
        labels,
        test_size=(1.0 - train_ratio),
        stratify=labels,
        random_state=random_state,
    )

    val_share = val_ratio / (val_ratio + test_ratio)
    val_paths, test_paths, val_labels, test_labels = train_test_split(
        temp_paths,
        temp_labels,
        test_size=(1.0 - val_share),
        stratify=temp_labels,
        random_state=random_state,
    )

    _prepare_output_dirs(output_path, class_names)
    _copy_split("train", train_paths, train_labels, output_path)
    _copy_split("val", val_paths, val_labels, output_path)
    _copy_split("test", test_paths, test_labels, output_path)

    _log_split_distribution("train", train_labels)
    _log_split_distribution("val", val_labels)
    _log_split_distribution("test", test_labels)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create stratified data splits for CropScan.")
    parser.add_argument("--input-dir", type=Path, required=True, help="Dataset root with class directories.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Destination split root directory.")
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    """CLI entry point for split creation."""
    args = _build_arg_parser().parse_args()
    stratified_split_dataset(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        random_state=args.seed,
    )


if __name__ == "__main__":
    main()
