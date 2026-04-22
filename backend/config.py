"""Application configuration for CropScan."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_type: str = "efficientnet_b4"
    model_weights_path: str = "./models/weights/efficientnet_b4_best.pth"
    model_class_names_path: str = "./data/processed/plantvillage/train"
    num_classes: int = 16
    confidence_threshold: float = 0.7

    ollama_base_url: str = "http://localhost:11434"
    vlm_model: str = "llava:7b"
    vlm_timeout_seconds: float = 25.0

    chroma_persist_dir: str = "./data/chroma_db"
    chroma_collection_name: str = "crop_knowledge"

    default_language: str = "en"
    indictrans_model_dir: str = "./models/indictrans2"

    tts_engine: str = "bark"
    bark_model_dir: str = "./models/bark"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_backend_store_uri: str = "./mlruns"

    @property
    def project_root(self) -> Path:
        """Absolute path to the repository root."""
        return Path(__file__).resolve().parents[1]

    def resolve_path(self, value: str) -> Path:
        """Resolve a config path relative to the repository root."""
        path = Path(value)
        return path if path.is_absolute() else (self.project_root / path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object."""
    return Settings()


settings = get_settings()
