#!/usr/bin/env python3
"""Output hook for claude-voice plugin.

Reads Claude's output from stdin, detects [NARRATE: "..."] markers,
speaks the text using TTS, and removes markers from the output
displayed to the user.
"""

import logging
import re
import sys
from pathlib import Path

# Add plugin root to path for imports
PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))

from src.config import load_config  # noqa: E402

logger = logging.getLogger("claude-voice")

# Regex pattern to match [NARRATE: "text"] markers
NARRATE_PATTERN = re.compile(r'\[NARRATE:\s*"([^"]+)"\]')


def process_output(text: str, enabled: bool = True) -> str:
    """Process Claude's output, extract narrations, and trigger TTS.

    Args:
        text: Raw output text from Claude.
        enabled: Whether narration is enabled.

    Returns:
        Cleaned output text with narration markers removed.
    """
    if not enabled:
        return text

    matches = NARRATE_PATTERN.findall(text)

    if matches:
        # Lazy import to avoid loading TTS unless needed
        try:
            from src.audio_player import play_audio_async
            from src.tts_engine import speak

            config = load_config()
            voice = config.get("voice", "af_bella")
            speed = config.get("speed", 1.1)

            for narration_text in matches:
                result = speak(narration_text, voice=voice, speed=speed)
                if result:
                    samples, sample_rate = result
                    play_audio_async(samples, sample_rate)
        except Exception as e:
            logger.error("Narration failed: %s", e)

    # Remove narration markers from output
    cleaned = NARRATE_PATTERN.sub("", text)
    # Clean up extra blank lines left by removal
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def main() -> None:
    """Read output from stdin, process narrations, write to stdout."""
    config = load_config()
    enabled = config.get("enabled", True)

    if not sys.stdin.isatty():
        text = sys.stdin.read()
        cleaned = process_output(text, enabled=enabled)
        sys.stdout.write(cleaned)


if __name__ == "__main__":
    main()
