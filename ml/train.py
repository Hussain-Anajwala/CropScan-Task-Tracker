from __future__ import annotations

# Phase 2 training entry point for CropScan.
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import mlflow
import pytorch_lightning as pl
import timm
import torch
from loguru import logger
from pytorch_lightning.callbacks import ModelCheckpoint
from sklearn.metrics import f1_score
from torch import Tensor, nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader

from ml.dataset import PlantDiseaseDataset, get_class_names
from ml.transforms import get_train_transforms, get_validation_transforms


DEFAULT_DATA_ROOT = Path(
    r"C:\Users\husai\Desktop\Clg Projects\MV_Python\CropScan-Task-Tracker\data\processed\plantvillage"
)
DEFAULT_MLFLOW_URI = f"file:{(Path(__file__).resolve().parents[1] / 'mlruns').as_posix()}"


PHASE2_RUN_PRESETS = {
    "run1": {
        "model": "efficientnet_b4",
        "epochs": 30,
        "batch_size": 32,
        "learning_rate": 3e-4,
        "weight_decay": 1e-4,
        "output_name": "efficientnet_b4_best.pth",
        "description": "EfficientNet-B4 baseline on PlantVillage.",
    },
    "run2": {
        "model": "vit_base_patch16_224",
        "epochs": 30,
        "batch_size": 32,
        "learning_rate": 3e-4,
        "weight_decay": 1e-4,
        "output_name": "vit_base_patch16_224_best.pth",
        "description": "ViT-Base baseline on PlantVillage.",
    },
    "run3": {
        "model": "efficientnet_b4",
        "epochs": 15,
        "batch_size": 32,
        "learning_rate": 1e-5,
        "weight_decay": 1e-4,
        "output_name": "phase2_finetuned_best.pth",
        "description": "Fine-tuning run on combined PlantVillage + PlantDoc data.",
    },
}


class CropDiseaseModule(pl.LightningModule):
    """Lightning module for crop disease classification."""

    def __init__(
        self,
        model_name: str,
        num_classes: int,
        learning_rate: float = 3e-4,
        weight_decay: float = 1e-4,
        max_epochs: int = 30,
        checkpoint_path: str | Path | None = None,
    ) -> None:
        """Initialize the lightning module."""
        super().__init__()
        self.save_hyperparameters()
        self.model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
        self.criterion = nn.CrossEntropyLoss()
        self.train_outputs: list[tuple[Tensor, Tensor]] = []
        self.val_outputs: list[tuple[Tensor, Tensor]] = []
        self.test_outputs: list[tuple[Tensor, Tensor]] = []
        if checkpoint_path:
            self._load_checkpoint(checkpoint_path)

    def forward(self, images: Tensor) -> Tensor:
        """Forward pass."""
        return self.model(images)

    def _load_checkpoint(self, checkpoint_path: str | Path) -> None:
        """Load model weights for warm start or fine-tuning."""
        checkpoint_file = Path(checkpoint_path)
        if not checkpoint_file.exists():
            raise FileNotFoundError(f"Checkpoint path does not exist: {checkpoint_file}")
        checkpoint = torch.load(checkpoint_file, map_location="cpu")
        state_dict = checkpoint.get("state_dict", checkpoint)
        cleaned_state_dict = {key.removeprefix("model."): value for key, value in state_dict.items()}
        self.model.load_state_dict(cleaned_state_dict, strict=False)
        logger.info("Loaded checkpoint from {}", checkpoint_file)

    def _shared_step(self, batch: tuple[Tensor, Tensor, list[str]], stage: str) -> tuple[Tensor, Tensor, Tensor]:
        images, labels, _ = batch
        batch_size = images.size(0)
        logits = self(images)
        loss = self.criterion(logits, labels)
        predictions = torch.argmax(logits, dim=1)
        accuracy = (predictions == labels).float().mean()
        self.log(f"{stage}/loss", loss, prog_bar=(stage != "train"), on_step=False, on_epoch=True, batch_size=batch_size)
        self.log(f"{stage}/accuracy", accuracy, prog_bar=True, on_step=False, on_epoch=True, batch_size=batch_size)
        return loss, predictions.detach().cpu(), labels.detach().cpu()

    def training_step(self, batch: tuple[Tensor, Tensor, list[str]], batch_idx: int) -> Tensor:
        """Training step."""
        loss, predictions, labels = self._shared_step(batch, "train")
        self.train_outputs.append((predictions, labels))
        return loss

    def validation_step(self, batch: tuple[Tensor, Tensor, list[str]], batch_idx: int) -> Tensor:
        """Validation step."""
        loss, predictions, labels = self._shared_step(batch, "val")
        self.val_outputs.append((predictions, labels))
        return loss

    def test_step(self, batch: tuple[Tensor, Tensor, list[str]], batch_idx: int) -> Tensor:
        """Test step."""
        loss, predictions, labels = self._shared_step(batch, "test")
        self.test_outputs.append((predictions, labels))
        return loss

    def _log_epoch_f1(self, stage: str, outputs: list[tuple[Tensor, Tensor]]) -> None:
        if not outputs:
            return
        predictions = torch.cat([item[0] for item in outputs]).numpy()
        labels = torch.cat([item[1] for item in outputs]).numpy()
        f1_value = float(f1_score(labels, predictions, average="macro"))
        self.log(f"{stage}/f1", f1_value, prog_bar=(stage != "train"), batch_size=1)
        if mlflow.active_run():
            mlflow.log_metric(f"{stage}_f1", f1_value, step=int(self.current_epoch))

    def on_train_epoch_end(self) -> None:
        """Log train F1 and clear epoch buffers."""
        self._log_epoch_f1("train", self.train_outputs)
        self.train_outputs.clear()

    def on_validation_epoch_end(self) -> None:
        """Log validation F1 and clear epoch buffers."""
        self._log_epoch_f1("val", self.val_outputs)
        self.val_outputs.clear()

    def on_test_epoch_end(self) -> None:
        """Log test F1 and clear epoch buffers."""
        self._log_epoch_f1("test", self.test_outputs)
        self.test_outputs.clear()

    def configure_optimizers(self) -> dict[str, object]:
        """Configure AdamW optimizer with cosine scheduler."""
        optimizer = AdamW(
            self.parameters(),
            lr=self.hparams.learning_rate,
            weight_decay=self.hparams.weight_decay,
        )
        scheduler = CosineAnnealingLR(optimizer, T_max=self.hparams.max_epochs)
        return {
            "optimizer": optimizer,
            "lr_scheduler": {"scheduler": scheduler, "interval": "epoch"},
        }

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a CropScan classifier.")
    parser.add_argument("--preset", type=str, choices=sorted(PHASE2_RUN_PRESETS), default=None)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--model", type=str, default="efficientnet_b4")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--mlflow-uri", type=str, default=DEFAULT_MLFLOW_URI)
    parser.add_argument("--experiment-name", type=str, default="cropscan-phase2")
    parser.add_argument("--output-dir", type=Path, default=Path("models/weights"))
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--resume-from-checkpoint", type=Path, default=None)
    parser.add_argument("--save-config", type=Path, default=None)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--fast-dev-run", action="store_true")
    return parser.parse_args()


def _configure_device() -> str:
    if torch.cuda.is_available():
        torch.cuda.set_device(0)
        torch.backends.cudnn.benchmark = True
        device_name = torch.cuda.get_device_name(0)
        logger.info("Using CUDA device 0: {}", device_name)
        return "gpu"
    logger.warning("CUDA is not available. Falling back to CPU.")
    return "cpu"


def _select_precision(accelerator: str) -> str:
    return "16-mixed" if accelerator == "gpu" else "32-true"


def _build_loader_kwargs(num_workers: int) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "num_workers": num_workers,
        "pin_memory": True,
    }
    if num_workers > 0:
        kwargs["persistent_workers"] = True
        kwargs["multiprocessing_context"] = "spawn"
    return kwargs


def _build_dataloader(split_dir: Path, batch_size: int, train: bool, num_workers: int) -> DataLoader:
    transform = get_train_transforms() if train else get_validation_transforms()
    dataset = PlantDiseaseDataset(split_dir, transform=transform)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=train,
        **_build_loader_kwargs(num_workers),
    )


def main() -> None:
    """CLI entry point for model training."""
    args = _parse_args()
    if args.preset:
        preset = PHASE2_RUN_PRESETS[args.preset]
        args.model = preset["model"]
        args.epochs = preset["epochs"]
        args.batch_size = preset["batch_size"]
        args.learning_rate = preset["learning_rate"]
        args.weight_decay = preset["weight_decay"]

    train_dir = args.data_root / "train"
    val_dir = args.data_root / "val"
    test_dir = args.data_root / "test"

    class_names = get_class_names(train_dir)
    logger.info("Training {} with {} classes", args.model, len(class_names))

    if args.batch_size > 64:
        logger.warning("Batch size {} is too high for the 6GB RTX 2060 target. Clamping to 64.", args.batch_size)
        args.batch_size = 64

    train_loader = _build_dataloader(train_dir, args.batch_size, train=True, num_workers=args.num_workers)
    val_loader = _build_dataloader(val_dir, args.batch_size, train=False, num_workers=args.num_workers)
    test_loader = _build_dataloader(test_dir, args.batch_size, train=False, num_workers=args.num_workers)

    module = CropDiseaseModule(
        model_name=args.model,
        num_classes=len(class_names),
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        max_epochs=args.epochs,
        checkpoint_path=args.checkpoint,
    )
    checkpoint_callback = ModelCheckpoint(
        dirpath=args.output_dir,
        filename=f"{args.model}" + "-epoch={epoch:02d}",
        monitor="val/loss",
        mode="min",
        save_top_k=1,
        auto_insert_metric_name=False,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    class_names_path = args.output_dir / "class_names.json"
    class_names_path.write_text(json.dumps(class_names, indent=2), encoding="utf-8")
    logger.info("Saved class names to {}", class_names_path)
    if args.save_config:
        args.save_config.parent.mkdir(parents=True, exist_ok=True)
        args.save_config.write_text(
            json.dumps(
                {
                    "preset": args.preset,
                    "model": args.model,
                    "epochs": args.epochs,
                    "batch_size": args.batch_size,
                    "learning_rate": args.learning_rate,
                    "weight_decay": args.weight_decay,
                    "data_root": str(args.data_root),
                    "checkpoint": str(args.checkpoint) if args.checkpoint else None,
                    "resume_from_checkpoint": str(args.resume_from_checkpoint) if args.resume_from_checkpoint else None,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    mlflow.set_tracking_uri(args.mlflow_uri)
    mlflow.set_experiment(args.experiment_name)

    with mlflow.start_run():
        mlflow.log_params(
            {
                "model": args.model,
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "learning_rate": args.learning_rate,
                "weight_decay": args.weight_decay,
                "num_classes": len(class_names),
                "preset": args.preset or "custom",
                "checkpoint": str(args.checkpoint) if args.checkpoint else "",
                "resume_from_checkpoint": str(args.resume_from_checkpoint) if args.resume_from_checkpoint else "",
            }
        )
        accelerator = _configure_device()
        trainer = pl.Trainer(
            max_epochs=args.epochs,
            accelerator=accelerator,
            devices=1,
            num_sanity_val_steps=0,
            callbacks=[checkpoint_callback],
            log_every_n_steps=1,
            fast_dev_run=args.fast_dev_run,
            precision=_select_precision(accelerator),
        )
        trainer.fit(module, train_loader, val_loader, ckpt_path=str(args.resume_from_checkpoint) if args.resume_from_checkpoint else None)
        trainer.test(module, dataloaders=test_loader)
        if checkpoint_callback.best_model_path:
            output_name = (
                PHASE2_RUN_PRESETS[args.preset]["output_name"]
                if args.preset
                else f"{args.model}_best.pth"
            )
            canonical_path = args.output_dir / output_name
            shutil.copy2(checkpoint_callback.best_model_path, canonical_path)
            mlflow.log_artifact(str(canonical_path))
            logger.info("Saved best checkpoint alias to {}", canonical_path)


if __name__ == "__main__":
    main()
