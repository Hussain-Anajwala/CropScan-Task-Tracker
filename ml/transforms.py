"""Albumentations transforms used across CropScan datasets."""

from __future__ import annotations

import albumentations as A
from albumentations.pytorch import ToTensorV2


IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def get_train_transforms(image_size: int = 224) -> A.Compose:
    """Build training-time augmentation pipeline.

    Args:
        image_size: Final square image size.

    Returns:
        Albumentations compose object.
    """
    return A.Compose(
        [
            A.Resize(image_size, image_size),
            A.RandomRotate90(p=0.5),
            A.HorizontalFlip(p=0.5),
            A.ColorJitter(
                brightness=0.2,
                contrast=0.2,
                saturation=0.2,
                hue=0.1,
                p=0.5,
            ),
            A.GaussNoise(std_range=(0.05, 0.15), p=0.3),
            A.CoarseDropout(
                num_holes_range=(1, 4),
                hole_height_range=(0.08, 0.2),
                hole_width_range=(0.08, 0.2),
                fill=0,
                p=0.3,
            ),
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ToTensorV2(),
        ]
    )


def get_validation_transforms(image_size: int = 224) -> A.Compose:
    """Build validation/test transform pipeline.

    Args:
        image_size: Final square image size.

    Returns:
        Albumentations compose object.
    """
    return A.Compose(
        [
            A.Resize(image_size, image_size),
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ToTensorV2(),
        ]
    )
