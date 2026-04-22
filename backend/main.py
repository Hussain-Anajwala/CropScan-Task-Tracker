"""FastAPI entry point for the CropScan backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.models.classifier import load_class_names, load_model
from backend.rag.retriever import retrieve_context
from backend.routers.advisory import router as advisory_router
from backend.routers.audio import router as audio_router
from backend.routers.predict import router as predict_router
from backend.schemas import ErrorResponse, HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up lightweight singleton resources."""
    class_names_path = settings.resolve_path(settings.model_class_names_path)
    weights_path = settings.resolve_path(settings.model_weights_path)
    exported_class_names = weights_path.parent / "class_names.json"
    class_names = load_class_names(
        exported_class_names if exported_class_names.exists() else class_names_path,
        fallback_dir=class_names_path if class_names_path.exists() else None,
    )
    app.state.classifier = load_model(
        model_type=settings.model_type,
        weights_path=weights_path,
        num_classes=max(len(class_names), 3),
        class_names=class_names,
    )
    app.state.rag_ready = bool(retrieve_context("blight", "tomato", top_k=1) or True)
    yield


app = FastAPI(title="CropScan API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_response(status_code: int, error: str, detail: str) -> JSONResponse:
    payload = ErrorResponse(error=error, detail=detail)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@app.exception_handler(Exception)
async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """Return a structured error response."""
    return _error_response(status_code=500, error="internal_error", detail=str(exc))


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Normalize HTTP exceptions into the standard JSON error shape."""
    return _error_response(status_code=exc.status_code, error="http_error", detail=str(exc.detail))


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Normalize validation errors into the standard JSON error shape."""
    detail = "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )
    return _error_response(status_code=422, error="validation_error", detail=detail)


def _demo_sample_files(limit: int = 3) -> list[Path]:
    sample_root = settings.resolve_path("./data/processed/plantvillage/test")
    if not sample_root.exists():
        return []

    sample_files: list[Path] = []
    for class_dir in sorted(entry for entry in sample_root.iterdir() if entry.is_dir()):
        for image_path in sorted(class_dir.rglob("*")):
            if image_path.is_file() and image_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                sample_files.append(image_path)
                break
        if len(sample_files) >= limit:
            break
    return sample_files


app.include_router(predict_router)
app.include_router(advisory_router)
app.include_router(audio_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Simple healthcheck used by local development and Docker."""
    return HealthResponse(status="ok")


@app.get("/demo/samples")
async def demo_samples() -> JSONResponse:
    """Return a few sample images from the processed test split for demo mode."""
    samples = []
    for sample_path in _demo_sample_files():
        label = sample_path.parent.name
        if "___" in label:
            crop, disease = label.split("___", 1)
        else:
            crop, disease = label, label
        samples.append(
            {
                "id": sample_path.stem,
                "label": label,
                "crop": crop,
                "disease": disease,
                "image_url": f"/demo/samples/{sample_path.stem}",
            }
        )
    return JSONResponse(content={"samples": samples})


@app.get("/demo/samples/{sample_id}")
async def demo_sample_image(sample_id: str) -> FileResponse:
    """Serve a demo sample image by id."""
    for sample_path in _demo_sample_files(limit=12):
        if sample_path.stem == sample_id:
            return FileResponse(sample_path)
    raise HTTPException(status_code=404, detail="Demo sample not found.")
