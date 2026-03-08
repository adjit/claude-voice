#!/usr/bin/env python3
"""Tests for claude-voice plugin.

Tests configuration loading, narration marker detection, output processing,
system prompt injection, and model manager utilities.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add plugin root to path
PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))

from hooks.on_output import NARRATE_PATTERN, process_output
from hooks.system_prompt import NARRATION_INSTRUCTIONS
from src.config import DEFAULT_CONFIG_PATH, load_config


class TestConfig(unittest.TestCase):
    """Tests for configuration loading."""

    def test_load_default_config(self):
        """Default config should load with expected keys."""
        config = load_config()
        self.assertIn("enabled", config)
        self.assertIn("voice", config)
        self.assertIn("speed", config)
        self.assertIn("model_path", config)
        self.assertIn("voices_path", config)

    def test_default_values(self):
        """Default config should have expected default values."""
        config = load_config()
        self.assertTrue(config["enabled"])
        self.assertEqual(config["voice"], "af_bella")
        self.assertAlmostEqual(config["speed"], 1.1)

    def test_user_override(self):
        """User config should override default values."""
        user_config = {"voice": "af_sarah", "speed": 0.9}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(user_config, f)
            tmp_path = f.name

        try:
            with patch("src.config.USER_CONFIG_PATH", Path(tmp_path)):
                config = load_config()
                self.assertEqual(config["voice"], "af_sarah")
                self.assertAlmostEqual(config["speed"], 0.9)
                # Other defaults should still be present
                self.assertTrue(config["enabled"])
        finally:
            os.unlink(tmp_path)

    def test_invalid_user_config(self):
        """Invalid user config should not crash, defaults should persist."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("not valid json{{{")
            tmp_path = f.name

        try:
            with patch("src.config.USER_CONFIG_PATH", Path(tmp_path)):
                config = load_config()
                # Should still have defaults
                self.assertIn("enabled", config)
        finally:
            os.unlink(tmp_path)


class TestNarrationPattern(unittest.TestCase):
    """Tests for the NARRATE regex pattern."""

    def test_basic_narration(self):
        """Should match basic narration marker."""
        text = '[NARRATE: "Hello world"]'
        matches = NARRATE_PATTERN.findall(text)
        self.assertEqual(matches, ["Hello world"])

    def test_multiple_narrations(self):
        """Should match multiple narration markers."""
        text = (
            '[NARRATE: "First message"] some text '
            '[NARRATE: "Second message"]'
        )
        matches = NARRATE_PATTERN.findall(text)
        self.assertEqual(matches, ["First message", "Second message"])

    def test_narration_with_punctuation(self):
        """Should handle punctuation in narration text."""
        text = '[NARRATE: "I found 3 bugs! Let me fix them."]'
        matches = NARRATE_PATTERN.findall(text)
        self.assertEqual(matches, ["I found 3 bugs! Let me fix them."])

    def test_narration_with_contractions(self):
        """Should handle contractions and apostrophe-like characters."""
        text = "[NARRATE: \"I'm checking the code now.\"]"
        matches = NARRATE_PATTERN.findall(text)
        self.assertEqual(matches, ["I'm checking the code now."])

    def test_no_narration(self):
        """Should return empty list when no narration markers present."""
        text = "Just regular output without any markers."
        matches = NARRATE_PATTERN.findall(text)
        self.assertEqual(matches, [])

    def test_narration_extra_spaces(self):
        """Should handle extra whitespace after NARRATE:."""
        text = '[NARRATE:  "Extra spaces"]'
        matches = NARRATE_PATTERN.findall(text)
        self.assertEqual(matches, ["Extra spaces"])

    def test_partial_marker_no_match(self):
        """Should not match incomplete markers."""
        text = '[NARRATE: missing quotes]'
        matches = NARRATE_PATTERN.findall(text)
        self.assertEqual(matches, [])


class TestOutputProcessing(unittest.TestCase):
    """Tests for output processing and marker removal."""

    @patch("hooks.on_output.load_config")
    def test_remove_markers(self, mock_config):
        """Should remove narration markers from output."""
        mock_config.return_value = {"voice": "af_bella", "speed": 1.1}
        text = 'Before [NARRATE: "Hello"] After'

        with patch("src.tts_engine.speak", return_value=None), \
             patch("src.audio_player.play_audio_async"):
            result = process_output(text, enabled=True)

        self.assertNotIn("[NARRATE:", result)
        self.assertIn("Before", result)
        self.assertIn("After", result)

    def test_disabled_passthrough(self):
        """Should pass through text unchanged when disabled."""
        text = '[NARRATE: "Hello"] Regular text'
        result = process_output(text, enabled=False)
        self.assertEqual(result, text)

    @patch("hooks.on_output.load_config")
    def test_no_markers_passthrough(self, mock_config):
        """Should pass through text when no markers present."""
        mock_config.return_value = {"voice": "af_bella", "speed": 1.1}
        text = "Just regular output."
        result = process_output(text, enabled=True)
        self.assertEqual(result, text)

    @patch("hooks.on_output.load_config")
    def test_multiple_markers_removed(self, mock_config):
        """Should remove all narration markers."""
        mock_config.return_value = {"voice": "af_bella", "speed": 1.1}
        text = (
            '[NARRATE: "First"] middle '
            '[NARRATE: "Second"] end'
        )

        with patch("src.tts_engine.speak", return_value=None), \
             patch("src.audio_player.play_audio_async"):
            result = process_output(text, enabled=True)

        self.assertNotIn("[NARRATE:", result)
        self.assertIn("middle", result)
        self.assertIn("end", result)


class TestSystemPrompt(unittest.TestCase):
    """Tests for system prompt injection."""

    def test_narration_instructions_content(self):
        """Instructions should contain key narration guidance."""
        self.assertIn("[NARRATE:", NARRATION_INSTRUCTIONS)
        self.assertIn("text-to-speech", NARRATION_INSTRUCTIONS)
        self.assertIn("concise", NARRATION_INSTRUCTIONS)

    @patch("hooks.system_prompt.load_config")
    def test_prompt_injection_when_enabled(self, mock_config):
        """Should append narration instructions when enabled."""
        mock_config.return_value = {"enabled": True}

        from hooks.system_prompt import main

        with patch("sys.stdin") as mock_stdin, \
             patch("sys.stdout") as mock_stdout:
            mock_stdin.isatty.return_value = False
            mock_stdin.read.return_value = "Existing prompt."
            mock_stdout.write = MagicMock()

            main()

            written = mock_stdout.write.call_args[0][0]
            self.assertIn("Existing prompt.", written)
            self.assertIn("[NARRATE:", written)

    @patch("hooks.system_prompt.load_config")
    def test_prompt_passthrough_when_disabled(self, mock_config):
        """Should not inject when narration is disabled."""
        mock_config.return_value = {"enabled": False}

        from hooks.system_prompt import main

        with patch("sys.stdin") as mock_stdin, \
             patch("sys.stdout") as mock_stdout:
            mock_stdin.isatty.return_value = False
            mock_stdin.read.return_value = "Existing prompt."
            mock_stdout.write = MagicMock()

            main()

            written = mock_stdout.write.call_args[0][0]
            self.assertEqual(written, "Existing prompt.")


class TestModelManager(unittest.TestCase):
    """Tests for model manager utilities."""

    def test_cache_dir_path(self):
        """Cache directory should be under user home."""
        from src.model_manager import CACHE_DIR
        self.assertTrue(str(CACHE_DIR).startswith(str(Path.home())))

    def test_model_urls_valid(self):
        """Model URLs should point to GitHub releases."""
        from src.model_manager import MODEL_URL, VOICES_URL
        self.assertIn("github.com", MODEL_URL)
        self.assertIn("github.com", VOICES_URL)
        self.assertTrue(MODEL_URL.endswith(".onnx"))
        self.assertTrue(VOICES_URL.endswith(".json"))


class TestAudioPlayer(unittest.TestCase):
    """Tests for audio player utilities."""

    def test_find_linux_player(self):
        """Should return a player name or None."""
        from src.audio_player import _find_linux_player
        result = _find_linux_player()
        # Result should be a string or None
        self.assertTrue(result is None or isinstance(result, str))

    @patch("src.audio_player._play_with_soundfile")
    def test_play_audio_async_nonblocking(self, mock_play):
        """play_audio_async should return immediately (non-blocking)."""
        import numpy as np

        from src.audio_player import play_audio_async

        samples = np.zeros(100, dtype=np.float32)
        # Should return without blocking
        play_audio_async(samples, 24000)
        # Give thread a moment to start
        import time
        time.sleep(0.1)


class TestPluginManifest(unittest.TestCase):
    """Tests for plugin manifest validity."""

    def test_manifest_exists(self):
        """Plugin manifest should exist."""
        manifest_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
        self.assertTrue(manifest_path.exists())

    def test_manifest_valid_json(self):
        """Plugin manifest should be valid JSON."""
        manifest_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        self.assertEqual(manifest["name"], "claude-voice")
        self.assertIn("hooks", manifest)
        self.assertIn("system_prompt", manifest["hooks"])
        self.assertIn("on_output", manifest["hooks"])


class TestMarketplaceJson(unittest.TestCase):
    """Tests for the plugin marketplace JSON file."""

    def test_marketplace_json_exists(self):
        """marketplace.json should exist at the repo root."""
        marketplace_path = PLUGIN_DIR / "marketplace.json"
        self.assertTrue(marketplace_path.exists())

    def test_marketplace_json_valid(self):
        """marketplace.json should be valid JSON with required fields."""
        marketplace_path = PLUGIN_DIR / "marketplace.json"
        with open(marketplace_path) as f:
            data = json.load(f)

        self.assertEqual(data["name"], "claude-voice")
        self.assertIn("version", data)
        self.assertIn("description", data)
        self.assertIn("author", data)
        self.assertIn("repository", data)

    def test_marketplace_json_directory_field(self):
        """marketplace.json should include a directory mapping."""
        marketplace_path = PLUGIN_DIR / "marketplace.json"
        with open(marketplace_path) as f:
            data = json.load(f)

        self.assertIn("directory", data)
        directory = data["directory"]
        self.assertIsInstance(directory, dict)
        self.assertTrue(len(directory) > 0)

    def test_marketplace_json_plugin_directory(self):
        """marketplace.json should reference the .claude-plugin directory."""
        marketplace_path = PLUGIN_DIR / "marketplace.json"
        with open(marketplace_path) as f:
            data = json.load(f)

        self.assertIn("plugin_directory", data)
        self.assertEqual(data["plugin_directory"], ".claude-plugin")
        self.assertIn("plugin_manifest", data)
        self.assertEqual(data["plugin_manifest"], ".claude-plugin/plugin.json")

    def test_marketplace_json_repository_url(self):
        """Repository URL should point to GitHub."""
        marketplace_path = PLUGIN_DIR / "marketplace.json"
        with open(marketplace_path) as f:
            data = json.load(f)

        self.assertIn("github.com", data["repository"])


if __name__ == "__main__":
    unittest.main()
