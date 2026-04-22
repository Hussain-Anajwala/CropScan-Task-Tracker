# TODO.md - CropScan Task Tracker

> Update this file as you complete tasks. Use `[x]` for done, `[-]` for in-progress, `[ ]` for pending.
> Code-implemented items are marked done even when real datasets, models, or manual validation are still pending.

---

## Phase 0 - Project Setup
> Target: Day 1-2

- [x] Create GitHub repo with this file structure
- [x] Set up Python virtual environment
- [x] Create `backend/requirements.txt` with dependencies from `CLAUDE.md`
- [x] Set up `frontend/` with Vite + React + TailwindCSS
- [x] Create `.env.example` with env var keys
- [x] Set up `docker-compose.yml` with `backend`, `frontend`, `ollama`
- [x] Pull Ollama + LLaVA model
- [x] Set up MLflow tracking server support
- [x] Create `ml/experiments/` folder
- [x] Verify GPU availability

---

## Phase 1 - Data Pipeline
> Target: Week 1-2

### Dataset Download
- [ ] Download PlantVillage from Kaggle
- [ ] Download PlantDoc dataset
- [ ] Download Cassava Leaf Disease from Kaggle
- [ ] Verify class distribution on real dataset with `python ml/dataset.py --stats`

### Preprocessing Pipeline
- [x] Create `backend/services/preprocessing.py`
  - [x] `resize_image(image, size=224)`
  - [x] `apply_clahe(image)`
  - [x] `remove_background(image)`
  - [x] `normalize(image)`
- [x] Create `ml/transforms.py` with Albumentations pipeline
  - [x] Training transforms
  - [x] Validation transforms
- [x] Create `ml/dataset.py`
  - [x] `PlantDiseaseDataset(Dataset)` class
  - [x] Loads images from `class_name/image.jpg`
  - [x] Returns `(image_tensor, label, image_path)`
  - [x] `get_class_names()` utility
- [x] Write `ml/split_dataset.py`
- [x] Run split logic and verify class ratios on synthetic data
- [x] Unit test equivalent: load 5 batches, check shapes and label ranges

---

## Phase 2 - CV Model Training
> Target: Week 3-4

### Model Setup
- [x] Create `ml/train.py` using PyTorch Lightning
  - [x] `CropDiseaseModule(LightningModule)` class
  - [x] `configure_optimizers()` with AdamW + cosine scheduler
  - [x] `training_step()`, `validation_step()`, `test_step()`
  - [x] Log loss, accuracy, and F1 to MLflow
- [x] Create `backend/models/classifier.py`
  - [x] `load_model(model_type, weights_path, num_classes)`
  - [x] `predict(image_tensor)`
  - [x] Singleton-style caching

### Training Runs
- [x] Run 1: EfficientNet-B4 on PlantVillage and save `models/weights/efficientnet_b4_best.pth`
- [ ] Run 2: ViT-Base-Patch16-224 and compare accuracy + inference time
- [ ] Run 3: Fine-tune best model on PlantVillage + PlantDoc combined
- [x] Log all runs to MLflow with hyperparameters + metrics support
- [x] Generate confusion matrix on test set support in `ml/evaluate.py`
  - [x] Save JSON evaluation summary with per-class accuracy

### Grad-CAM
- [x] Create `backend/services/gradcam.py`
  - [x] `generate_heatmap(...)`
  - [x] `overlay_heatmap(...)`
  - [x] `heatmap_to_base64(...)`
  - [x] Use `pytorch-grad-cam`
- [-] Test Grad-CAM on 20 real test images
  Implemented export pipeline in `ml/evaluate.py`; real validation still needs trained weights and test data.

---

## Phase 3 - VLM + RAG Pipeline
> Target: Week 5-6

### RAG Knowledge Base
- [ ] Collect ICAR Bulletins (PDF)
- [ ] Collect FAO documents (PDF)
- [x] Create `backend/rag/ingest.py`
  - [x] Load PDFs with `PyPDFLoader`
  - [x] Chunk with `RecursiveCharacterTextSplitter`
  - [x] Embed with `all-MiniLM-L6-v2`
  - [x] Store in ChromaDB
  - [x] Log chunks ingested per document
- [x] Create `backend/rag/retriever.py`
  - [x] `retrieve_context(disease_name, crop_name, top_k=5)`
  - [ ] Validate retrieval quality on real ICAR content

### VLM Advisory
- [x] Create `backend/models/vlm.py`
  - [x] `OllamaVLMClient` class
  - [x] `generate_advisory(...)` async streaming generator
  - [x] Use prompt templates from `PROMPTS.md`
  - [x] Timeout/fallback behavior
- [x] Create `backend/services/advisory_chain.py`
  - [x] Orchestrates retrieve -> prompt -> stream -> parse
  - [x] Parses `severity`, `treatment`, `prevention`, `sources`
- [ ] Test CLI on a real image and verify streamed output + cited sources

---

## Phase 4 - Multilingual Output + TTS
> Target: Week 7-8

### Translation
- [ ] Install IndicTrans2
- [x] Create `backend/services/translation.py`
  - [x] `translate(text, target_lang)`
  - [x] Support `hi`, `ta`, `te`, `mr`, `en`
  - [x] Cache model/fallback loader
  - [x] Handle long-text fallback behavior
- [ ] Test translations with sample advisories and human review

### TTS
- [x] Create `backend/services/tts.py`
  - [x] `generate_audio(text, language)`
  - [x] Primary Bark path
  - [x] gTTS fallback path
  - [x] `wav_to_base64(wav_bytes)`
- [ ] Benchmark Bark generation time on target hardware

---

## Phase 5 - FastAPI Backend
> Target: Week 9-10

### Core Setup
- [x] Create `backend/main.py`
  - [x] Lifespan context
  - [x] CORS middleware from env
  - [x] Structured exception handler
  - [x] Include `predict`, `advisory`, `audio` routers
- [x] Create `backend/schemas.py` with Pydantic v2 models
  - [x] `PredictRequest`, `PredictResponse`
  - [x] `AdvisoryRequest`, `AdvisoryResponse`
  - [x] `AudioRequest`, `AudioResponse`
  - [x] `ErrorResponse`
- [x] Create `backend/config.py` using `pydantic-settings`

### Routers
- [x] Create `backend/routers/predict.py`
  - [x] Decode base64 -> preprocess -> classify -> gradcam -> return
  - [x] Reject invalid image payloads
  - [x] Return heatmap as base64 PNG
- [x] Create `backend/routers/advisory.py`
  - [x] SSE streaming endpoint
  - [x] Token events
  - [x] Final structured advisory event
- [x] Create `backend/routers/audio.py`
  - [x] Generate audio and return base64
  - [x] 10-minute in-memory cache

### Testing
- [ ] Write `backend/tests/test_predict.py`
- [ ] Write `backend/tests/test_advisory.py`
- [ ] Write `backend/tests/test_audio.py`
- [ ] Run full backend test suite with `pytest`
  Multipart `/predict` inference path is now wired to the trained EfficientNet-B4 checkpoint; automated API tests still need to be added.

### Docker
- [x] Create `Dockerfile.backend`
- [x] Create `docker-compose.yml`
- [ ] Test `docker-compose up` end to end on a Docker-enabled machine
- [ ] Verify `curl http://localhost:8000/health`

---

## Phase 6 - React Frontend
> Target: Week 11-12

### Components
- [x] `src/api/cropscan.js`
  - [x] `predictDisease(imageBase64)`
  - [x] `streamAdvisory(...)`
  - [x] `generateAudio(text, language)`
- [x] `src/components/CameraCapture.jsx`
  - [x] Toggle upload/camera
  - [x] Camera capture
  - [x] File upload to base64
  - [x] Preview selected image
- [x] `src/components/HeatmapOverlay.jsx`
- [x] `src/components/ResultCard.jsx`
- [x] `src/components/AudioPlayer.jsx`
- [x] `src/components/LanguageSelector.jsx`

### Pages
- [x] `src/pages/Home.jsx`
- [x] `src/pages/About.jsx`

### State & Flow
- [x] `src/hooks/useCamera.js`
- [x] Home-page state for `image`, `prediction`, `advisory`, `audioUrl`, `language`, `isLoading`
- [x] Loading and error states for the main flow
- [x] Upload image -> `/predict` multipart call -> prediction -> advisory stream flow

### UI Polish
- [x] Mobile-first responsive structure
- [x] High-contrast light UI
- [ ] Skeleton loader while prediction is in progress
- [x] Error states for camera/API issues
- [ ] PWA manifest + service worker

---

## Phase 7 - Custom Dataset + Research + Deploy
> Target: Week 13-14

### Custom India Dataset
- [ ] Collect 500+ photos of Indian crop leaves
- [ ] Use diseases common to Maharashtra, Punjab, Tamil Nadu
- [ ] Label using Label Studio
- [ ] Split and add to training pipeline
- [ ] Re-train with custom data and report accuracy delta
- [ ] Upload dataset to HuggingFace Datasets

### Evaluation
- [ ] Generate full evaluation report
- [ ] Latency benchmarks across classifier, VLM, advisory, and TTS
- [ ] User study with SUS questionnaire

### Deployment
- [ ] Deploy demo to HuggingFace Spaces
- [ ] Deploy full app to GCP Cloud Run
- [ ] Configure custom domain (optional)

### Research Paper
- [ ] Write `paper/cropscan_paper.tex`
- [ ] Submit to CVPR 2026 CV4A workshop or equivalent
- [ ] Upload preprint to arXiv

---

## Backlog

- [ ] Native Android app
- [ ] Real-time video analysis
- [ ] Multi-plant detection in one image
- [ ] Soil quality analysis module
- [ ] WhatsApp Bot integration
- [ ] Offline-capable VLM
- [ ] Fine-tune LLaVA on CropScan advisory pairs
