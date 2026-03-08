#!/usr/bin/env python3
"""TTS engine for claude-voice plugin.

Wraps the kokoro-onnx library to provide text-to-speech synthesis
with voice selection and speed control.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger("claude-voice")

# Module-level cache for the loaded model
_kokoro_instance = None


def _get_kokoro():
    """Get or create a cached Kokoro TTS instance.

    Lazily loads the model on first call and caches it for subsequent use.

    Returns:
        A Kokoro instance, or None if loading fails.
    """
    global _kokoro_instance

    if _kokoro_instance is not None:
        return _kokoro_instance

    try:
        from kokoro_onnx import Kokoro

        from src.model_manager import get_model_path, get_voices_path

        model_path = get_model_path()
        voices_path = get_voices_path()

        if not model_path or not voices_path:
            logger.error(
                "Model files not found. Run the install script first."
            )
            return None

        logger.debug("Loading Kokoro model from %s", model_path)
        _kokoro_instance = Kokoro(str(model_path), str(voices_path))
        logger.info("Kokoro TTS model loaded successfully.")
        return _kokoro_instance

    except ImportError:
        logger.error(
            "kokoro-onnx not installed. Run: pip3 install kokoro-onnx"
        )
        return None
    except Exception as e:
        logger.error("Failed to load Kokoro model: %s", e)
        return None


def speak(
    text: str, voice: str = "af_bella", speed: float = 1.1
) -> Optional[Tuple[bytes, int]]:
    """Generate audio samples from text using Kokoro TTS.

    Args:
        text: The text to synthesize into speech.
        voice: Voice identifier (default: af_bella).
        speed: Playback speed multiplier (default: 1.1).

    Returns:
        A tuple of (audio_samples as numpy array, sample_rate),
        or None if synthesis fails.
    """
    if not text or not text.strip():
        logger.debug("Empty text, skipping TTS.")
        return None

    kokoro = _get_kokoro()
    if kokoro is None:
        return None

    try:
        samples, sample_rate = kokoro.create(text, voice=voice, speed=speed)
        logger.debug(
            "Generated %d audio samples at %d Hz", len(samples), sample_rate
        )
        return (samples, sample_rate)
    except Exception as e:
        logger.error("TTS synthesis failed: %s", e)
        return None
