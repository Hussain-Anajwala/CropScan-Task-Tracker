"""Advisory orchestration across retrieval, VLM, translation, and parsing."""

from __future__ import annotations

import argparse
import asyncio
import base64
import re
from pathlib import Path
from typing import AsyncIterator

from loguru import logger

from backend.models.vlm import OllamaVLMClient
from backend.prompts import ADVISORY_USER_PROMPT
from backend.rag.retriever import retrieve_context
from backend.schemas import AdvisoryResponse
from backend.services.translation import translate


SECTION_PATTERNS = {
    "overview": r"\*\*DISEASE OVERVIEW\*\*\s*(.*?)(?=\*\*SEVERITY LEVEL\*\*|$)",
    "severity": r"\*\*SEVERITY LEVEL\*\*\s*(.*?)(?=\*\*SYMPTOMS TO CONFIRM\*\*|$)",
    "symptoms": r"\*\*SYMPTOMS TO CONFIRM\*\*\s*(.*?)(?=\*\*IMMEDIATE TREATMENT STEPS\*\*|$)",
    "treatment": r"\*\*IMMEDIATE TREATMENT STEPS\*\*\s*(.*?)(?=\*\*PREVENTIVE MEASURES\*\*|$)",
    "prevention": r"\*\*PREVENTIVE MEASURES\*\*\s*(.*?)(?=\*\*SOURCES\*\*|$)",
    "sources": r"\*\*SOURCES\*\*\s*(.*)$",
}

FALLBACK_SOURCES = ["General CropScan fallback guidance"]


def parse_advisory_sections(advisory_text: str) -> dict[str, object]:
    """Parse structured advisory sections from model output."""
    parsed: dict[str, object] = {}
    for key, pattern in SECTION_PATTERNS.items():
        match = re.search(pattern, advisory_text, flags=re.DOTALL | re.IGNORECASE)
        parsed[key] = match.group(1).strip() if match else ""

    severity_text = str(parsed["severity"]).upper()
    for level in ("LOW", "MODERATE", "HIGH", "CRITICAL"):
        if level in severity_text:
            parsed["severity_label"] = level.title()
            break
    else:
        parsed["severity_label"] = "Moderate"

    parsed["treatment_items"] = [
        line.strip("-* ").strip()
        for line in str(parsed["treatment"]).splitlines()
        if line.strip()
    ]
    parsed["prevention_items"] = [
        line.strip("-* ").strip()
        for line in str(parsed["prevention"]).splitlines()
        if line.strip()
    ]
    parsed["source_items"] = [
        line.strip("-* ").strip()
        for line in str(parsed["sources"]).splitlines()
        if line.strip()
    ]
    return parsed


def build_prompt(disease: str, crop: str, confidence: float, context: str) -> str:
    """Build the advisory prompt payload passed to the VLM."""
    return ADVISORY_USER_PROMPT.format(
        disease_name=disease,
        crop_name=crop,
        confidence_pct=round(confidence * 100, 2),
        rag_context=context or "No supporting agronomic context was retrieved.",
    )


def build_fallback_advisory(disease: str, crop: str, confidence: float, context: str) -> str:
    """Return a structured template advisory when retrieval or Ollama fails."""
    sources = []
    for line in context.splitlines():
        if line.startswith("Source:"):
            sources.append(line.replace("Source:", "").strip())
    sources = sources or FALLBACK_SOURCES
    return (
        f"**DISEASE OVERVIEW**\n"
        f"{disease} is the predicted issue affecting {crop}. The model confidence is {confidence * 100:.1f}%, so treat this as a strong hint and verify visible symptoms in the field.\n\n"
        f"**SEVERITY LEVEL**\n"
        f"MODERATE - immediate action is recommended to reduce spread while you confirm symptoms.\n\n"
        f"**SYMPTOMS TO CONFIRM**\n"
        f"- Check for lesions, spots, curling, mold, or yellowing on multiple leaves.\n"
        f"- Compare upper and lower leaf surfaces for progression.\n"
        f"- Inspect nearby plants for similar symptoms and spread.\n\n"
        f"**IMMEDIATE TREATMENT STEPS**\n"
        f"1. Remove and isolate heavily affected leaves where practical.\n"
        f"2. Avoid overhead irrigation and reduce leaf wetness.\n"
        f"3. Improve field airflow and sanitation around infected plants.\n"
        f"4. Apply a crop-appropriate treatment recommended by local agricultural guidance or extension officers.\n\n"
        f"**PREVENTIVE MEASURES**\n"
        f"- Monitor the crop regularly for early symptom spread.\n"
        f"- Clean tools after handling infected plants.\n"
        f"- Maintain balanced irrigation and spacing.\n\n"
        f"**SOURCES**\n"
        + "\n".join(f"- {source}" for source in sources)
    )


def stream_text_tokens(text: str) -> AsyncIterator[str]:
    """Yield whitespace-preserving tokens for SSE streaming."""
    async def _generator() -> AsyncIterator[str]:
        for token in re.findall(r"\S+\s*", text):
            yield token

    return _generator()


async def stream_advisory(
    image_b64: str,
    disease: str,
    crop: str,
    confidence: float,
    top_k: int = 5,
) -> AsyncIterator[str]:
    """Stream advisory tokens from the VLM."""
    try:
        context = retrieve_context(disease_name=disease, crop_name=crop, top_k=top_k)
    except Exception as exc:
        logger.warning("RAG retrieval failed, using advisory fallback: {}", exc)
        context = ""

    prompt = build_prompt(disease=disease, crop=crop, confidence=confidence, context=context)
    client = OllamaVLMClient()
    try:
        async for token in client.generate_advisory(
            image_b64=image_b64,
            disease=disease,
            crop=crop,
            confidence=confidence,
            rag_context=context,
            prompt=prompt,
        ):
            yield token
        return
    except Exception as exc:
        logger.warning("VLM streaming failed in advisory chain, using fallback template: {}", exc)

    fallback = build_fallback_advisory(disease=disease, crop=crop, confidence=confidence, context=context)
    async for token in stream_text_tokens(fallback):
        yield token


async def generate_full_advisory(
    image_b64: str,
    disease: str,
    crop: str,
    confidence: float,
    language: str = "en",
    top_k: int = 5,
) -> AdvisoryResponse:
    """Generate and parse a full advisory response."""
    chunks: list[str] = []
    async for token in stream_advisory(image_b64, disease, crop, confidence, top_k=top_k):
        chunks.append(token)
    advisory_text = "".join(chunks).strip()
    return build_advisory_response(advisory_text, language)


def build_advisory_response(advisory_text: str, language: str) -> AdvisoryResponse:
    """Build a structured advisory response from raw text."""
    parsed = parse_advisory_sections(advisory_text)
    translated = translate(advisory_text, language)
    return AdvisoryResponse(
        advisory=translated,
        severity=parsed["severity_label"],
        treatment=[str(item) for item in parsed["treatment_items"]],
        prevention=[str(item) for item in parsed["prevention_items"]],
        sources=[str(item) for item in parsed["source_items"]],
        language=language,
    )


def _image_to_base64(image_path: Path) -> str:
    data = image_path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


async def _main_async(args: argparse.Namespace) -> None:
    response = await generate_full_advisory(
        image_b64=_image_to_base64(args.image),
        disease=args.disease,
        crop=args.crop,
        confidence=args.confidence,
        language=args.language,
    )
    logger.info("Severity: {}", response.severity)
    logger.info("Advisory:\n{}", response.advisory)


def main() -> None:
    """CLI entry point for advisory generation."""
    parser = argparse.ArgumentParser(description="Run the CropScan advisory chain.")
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--disease", type=str, default="Tomato Late Blight")
    parser.add_argument("--crop", type=str, default="Tomato")
    parser.add_argument("--confidence", type=float, default=0.9)
    parser.add_argument("--language", type=str, default="en")
    args = parser.parse_args()
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
