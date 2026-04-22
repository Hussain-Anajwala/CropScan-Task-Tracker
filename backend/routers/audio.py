"""Audio API router."""

from __future__ import annotations

import time

from fastapi import APIRouter

from backend.schemas import AudioRequest, AudioResponse
from backend.services.tts import generate_audio, wav_to_base64


router = APIRouter(prefix="/audio", tags=["audio"])
_AUDIO_CACHE: dict[tuple[str, str], tuple[float, str]] = {}


@router.post("", response_model=AudioResponse)
async def audio(request: AudioRequest) -> AudioResponse:
    """Generate advisory audio with a simple in-memory cache."""
    cache_key = (request.text, request.language)
    now = time.time()
    cached = _AUDIO_CACHE.get(cache_key)
    if cached and now - cached[0] < 600:
        return AudioResponse(audio=cached[1], cached=True)

    audio_bytes = generate_audio(request.text, request.language)
    encoded = wav_to_base64(audio_bytes)
    _AUDIO_CACHE[cache_key] = (now, encoded)
    return AudioResponse(audio=encoded, cached=False)
