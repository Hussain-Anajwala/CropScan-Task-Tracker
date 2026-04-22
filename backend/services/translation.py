"""Translation service for CropScan."""

from __future__ import annotations

from functools import lru_cache

from loguru import logger


SUPPORTED_LANGUAGES = {"en", "hi", "ta", "te", "mr"}


@lru_cache(maxsize=1)
def _load_translator() -> object | None:
    try:
        from transformers import pipeline

        return pipeline("translation", model="Helsinki-NLP/opus-mt-en-ROMANCE")
    except Exception as exc:
        logger.warning("Translation model unavailable, using rule-based fallback: {}", exc)
        return None


def translate(text: str, target_lang: str) -> str:
    """Translate advisory text, with a deterministic fallback when models are unavailable."""
    if target_lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {target_lang}")
    if target_lang == "en":
        return text

    translator = _load_translator()
    if translator is not None:
        try:
            translated = translator(text[:1024])
            if translated and "translation_text" in translated[0]:
                return translated[0]["translation_text"]
        except Exception as exc:
            logger.warning("Model translation failed, using fallback: {}", exc)

    language_names = {
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "mr": "Marathi",
    }
    return f"[{language_names[target_lang]} translation placeholder]\n{text}"
