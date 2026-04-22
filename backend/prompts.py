"""Prompt templates referenced by backend services."""

from __future__ import annotations


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
[One of: LOW / MODERATE / HIGH / CRITICAL - with one sentence explanation]

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


LOW_CONFIDENCE_PROMPT = """The crop disease classifier returned uncertain results. The top predictions are:

{top_predictions}

Please look carefully at the image and:
1. Describe what you observe on the leaf (color, texture, spots, lesions, pattern)
2. State which of the above diseases best matches what you see and why
3. Provide a cautious advisory noting that professional verification is recommended

Be honest about uncertainty. Start your response with "Based on visual analysis (classifier confidence was low):"
"""


RAG_QUERY_PRIMARY = "{disease_name} {crop_name} treatment symptoms management"
RAG_QUERY_SECONDARY = "{disease_name} causes prevention organic control"
RAG_QUERY_FALLBACK = "{crop_name} disease management integrated pest management"


RAG_CONTEXT_TEMPLATE = """
Source: {source_name}
Relevance: {relevance_score:.2f}
Content: {chunk_text}
---
"""


IMAGE_VALIDATION_PROMPT = """Look at this image and answer with ONLY one of these three responses:
- "LEAF" if the image clearly shows a plant leaf (with or without disease)
- "PLANT" if the image shows a plant but the leaf is not clearly visible
- "NOT_PLANT" if the image does not contain a plant or leaf

Respond with exactly one word. No explanation."""
