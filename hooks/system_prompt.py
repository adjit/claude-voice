#!/usr/bin/env python
"""System prompt hook for claude-voice plugin.

Injects TTS instructions based on the configured mode.
"""

import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))

from src.config import load_config

MCP_INSTRUCTIONS = """
You have access to a 'speak' tool that lets you narrate what you're doing aloud.
Use it to provide audio feedback to the user during your work.

Guidelines for using the speak tool:
- Speak at key moments: starting tasks, discoveries, completions, errors
- Keep messages concise (1-2 sentences)
- Use a friendly, professional tone
- Don't speak every small action - focus on meaningful updates

Example uses:
- speak("I'm searching through your authentication code now.")
- speak("Found the issue. The API endpoint is missing error handling.")
- speak("Tests are passing. Creating the pull request now.")
"""

STOP_INSTRUCTIONS = """
You are working with a user who has text-to-speech enabled. When you complete
a response, a brief summary will be spoken aloud automatically. Write your
responses clearly and ensure key information is at the beginning.
"""


def main() -> None:
    """Read system prompt from stdin, append TTS instructions, write to stdout."""
    config = load_config()

    # Read existing prompt from stdin
    existing_prompt = ""
    if not sys.stdin.isatty():
        existing_prompt = sys.stdin.read()

    # Check if enabled
    if not config.get("enabled", True):
        sys.stdout.write(existing_prompt)
        return

    # Add mode-appropriate instructions
    mode = config.get("mode", "stop")
    instructions = ""

    if mode == "mcp":
        instructions = MCP_INSTRUCTIONS
    elif mode == "stop":
        instructions = STOP_INSTRUCTIONS
    elif mode == "both":
        instructions = MCP_INSTRUCTIONS + "\n" + STOP_INSTRUCTIONS

    if instructions:
        enhanced_prompt = existing_prompt.rstrip() + "\n" + instructions
        sys.stdout.write(enhanced_prompt)
    else:
        sys.stdout.write(existing_prompt)


if __name__ == "__main__":
    main()
