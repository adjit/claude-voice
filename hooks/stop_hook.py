#!/usr/bin/env python
"""Stop hook for claude-voice plugin.

Reads the Stop event JSON from stdin, extracts Claude's last response,
generates a brief summary, and speaks it using TTS.

Exit codes:
  0 - Allow Claude to stop (normal)
  2 - Block stop (avoid - creates infinite loop)
"""

import json
import logging
import sys
from pathlib import Path

# Add plugin root to path for imports
PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))

from src.config import load_config

logger = logging.getLogger("claude-voice")


def summarize_response(text: str, max_length: int = 200) -> str:
    """Create a brief speakable summary of Claude's response.

    Takes the first sentence or truncates to max_length.
    """
    if not text:
        return ""

    # Find first sentence ending
    for end_char in [". ", "! ", "? "]:
        idx = text.find(end_char)
        if idx != -1 and idx < max_length:
            return text[: idx + 1].strip()

    # Truncate if no sentence ending found
    if len(text) > max_length:
        idx = text.rfind(" ", 0, max_length)
        if idx > 0:
            return text[:idx].strip() + "..."
        return text[:max_length].strip() + "..."

    return text.strip()


def main() -> None:
    """Process Stop hook - speak summary of Claude's response."""
    config = load_config()

    # Check if plugin is enabled
    if not config.get("enabled", True):
        sys.exit(0)

    # Check mode - only run in "stop" or "both" mode
    mode = config.get("mode", "stop")
    if mode not in ("stop", "both"):
        sys.exit(0)

    # Read hook input from stdin
    try:
        if sys.stdin.isatty():
            sys.exit(0)
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    # Check stop_hook_active to prevent infinite loops
    if hook_input.get("stop_hook_active", False):
        sys.exit(0)

    # Get Claude's last message
    last_message = hook_input.get("last_assistant_message", "")
    if not last_message:
        sys.exit(0)

    # Generate summary
    max_length = config.get("summary_max_length", 200)
    summary = summarize_response(last_message, max_length)

    if not summary:
        sys.exit(0)

    # Speak the summary
    try:
        from src.audio_player import play_audio_async
        from src.tts_engine import speak

        voice = config.get("voice", "af_bella")
        speed = config.get("speed", 1.1)

        result = speak(summary, voice=voice, speed=speed)
        if result:
            samples, sample_rate = result
            play_audio_async(samples, sample_rate)
    except Exception as e:
        logger.error("Stop hook TTS failed: %s", e)

    # Always exit 0 to allow Claude to stop
    sys.exit(0)


if __name__ == "__main__":
    main()
