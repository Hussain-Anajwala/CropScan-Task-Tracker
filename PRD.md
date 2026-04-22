# PRD — CropScan
## Product Requirements Document v1.0

**Project:** CropScan — Agricultural Disease Detection + Multimodal Advisory  
**Author:** Hussain  
**Date:** April 2026  
**Status:** Approved — In Development  
**Classification:** Final Year Project (FYP) + Portfolio  

---

## 1. Executive Summary

CropScan is an AI-powered mobile-accessible web application that enables farmers to photograph a crop leaf and receive an instant disease diagnosis, severity assessment, and actionable treatment advisory in their native language — powered entirely by open-source models running locally.

The system fuses a fine-tuned Vision Transformer classifier with a locally-hosted Vision-Language Model (LLaVA), a RAG-based agronomic knowledge base (ChromaDB + ICAR/FAO documents), multilingual translation (IndicTrans2), and text-to-speech output (Bark TTS).

---

## 2. Problem Statement

### The Core Problem
- Indian farmers lose 20–30% of annual crop yield to diseases like leaf blight, rust, mosaic virus, and bacterial spot.
- Expert agronomists are unavailable in rural areas — the national ratio is 1 agronomist per 1,000 farmers.
- Existing apps (Plantix, etc.) only return a class label with minimal explanation.
- Advisory content is almost never available in regional Indian languages.
- Farmers cannot act on a disease name alone — they need treatment steps.

### What CropScan Solves
- Instant disease classification from a phone photo (no agronomist needed)
- Explainable AI — Grad-CAM heatmap shows *why* the model made its prediction
- Full natural-language advisory: cause, severity, treatment, prevention
- Output in Hindi, Tamil, Telugu, Marathi — with audio playback
- Grounded in verified ICAR and FAO guidelines via RAG (no hallucination)

---

## 3. Goals & Success Metrics

### Primary Goals
| Goal | Metric | Target |
|---|---|---|
| Disease classification accuracy | Top-1 accuracy on PlantVillage test set | ≥ 93% |
| Real-world robustness | Accuracy on PlantDoc test set | ≥ 78% |
| Inference speed | End-to-end time (classify + advisory) | < 8 seconds |
| Classifier latency | Time to prediction only | < 300ms |
| Advisory quality | BLEU score vs expert-written advisories | ≥ 0.35 |
| Multilingual coverage | Languages supported | 5 (EN, HI, TA, TE, MR) |
| Uptime | System availability | ≥ 99% (demo deployment) |

### Secondary Goals
- Publishable research paper (CVPR CV4A workshop or equivalent)
- Open-source India-specific crop disease dataset (novel contribution)
- Live demo deployable on HuggingFace Spaces

---

## 4. Target Users

### Primary User: Rural Indian Farmer
- Has a basic Android smartphone with a camera
- Limited digital literacy — UI must be extremely simple
- Prefers audio over text
- Speaks Hindi, Tamil, Telugu, or Marathi — not English
- Cannot wait more than 10 seconds for a result

### Secondary User: Agriculture Extension Worker
- Uses CropScan in the field with farmers
- Needs to share results / export reports
- May need batch analysis of multiple plants

### Tertiary User: Researcher / Evaluator
- Needs access to model metrics, confidence scores, Grad-CAM heatmaps
- Evaluates the system for publication / deployment decisions

---

## 5. Features

### 5.1 Core Features (MVP — Must Have)

#### F1: Image Input
- Capture image via device camera (MediaDevices API)
- Upload image from gallery / file system
- Supported formats: JPG, PNG, WEBP
- Max file size: 10MB
- Auto-resize to 224×224 for model input (display full resolution)

#### F2: Disease Classification
- Model: EfficientNet-B4 fine-tuned on PlantVillage (38 classes, 14 crops)
- Output: disease name, crop name, confidence score (0–100%)
- Reject low-confidence predictions (< 70%) with "unclear — try again" message
- Return Grad-CAM heatmap overlaid on original image

#### F3: VLM Advisory Generation
- Input: original image + predicted disease + confidence
- Model: LLaVA-1.6 (13B) via Ollama
- RAG context injected from ChromaDB (ICAR/FAO docs)
- Streaming output — advisory appears word-by-word in real time
- Advisory structure:
  - Disease overview (2–3 sentences)
  - Severity level: Low / Moderate / High / Critical
  - Symptoms to look for
  - Recommended treatment (step-by-step)
  - Preventive measures
  - Source citations (ICAR bulletin, FAO document)

#### F4: Multilingual Output
- Languages: English (default), Hindi, Tamil, Telugu, Marathi
- Translation via IndicTrans2 (AI4Bharat)
- Language selector in UI (flag icons)
- Advisory stored in original language; translated on demand

#### F5: Text-to-Speech
- Convert advisory to audio using Bark TTS
- Fallback to gTTS if Bark is unavailable
- Audio playback controls: play, pause, speed (0.75×, 1×, 1.25×)
- Auto-play option (enabled by default on mobile)

#### F6: Result Display
- Disease name + confidence badge
- Grad-CAM heatmap overlay (toggle on/off)
- Advisory text (scrollable)
- Audio player
- Language selector
- Share button (copy link / download PDF summary)

### 5.2 Enhanced Features (Should Have)

#### F7: Crop Selection Context
- Optional: user selects crop type before scanning (improves classification accuracy)
- Dropdown: Tomato, Potato, Corn, Wheat, Rice, Sugarcane, Mustard, Cotton, and others

#### F8: History & Scan Log
- Store last 10 scans in browser localStorage
- Each entry: thumbnail, disease name, date, confidence
- Tap to review previous result

#### F9: Offline Classifier
- Download compressed EfficientNet model as ONNX
- Run inference client-side via ONNX Runtime Web
- Works without internet (advisory requires connection to Ollama backend)

#### F10: Batch Analysis
- Upload up to 5 images at once
- Returns summary table: image | crop | disease | confidence
- Export as CSV

### 5.3 Research Features (Nice to Have)

#### F11: Model Comparison Dashboard
- Side-by-side: EfficientNet-B4 vs ViT-Base predictions on same image
- Confidence comparison, inference time comparison

#### F12: Advisory Quality Rating
- Thumbs up / thumbs down on advisory
- Optional text feedback
- Stored for model fine-tuning dataset

#### F13: Expert Override Mode
- Agronomist can correct the disease label
- Correction stored for fine-tuning pipeline

---

## 6. Non-Functional Requirements

### Performance
- Classifier inference: < 300ms on CPU, < 50ms on GPU
- VLM first token: < 3 seconds (streaming starts immediately after)
- Full advisory generation: < 30 seconds
- Frontend initial load: < 2 seconds

### Reliability
- System must handle corrupt / non-leaf images gracefully
- VLM timeout after 60 seconds — fallback to template-based advisory
- All errors must return structured JSON (never raw tracebacks)

### Security
- No user data stored on server beyond the request lifecycle
- Images processed in memory, not written to disk
- CORS restricted to known origins
- Rate limiting: 10 requests/minute per IP

### Scalability
- Backend stateless — horizontally scalable
- Ollama runs as a separate service (can be scaled independently)
- ChromaDB persists to disk (no in-memory only mode)

### Accessibility
- WCAG 2.1 AA compliance
- All images have alt text
- Audio controls keyboard-accessible
- Minimum touch target size: 44×44px

---

## 7. System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    React Frontend                    │
│  CameraCapture → ResultCard → HeatmapOverlay         │
│  AudioPlayer → LanguageSelector → HistoryPanel       │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────▼──────────────────────────────┐
│                   FastAPI Backend                    │
│  /predict  /advisory (SSE)  /audio                   │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐ │
│  │ Classifier  │ │ VLM Service  │ │ TTS Service   │ │
│  │ EfficientNet│ │ Ollama Client│ │ Bark / gTTS   │ │
│  │ Grad-CAM    │ └──────┬───────┘ └───────────────┘ │
│  └─────────────┘        │                            │
│  ┌──────────────────────▼──────────────────────────┐ │
│  │                 RAG Layer                       │ │
│  │  ChromaDB ← sentence-transformers               │ │
│  │  LangChain Retriever → Context injection        │ │
│  └─────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────┐ │
│  │           Translation Service                   │ │
│  │  IndicTrans2 — EN → HI / TA / TE / MR           │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               Ollama (separate service)              │
│               LLaVA-1.6 13B running locally          │
└─────────────────────────────────────────────────────┘
```

---

## 8. Data Requirements

### Training Data
| Dataset | Size | Classes | Use |
|---|---|---|---|
| PlantVillage | 87,000 images | 38 | Primary training |
| PlantDoc | 2,598 images | 27 | Robustness eval |
| Cassava Leaf Disease (Kaggle) | 21,397 images | 5 | Transfer learning |
| Custom India Dataset | 500+ images | TBD | Novel contribution |

### RAG Knowledge Base
| Source | Format | Content |
|---|---|---|
| ICAR Crop Protection Bulletins | PDF | Disease identification + treatment |
| FAO Integrated Pest Management | PDF | Prevention + organic treatment |
| State Agriculture Dept Guidelines | PDF | Region-specific recommendations |
| PestDisease.net structured data | Scraped JSON | Symptoms + lifecycle |

### Data Split (Training)
- Train: 70%
- Validation: 15%
- Test: 15%
- Stratified split — equal class representation across all splits

---

## 9. UI/UX Requirements

### Design Principles
- Mobile-first (primary users are on smartphones)
- Single-screen flow: capture → loading → result
- Maximum 3 taps from open to result
- High contrast — usable in outdoor sunlight
- Font size minimum 16px for body text

### Key Screens

**Screen 1 — Home / Capture**
- Large camera capture button (center)
- File upload option (secondary)
- Optional: crop selector dropdown
- Language selector (top right)
- Recent scans (bottom strip, last 3)

**Screen 2 — Processing**
- Full-screen loading state
- Progress: "Analyzing leaf..." → "Generating advisory..." → "Translating..."
- Animated leaf scan visual

**Screen 3 — Results**
- Image with Grad-CAM heatmap (toggle)
- Disease name (large, bold) + confidence badge
- Severity chip (color-coded: green/yellow/orange/red)
- Advisory text (streaming, scrollable)
- Audio player (auto-play on mobile)
- Language selector (re-translates on change)
- Share button + Scan Again button

---

## 10. Integration Points

| Integration | Purpose | Method |
|---|---|---|
| Ollama (local) | LLaVA inference | HTTP REST (ollama client lib) |
| ChromaDB (local) | Vector similarity search | Python client |
| IndicTrans2 (local) | Translation | Python subprocess / direct import |
| Bark (local) | TTS generation | Python direct import |
| HuggingFace Hub | Model download | `huggingface_hub` library |
| MLflow (local) | Experiment tracking | Python client |

---

## 11. Out of Scope (v1.0)

- Native mobile app (iOS/Android) — web app only
- Real-time video analysis — single image only
- Soil quality analysis — leaves only
- Price recommendations or market data
- Multi-plant detection in one image (single leaf crop)
- User accounts / authentication
- Cloud-synced history

---

## 12. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLaVA hallucinating treatment advice | Medium | High | RAG layer with verified sources; source citations required |
| PlantVillage ≠ real field conditions | High | Medium | Test on PlantDoc; collect custom India dataset |
| Bark TTS too slow (> 10s) | Medium | Medium | gTTS fallback; async generation |
| IndicTrans2 translation quality | Low | Medium | Human evaluation; fallback to English |
| Ollama GPU memory (13B model) | Medium | High | Use llava:7b as fallback; quantized 4-bit version |

---

## 13. Milestones

| Phase | Weeks | Deliverable |
|---|---|---|
| 1. Foundation | 1–2 | Data pipeline, preprocessing, project setup |
| 2. CV Model | 3–4 | Trained classifier + Grad-CAM + evaluation report |
| 3. VLM + RAG | 5–6 | End-to-end advisory pipeline (CLI working) |
| 4. Multilingual + TTS | 7–8 | Audio advisory in 4 Indian languages |
| 5. Backend API | 9–10 | FastAPI with streaming SSE, Dockerized |
| 6. Frontend | 11–12 | Full React web app, mobile-responsive |
| 7. Custom Dataset + Deploy | 13–14 | Live deployment + paper draft submitted |

---

## 14. Appendix — Disease Classes (PlantVillage)

Apple (4 classes) · Blueberry · Cherry · Corn (4) · Grape (4) · Orange · Peach · Bell Pepper (2) · Potato (3) · Raspberry · Soybean · Squash · Strawberry · Tomato (10 classes including healthy)

Full list: https://github.com/spMohanty/PlantVillage-Dataset
