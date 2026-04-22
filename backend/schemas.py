"""Pydantic schemas for CropScan API contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    """Request schema for disease prediction."""

    image: str = Field(min_length=1)


class TopKPrediction(BaseModel):
    """Single ranked prediction result."""

    class_name: str = Field(alias="class")
    confidence: float
    disease: str
    crop: str

    model_config = ConfigDict(populate_by_name=True)


class PredictResponse(BaseModel):
    """Response schema for classifier predictions."""

    class_name: str = Field(alias="class")
    disease: str
    confidence: float
    crop: str
    top_k: list[TopKPrediction] = Field(default_factory=list)
    heatmap: str | None = None
    inference_time_ms: float
    environmental_stats: dict | None = None

    model_config = ConfigDict(populate_by_name=True)


class AdvisoryRequest(BaseModel):
    """Request schema for advisory generation."""

    image: str = Field(min_length=1)
    disease: str = Field(min_length=1)
    crop: str = "Unknown"
    confidence: float = 0.8
    language: str = Field(default="en", min_length=2, max_length=5)


class AdvisoryResponse(BaseModel):
    """Structured advisory response."""

    advisory: str
    severity: str
    treatment: list[str] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    language: str


class AudioRequest(BaseModel):
    """Request schema for audio generation."""

    text: str = Field(min_length=1)
    language: str = Field(default="en", min_length=2, max_length=5)


class AudioResponse(BaseModel):
    """Response schema for audio generation."""

    audio: str
    cached: bool = False


class ErrorResponse(BaseModel):
    """Standard error shape."""

    error: str
    detail: str


class HealthResponse(BaseModel):
    """Healthcheck response schema."""

    status: str
