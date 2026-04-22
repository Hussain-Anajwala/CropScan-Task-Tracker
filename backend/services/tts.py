"""Text-to-speech service for CropScan."""

from __future__ import annotations

import base64
import io
import math
import wave
from functools import lru_cache

from loguru import logger

from backend.config import settings


@lru_cache(maxsize=1)
def _load_bark_processor() -> tuple[object, object] | None:
    try:
        from transformers import AutoProcessor, BarkModel

        processor = AutoProcessor.from_pretrained("suno/bark-small")
        model = BarkModel.from_pretrained("suno/bark-small")
        return processor, model
    except Exception as exc:
        logger.warning("Bark unavailable, falling back to gTTS or synthetic audio: {}", exc)
        return None


def _generate_sine_wave(duration_seconds: float = 1.5, sample_rate: int = 22050) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        for index in range(int(duration_seconds * sample_rate)):
            sample = int(16000 * math.sin(2 * math.pi * 440 * (index / sample_rate)))
            frames += sample.to_bytes(2, byteorder="little", signed=True)
        wav_file.writeframes(bytes(frames))
    return buffer.getvalue()


def generate_audio(text: str, language: str) -> bytes:
    """Generate WAV audio bytes for advisory text."""
    if settings.tts_engine == "bark":
        bark_bundle = _load_bark_processor()
        if bark_bundle is not None:
            try:
                import scipy.io.wavfile

                processor, model = bark_bundle
                inputs = processor(text, voice_preset="v2/en_speaker_6")
                audio_array = model.generate(**inputs)
                wav_buffer = io.BytesIO()
                scipy.io.wavfile.write(wav_buffer, rate=model.generation_config.sample_rate, data=audio_array.cpu().numpy().squeeze())
                return wav_buffer.getvalue()
            except Exception as exc:
                logger.warning("Bark generation failed, trying gTTS fallback: {}", exc)

    try:
        from gtts import gTTS

        tts = gTTS(text=text[:500], lang=language if language != "en" else "en")
        mp3_buffer = io.BytesIO()
        tts.write_to_fp(mp3_buffer)
        return mp3_buffer.getvalue()
    except Exception as exc:
        logger.warning("gTTS generation failed, using synthetic WAV fallback: {}", exc)
        return _generate_sine_wave()


def wav_to_base64(wav_bytes: bytes) -> str:
    """Encode audio bytes as base64."""
    return base64.b64encode(wav_bytes).decode("utf-8")
