# CLAUDE.md — CropScan Project Context

> This file is the single source of truth for any AI coding agent (Claude Code, Codex, Cursor, Copilot) working on this project.
> Read this file fully before writing any code, creating any file, or making any architectural decision.

---

## Project Identity

**Name:** CropScan  
**Type:** Final Year Project (FYP) + Resume-grade portfolio project  
**Domain:** Agricultural AI — Machine Vision + Generative AI  
**Owner:** Hussain (Computer Engineering, Honours in Generative AI)  
**Status:** In active development

---

## What CropScan Does

CropScan is an AI-powered crop disease detection and advisory system. A farmer photographs a diseased leaf using their phone. CropScan:

1. Classifies the disease using a fine-tuned Vision Transformer / EfficientNet model
2. Generates a Grad-CAM heatmap showing which leaf region triggered the prediction
3. Sends the image + classifier result to a locally-hosted Vision-Language Model (LLaVA via Ollama)
4. Retrieves relevant treatment context from a ChromaDB RAG knowledge base (ICAR/FAO docs)
5. Returns a natural-language advisory: disease name, severity, recommended treatment
6. Translates the advisory into the user's Indian language (Hindi, Tamil, Telugu, Marathi) via IndicTrans2
7. Converts the advisory to speech using Bark TTS

---

## Architecture Overview

```
Mobile/Web Camera
      ↓
Image Preprocessing (OpenCV, rembg, Albumentations)
      ↓
CV Classifier (EfficientNet-B4 or ViT-Base via timm + PyTorch)
      ↓ class + confidence + Grad-CAM heatmap
VLM Advisory Engine (LLaVA-1.6 via Ollama)
      ↓ (augmented by)
RAG Layer (ChromaDB + sentence-transformers + ICAR/FAO docs)
      ↓ advisory text
Multilingual Translation (IndicTrans2 — AI4Bharat)
      ↓
TTS Audio Output (Bark / gTTS)
      ↓
FastAPI Backend → React Frontend
```

---

## Repository Structure

```
cropscan/
├── CLAUDE.md              ← You are here
├── PRD.md                 ← Full product requirements
├── TODO.md                ← Task tracker by phase
├── PROMPTS.md             ← LLM prompt templates for all modules
│
├── backend/
│   ├── main.py            ← FastAPI app entry point
│   ├── routers/
│   │   ├── predict.py     ← POST /predict — classifier endpoint
│   │   ├── advisory.py    ← POST /advisory — VLM + RAG endpoint
│   │   └── audio.py       ← POST /audio — TTS endpoint
│   ├── models/
│   │   ├── classifier.py  ← EfficientNet/ViT model loader + inference
│   │   └── vlm.py         ← Ollama LLaVA client wrapper
│   ├── rag/
│   │   ├── ingest.py      ← Load docs → chunk → embed → ChromaDB
│   │   └── retriever.py   ← Query ChromaDB, return context
│   ├── services/
│   │   ├── preprocessing.py  ← CLAHE, background removal, augmentation
│   │   ├── gradcam.py        ← Grad-CAM heatmap generation
│   │   ├── translation.py    ← IndicTrans2 wrapper
│   │   └── tts.py            ← Bark/gTTS wrapper
│   ├── schemas.py         ← Pydantic request/response models
│   ├── config.py          ← App config, env vars, model paths
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── CameraCapture.jsx   ← webcam / file upload
│   │   │   ├── ResultCard.jsx      ← disease + confidence + advisory
│   │   │   ├── HeatmapOverlay.jsx  ← canvas overlay on image
│   │   │   └── AudioPlayer.jsx     ← TTS playback
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── About.jsx
│   │   ├── hooks/
│   │   │   └── useCamera.js
│   │   └── api/
│   │       └── cropscan.js         ← axios API client
│   ├── package.json
│   └── tailwind.config.js
│
├── ml/
│   ├── train.py           ← PyTorch Lightning training script
│   ├── evaluate.py        ← Metrics, confusion matrix, Grad-CAM eval
│   ├── dataset.py         ← PyTorch Dataset class for PlantVillage etc.
│   ├── transforms.py      ← Albumentations augmentation pipeline
│   └── experiments/       ← MLflow / W&B configs
│
├── data/
│   ├── raw/               ← Downloaded datasets (gitignored)
│   ├── processed/         ← Cleaned + split datasets
│   └── knowledge_base/    ← ICAR/FAO PDFs for RAG ingestion
│
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── .env.example
```

---

## Tech Stack (Strict — Do Not Deviate)

| Layer | Tool | Notes |
|---|---|---|
| CV Model | EfficientNet-B4, ViT-Base | via `timm` library |
| Training | PyTorch, PyTorch Lightning | Use Lightning for training loops |
| Augmentation | Albumentations | NOT torchvision transforms |
| Explainability | pytorch-grad-cam | GradCAM, EigenCAM |
| Background removal | rembg | U2-Net based |
| VLM | LLaVA-1.6 (llava:13b) | via Ollama locally |
| Orchestration | LangChain, LangGraph | For RAG + VLM chain |
| Vector DB | ChromaDB | Persistent local store |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | For RAG |
| Translation | IndicTrans2 (AI4Bharat) | Open source only |
| TTS | Bark (suno-ai/bark) | Primary; gTTS as fallback |
| Backend | FastAPI, Uvicorn, Pydantic v2 | Async; SSE for streaming |
| Frontend | React 18, TailwindCSS, shadcn/ui | Vite build |
| Experiment tracking | MLflow | Local server |
| Containerisation | Docker, Docker Compose | Full stack in one command |
| Deployment | HuggingFace Spaces (demo), GCP Cloud Run (prod) | |

**ALL tools must be open source. No paid API calls in the core pipeline.**

---

## Coding Standards

### Python (backend + ML)
- Python 3.11+
- Type hints on all function signatures
- Pydantic v2 for all data models
- Async functions for all FastAPI endpoints (`async def`)
- Use `loguru` for logging, not `print()`
- Configuration via `.env` + `pydantic-settings` (never hardcode paths or keys)
- All ML model weights stored in `models/weights/` (gitignored)
- Docstrings on all public functions — Google style

### JavaScript / React (frontend)
- React 18 with functional components and hooks only — no class components
- TailwindCSS for all styling — no inline styles, no CSS modules
- shadcn/ui for UI components
- Axios for API calls, wrapped in `src/api/cropscan.js`
- Mobile-first responsive design
- No TypeScript (keep it simple for now)

### Git
- Branch naming: `feature/module-name`, `fix/bug-description`
- Commit messages: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- Never commit model weights, datasets, or `.env` files

---

## Environment Variables

```env
# .env (copy from .env.example)

# Model
MODEL_TYPE=efficientnet_b4          # or vit_base_patch16_224
MODEL_WEIGHTS_PATH=./models/weights/best_model.pth
NUM_CLASSES=38
CONFIDENCE_THRESHOLD=0.7

# Ollama / VLM
OLLAMA_BASE_URL=http://localhost:11434
VLM_MODEL=llava:13b

# ChromaDB
CHROMA_PERSIST_DIR=./data/chroma_db
CHROMA_COLLECTION_NAME=crop_knowledge

# Translation
DEFAULT_LANGUAGE=en                 # en, hi, ta, te, mr
INDICTRANS_MODEL_DIR=./models/indictrans2

# TTS
TTS_ENGINE=bark                     # bark or gtts
BARK_MODEL_DIR=./models/bark

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:5173"]
```

---

## Key Design Decisions

1. **Local-first VLM:** LLaVA runs via Ollama — no OpenAI API dependency. This keeps costs zero and the stack fully open source.

2. **Classifier first, VLM second:** The CV classifier runs fast (< 200ms). The VLM only runs after classification — it receives the predicted class as context, making its advisory more grounded and accurate.

3. **RAG grounds the advisory:** The VLM alone can hallucinate treatment advice. The RAG layer retrieves verified ICAR/FAO content and injects it into the VLM prompt as context.

4. **Streaming advisory:** FastAPI streams the VLM response token-by-token via SSE so the frontend can show real-time text generation.

5. **Grad-CAM is required:** Every prediction must return a heatmap. This is non-negotiable for the research paper (explainability is a key contribution).

6. **Modular services:** Each service (preprocessing, gradcam, translation, tts) is independently testable. Do not couple them.

---

## Datasets

| Dataset | Location | Purpose |
|---|---|---|
| PlantVillage | Kaggle / HuggingFace (`plant-disease`) | Primary training (87K images, 38 classes) |
| PlantDoc | GitHub (`pratikkayal/PlantDoc-Dataset`) | Robustness evaluation |
| Cassava Leaf Disease | Kaggle (`cassava-leaf-disease-classification`) | Transfer learning |
| ICAR Bulletins (PDF) | `data/knowledge_base/icar/` | RAG knowledge base |
| FAO Crop Protection PDFs | `data/knowledge_base/fao/` | RAG knowledge base |
| Custom India Dataset | `data/raw/custom/` | Research novelty contribution |

---

## API Contract

### POST /predict
```json
Request:  { "image": "<base64 string>" }
Response: {
  "disease": "Tomato Late Blight",
  "confidence": 0.94,
  "crop": "Tomato",
  "heatmap": "<base64 PNG string>",
  "inference_time_ms": 180
}
```

### POST /advisory (streaming SSE)
```json
Request:  { "image": "<base64>", "disease": "Tomato Late Blight", "language": "hi" }
Response: SSE stream of advisory tokens, then final JSON:
{
  "advisory": "...",
  "severity": "High",
  "treatment": ["..."],
  "sources": ["ICAR Bulletin 2023", "..."],
  "language": "hi"
}
```

### POST /audio
```json
Request:  { "text": "...", "language": "hi" }
Response: { "audio": "<base64 WAV string>" }
```

---

## What NOT to Do

- Do NOT use OpenAI, Gemini, or any paid API in the core pipeline
- Do NOT use torchvision transforms — use Albumentations only
- Do NOT hardcode file paths — use config.py
- Do NOT use class components in React
- Do NOT write synchronous FastAPI endpoints — always `async def`
- Do NOT skip Grad-CAM — every prediction must return a heatmap
- Do NOT store model weights in Git
- Do NOT mix LangChain v1 and v2 APIs — use LangChain v0.3+

---

## Running the Project

```bash
# 1. Start Ollama and pull LLaVA
ollama pull llava:13b

# 2. Start full stack
docker-compose up --build

# 3. Or run individually
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# 4. Run ML training
cd ml && python train.py --model efficientnet_b4 --epochs 30

# 5. Ingest RAG knowledge base
cd backend && python rag/ingest.py --source ../data/knowledge_base/
```
