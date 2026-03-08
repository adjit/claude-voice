#!/usr/bin/env python3
"""Configuration loader for claude-voice plugin.

Loads configuration from default_config.json with user overrides
from ~/.claude-voice.json.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("claude-voice")

# Paths
PLUGIN_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PLUGIN_DIR / "config" / "default_config.json"
USER_CONFIG_PATH = Path.home() / ".claude-voice.json"

# Valid modes
VALID_MODES = ("stop", "mcp", "both")


def load_config() -> Dict[str, Any]:
    """Load plugin configuration with user overrides.

    Reads the default configuration from config/default_config.json,
    then merges any user overrides from ~/.claude-voice.json.

    Returns:
        Dict containing the merged configuration.
    """
    config: Dict[str, Any] = {}

    # Load default config
    try:
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Failed to load default config: %s", e)
        config = {
            "enabled": True,
            "mode": "stop",
            "voice": "af_bella",
            "speed": 1.1,
            "model_path": "models/kokoro-v0_19.onnx",
            "voices_path": "models/voices.json",
            "summary_max_length": 200,
        }

    # Merge user overrides
    if USER_CONFIG_PATH.exists():
        try:
            with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            config.update(user_config)
            logger.debug("Loaded user config from %s", USER_CONFIG_PATH)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load user config: %s", e)

    # Validate mode
    if config.get("mode") not in VALID_MODES:
        logger.warning("Invalid mode '%s', defaulting to 'stop'", config.get("mode"))
        config["mode"] = "stop"

    return config
