# CropScan Task Tracker

CropScan is a full-stack crop disease detection and advisory system built for an FYP workflow:

- Upload/capture a leaf image
- Run CV prediction (EfficientNet-B4, PlantVillage 16 classes)
- Generate explainability heatmap (Grad-CAM)
- Generate agronomy advisory (RAG + LLaVA with fallback)
- Optional translation and TTS output

This repository is the active implementation workspace, with task tracking in `TODO.md`.

## Current Project Status

Implemented:

- End-to-end `predict -> advisory -> audio` flow in backend + frontend
- Model inference using trained `models/weights/efficientnet_b4_best.pth`
- Correct class-name mapping from PlantVillage labels
- Advisory JSON endpoint (`POST /advisory`) and optional SSE (`POST /advisory/stream`)
- Robust fallback advisory when RAG or Ollama is unavailable
- Demo sample endpoints (`GET /demo/samples`, `GET /demo/samples/{id}`)
- Evaluation outputs:
  - Confusion matrix image
  - Classification report JSON
  - Per-class accuracy chart

In progress / pending:

- Automated API test coverage (`test_predict.py`, `test_advisory.py`, `test_audio.py`)
- Real ICAR/FAO PDF ingestion quality validation
- Full Docker end-to-end run verification
- Production-grade UI polish and deployment phase

## Repository Structure

```text
backend/
  config.py
  main.py
  models/
  rag/
  routers/
  services/
  schemas.py
  requirements.txt
frontend/
  src/
ml/
  train.py
  evaluate.py
  dataset.py
models/
  weights/
data/
  processed/
  knowledge_base/
TODO.md
```

## Tech Stack

- Backend: FastAPI, Pydantic v2, Loguru
- CV/ML: PyTorch Lightning, timm, Albumentations, Grad-CAM
- Advisory: Ollama (LLaVA), ChromaDB, LangChain text splitting/loading
- Frontend: React + Vite + TailwindCSS
- Tracking: MLflow

## Local Setup (Windows / PowerShell)

### 1) Create and activate venv

```powershell
cd "C:\Users\husai\Desktop\Clg Projects\MV_Python\CropScan-Task-Tracker"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install backend dependencies

```powershell
pip install -r backend\requirements.txt
```

### 3) Install frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

### 4) Configure environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` as needed (weights path, model type, Ollama URL, etc.).

## Run the App

### Backend

```powershell
cd "C:\Users\husai\Desktop\Clg Projects\MV_Python\CropScan-Task-Tracker"
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd "C:\Users\husai\Desktop\Clg Projects\MV_Python\CropScan-Task-Tracker\frontend"
npm run dev
```

Frontend default URL: `http://localhost:5173`  
Backend default URL: `http://localhost:8000`

## API Overview

### Health

- `GET /health`

### Prediction

- `POST /predict`
- Multipart upload with `file`
- Returns class, crop, disease, confidence, top-k, heatmap, inference time

### Advisory

- `POST /advisory` (primary path, JSON response)
- `POST /advisory/stream` (optional SSE)

### Audio

- `POST /audio`

### Demo Mode

- `GET /demo/samples`
- `GET /demo/samples/{sample_id}`

## Model Training and Evaluation

### Resume/Run training

```powershell
cd "C:\Users\husai\Desktop\Clg Projects\MV_Python\CropScan-Task-Tracker"
python -m ml.train --preset run1 --data-root ".\data\processed\plantvillage"
```

### Evaluate trained model

```powershell
python -m ml.evaluate --data-dir ".\data\processed\plantvillage\test" --weights ".\models\weights\efficientnet_b4_best.pth"
```

Outputs are written to `models/evaluation/` (confusion matrix, report JSON, per-class chart).

## RAG Ingestion

Place PDFs in:

- `data/knowledge_base/icar/`
- `data/knowledge_base/fao/`

Run ingestion:

```powershell
python backend\rag\ingest.py
```

If network/model download is unavailable, ingestion gracefully falls back to JSONL manifest mode.

## Notes for Migration to New Chat

- Primary source of truth for progress is `TODO.md`.
- Advisory endpoint contract is now JSON-first (`POST /advisory`), with SSE optional.
- Demo routes are available and useful for presentation even without live camera uploads.
- Fallback paths are implemented for VLM and RAG failure scenarios to avoid blank outputs.

## Next Recommended Focus

1. Write and run backend integration tests for `/predict`, `/advisory`, `/audio`.
2. Validate real ICAR/FAO retrieval quality after adding PDFs.
3. Run full Docker E2E check and finalize deployment pipeline.
