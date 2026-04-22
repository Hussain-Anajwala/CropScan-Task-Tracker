# PROMPTS.md — CropScan Prompt Templates

> This file contains every prompt template used in CropScan's LLM/VLM pipeline.
> Reference these in code using the template names. Do NOT hardcode prompts inline.
> All prompts use Python f-string style `{variable}` placeholders.

---

## 1. VLM Advisory Prompt (Main)

**Used in:** `backend/models/vlm.py` → `generate_advisory()`  
**Model:** LLaVA-1.6 via Ollama  
**Variables:** `disease_name`, `crop_name`, `confidence_pct`, `rag_context`

```
ADVISORY_SYSTEM_PROMPT = """You are CropScan, an expert agricultural AI assistant trained on verified agronomic data from ICAR (Indian Council of Agricultural Research) and FAO (Food and Agriculture Organization).

Your role is to help farmers understand crop diseases and take immediate, practical action. You always:
- Provide clear, actionable advice in simple language
- Base your recommendations on verified agronomic sources
- State the severity level explicitly
- Give step-by-step treatment instructions
- Cite your sources from the provided context

You never:
- Recommend treatments not supported by the provided context
- Give vague or non-actionable advice
- Use technical jargon without explanation
"""

ADVISORY_USER_PROMPT = """I am sharing a photo of a diseased crop leaf.

My AI classifier has identified this as: **{disease_name}** on **{crop_name}** with {confidence_pct}% confidence.

Here is verified agronomic context from ICAR and FAO guidelines:
---
{rag_context}
---

Based on the image and the context above, please provide a detailed advisory in this exact structure:

**DISEASE OVERVIEW**
[2-3 sentences describing what this disease is and how it spreads]

**SEVERITY LEVEL**
[One of: LOW / MODERATE / HIGH / CRITICAL — with one sentence explanation]

**SYMPTOMS TO CONFIRM**
[3-5 bullet points of visible symptoms the farmer should look for]

**IMMEDIATE TREATMENT STEPS**
[Numbered list of 4-6 specific, actionable treatment steps with product names where applicable]

**PREVENTIVE MEASURES**
[3-4 bullet points for future prevention]

**SOURCES**
[List the ICAR/FAO documents you drew from in the context above]

Keep the language simple. This advisory will be read by farmers who may not have agricultural training.
"""
```

---

## 2. Low Confidence Advisory Prompt

**Used in:** `backend/services/advisory_chain.py` when `confidence < 0.70`  
**Model:** LLaVA-1.6 via Ollama  
**Variables:** `top_predictions` (list of top-3 predictions with confidence)

```
LOW_CONFIDENCE_PROMPT = """The crop disease classifier returned uncertain results. The top predictions are:

{top_predictions}

Please look carefully at the image and:
1. Describe what you observe on the leaf (color, texture, spots, lesions, pattern)
2. State which of the above diseases best matches what you see and why
3. Provide a cautious advisory noting that professional verification is recommended

Be honest about uncertainty. Start your response with "Based on visual analysis (classifier confidence was low):"
"""
```

---

## 3. RAG Query Templates

**Used in:** `backend/rag/retriever.py` → `retrieve_context()`

```python
# Primary query — most specific
RAG_QUERY_PRIMARY = "{disease_name} {crop_name} treatment symptoms management"

# Secondary query — broader context
RAG_QUERY_SECONDARY = "{disease_name} causes prevention organic control"

# Fallback query — crop-level
RAG_QUERY_FALLBACK = "{crop_name} disease management integrated pest management"
```

**RAG Context Formatting Template:**
```python
RAG_CONTEXT_TEMPLATE = """
Source: {source_name}
Relevance: {relevance_score:.2f}
Content: {chunk_text}
---
"""
```

---

## 4. Image Description Prompt (Preprocessing Validation)

**Used in:** `backend/routers/predict.py` — validates that uploaded image contains a plant leaf  
**Model:** LLaVA-1.6 (lightweight check before full pipeline)

```
IMAGE_VALIDATION_PROMPT = """Look at this image and answer with ONLY one of these three responses:
- "LEAF" if the image clearly shows a plant leaf (with or without disease)
- "PLANT" if the image shows a plant but the leaf is not clearly visible
- "NOT_PLANT" if the image does not contain a plant or leaf

Respond with exactly one word. No explanation."""
```

**Usage:**
```python
# If response is "NOT_PLANT", return error to user:
# {"error": "no_leaf_detected", "message": "Please upload a clear photo of a crop leaf"}
```

---

## 5. Severity Classification Prompt

**Used in:** `backend/services/advisory_chain.py` — structured extraction after VLM response  
**Model:** Any fast LLM (can use a smaller model for this)

```
SEVERITY_EXTRACTION_PROMPT = """From the following agricultural advisory text, extract the severity level.

Advisory text:
{advisory_text}

Respond with ONLY one of: LOW, MODERATE, HIGH, CRITICAL

Rules:
- LOW: < 20% leaf area affected, easily treatable
- MODERATE: 20-50% affected, requires treatment soon
- HIGH: > 50% affected, urgent treatment needed
- CRITICAL: Systemic infection, may spread to entire field

Single word response only."""
```

---

## 6. Translation Quality Check Prompt

**Used in:** `backend/services/translation.py` — optional quality verification step  
**Model:** Any LLM  
**Variables:** `original_text`, `translated_text`, `target_language`

```
TRANSLATION_CHECK_PROMPT = """You are a bilingual agricultural expert. 

Original English advisory:
{original_text}

Translation into {target_language}:
{translated_text}

Rate the translation quality from 1-5 on:
1. Accuracy (are all facts preserved?)
2. Naturalness (does it read naturally in {target_language}?)
3. Terminology (are agricultural terms correctly translated?)

Respond in this JSON format only:
{{"accuracy": <1-5>, "naturalness": <1-5>, "terminology": <1-5>, "issues": "<brief description or none>"}}"""
```

---

## 7. Custom Dataset Annotation Prompt

**Used in:** Data collection phase — for auto-labeling custom India dataset images using VLM  
**Model:** LLaVA-1.6  
**Variables:** `class_candidates` (comma-separated list of possible diseases)

```
ANNOTATION_PROMPT = """You are an expert plant pathologist. Examine this crop leaf image carefully.

Possible disease classes for this crop:
{class_candidates}

Provide your assessment in this JSON format only:
{{
  "predicted_class": "<exact class name from the list above, or 'healthy' or 'unknown'>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<1-2 sentences explaining visual evidence>",
  "needs_human_review": <true if confidence < 0.7>
}}

If the image quality is too poor to assess, set predicted_class to "unclear" and needs_human_review to true."""
```

---

## 8. Advisory Summary Prompt (Share Feature)

**Used in:** Frontend share feature — generates short shareable summary  
**Model:** Any fast LLM  
**Variables:** `disease_name`, `crop_name`, `severity`, `full_advisory`

```
SUMMARY_PROMPT = """Summarize this crop disease advisory in exactly 3 bullet points for sharing via WhatsApp.
Each bullet should be under 100 characters. Write in simple farmer-friendly language.

Disease: {disease_name} on {crop_name} (Severity: {severity})

Full advisory:
{full_advisory}

Format:
• [Bullet 1 — what disease it is]
• [Bullet 2 — most important treatment step]
• [Bullet 3 — key prevention tip]

Output only the 3 bullet points, nothing else."""
```

---

## 9. Paper Abstract Generation Prompt

**Used in:** Research paper writing — helper prompt  
**Model:** Claude / GPT-4 (external tool, not in app pipeline)

```
ABSTRACT_PROMPT = """Write a 150-word academic abstract for a paper titled:
"CropScan: A Multimodal Vision-Language Pipeline for Agricultural Disease Diagnosis with Low-Resource Multilingual Advisory Generation"

Key facts to include:
- Fine-tuned EfficientNet-B4 and ViT-Base on PlantVillage (87K images, 38 classes)
- Top-1 accuracy: {classifier_accuracy}% on PlantVillage test set, {plantdoc_accuracy}% on PlantDoc
- LLaVA-1.6 (13B) via Ollama for advisory generation — fully local, no API cost
- RAG via ChromaDB with ICAR/FAO documents for grounded recommendations
- IndicTrans2 for translation into 4 Indian languages (Hindi, Tamil, Telugu, Marathi)
- Bark TTS for audio output
- Novel India-specific crop disease dataset: {custom_dataset_size} images

Write in formal academic style. Third person. Past tense for experiments, present for contributions."""
```

---

## 10. Ollama API Call Template

**Reference implementation for `backend/models/vlm.py`:**

```python
import httpx
import json

async def stream_ollama(prompt: str, image_b64: str, model: str = "llava:13b"):
    """
    Stream tokens from Ollama LLaVA.
    Yields decoded token strings as they arrive.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_b64],
        "stream": True,
        "options": {
            "temperature": 0.3,      # Low temp for factual advisory
            "top_p": 0.9,
            "num_predict": 1024,     # Max advisory length
            "stop": ["<|end|>", "###"]
        }
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    if not chunk.get("done"):
                        yield chunk.get("response", "")
                    else:
                        break
```

---

## Prompt Engineering Notes

### Temperature Guidelines
| Use case | Temperature | Reasoning |
|---|---|---|
| Disease advisory | 0.3 | Factual, consistent, no hallucination |
| Translation check | 0.1 | Deterministic scoring |
| Image validation | 0.0 | Single-word response, no creativity |
| Summary generation | 0.5 | Slight variation acceptable |
| Annotation | 0.2 | Consistent labeling |

### RAG Injection Strategy
1. Always inject RAG context BEFORE asking for advisory
2. Limit RAG context to 1500 tokens (leave room for image tokens + response)
3. Include source names — LLaVA is better at citing when sources are labeled
4. If RAG returns 0 results, use LOW_CONFIDENCE_PROMPT instead of ADVISORY_USER_PROMPT

### Prompt Versioning
When you modify a prompt, append version suffix and keep old version:
```python
ADVISORY_USER_PROMPT_v1 = "..."   # original
ADVISORY_USER_PROMPT_v2 = "..."   # current
ADVISORY_USER_PROMPT = ADVISORY_USER_PROMPT_v2  # alias
```
This makes it easy to A/B test prompt versions in MLflow experiments.

### Common Failure Modes to Avoid
- **Don't ask LLaVA to output pure JSON** — it often adds preamble text. Use the structured section format in ADVISORY_USER_PROMPT instead, then parse sections with regex.
- **Don't inject the full ICAR PDF** — chunk and retrieve top-5 relevant passages only (≤ 1500 tokens).
- **Don't use high temperature for medical/agronomic advice** — hallucination risk is too high.
- **Always include the classifier result in the VLM prompt** — grounding the VLM with the classifier output significantly improves advisory accuracy.
