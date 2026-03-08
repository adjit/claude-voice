#!/usr/bin/env python3
"""System prompt hook for claude-voice plugin.

Reads the existing system prompt from stdin and appends narration
instructions so Claude provides spoken updates during coding sessions.
"""

import sys
from pathlib import Path

# Add plugin root to path for imports
PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))

from src.config import load_config  # noqa: E402

NARRATION_INSTRUCTIONS = """
You are working with a user who has text-to-speech narration enabled. \
As you work, provide conversational updates about what you're doing, \
what you've discovered, and your thought process—like a senior engineer \
pair programming.

Output narration using this format:
[NARRATE: "your conversational message here"]

Guidelines for narration:
- Be concise and natural (1-2 sentences)
- Speak in first person ("I'm checking...", "I found...")
- Narrate key moments: starting tasks, discoveries, completions, errors
- Don't narrate every small action—focus on meaningful updates
- Use a friendly, professional tone

Example narrations:
[NARRATE: "I'm searching through your authentication code now."]
[NARRATE: "Found three API endpoints. The login handler looks solid, \
but I see a potential issue in the password reset flow."]
[NARRATE: "Tests are passing. I'm creating the pull request now."]
"""


def main() -> None:
    """Read system prompt from stdin, append narration, write to stdout."""
    config = load_config()

    # Read existing prompt from stdin (if piped)
    existing_prompt = ""
    if not sys.stdin.isatty():
        existing_prompt = sys.stdin.read()

    # Only inject if narration is enabled
    if not config.get("enabled", True):
        sys.stdout.write(existing_prompt)
        return

    # Append narration instructions
    enhanced_prompt = existing_prompt.rstrip() + "\n" + NARRATION_INSTRUCTIONS
    sys.stdout.write(enhanced_prompt)


if __name__ == "__main__":
    main()
