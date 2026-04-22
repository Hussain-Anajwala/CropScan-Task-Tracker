"""Ollama VLM client for advisory generation."""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx
from loguru import logger

from backend.config import settings
from backend.prompts import ADVISORY_SYSTEM_PROMPT, ADVISORY_USER_PROMPT


class OllamaVLMClient:
    """Client for advisory generation with Ollama-hosted VLMs."""

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or "llava:7b"
        self.timeout_seconds = settings.vlm_timeout_seconds

    async def generate_advisory(
        self,
        image_b64: str,
        disease: str,
        crop: str,
        confidence: float,
        rag_context: str,
        prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream advisory text from Ollama, with a template fallback."""
        prompt = prompt or ADVISORY_USER_PROMPT.format(
            disease_name=disease,
            crop_name=crop,
            confidence_pct=round(confidence * 100, 2),
            rag_context=rag_context or "No supporting agronomic context was retrieved.",
        )
        payload = {
            "model": self.model,
            "prompt": f"{ADVISORY_SYSTEM_PROMPT}\n\n{prompt}",
            "images": [image_b64],
            "stream": True,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 1024,
                "stop": ["<|end|>", "###"],
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        if chunk.get("done"):
                            break
                        token = chunk.get("response", "")
                        if token:
                            yield token
            return
        except Exception as exc:
            print("VLM ERROR:", exc)
            logger.warning("Ollama advisory generation failed: {}", exc)
            raise
