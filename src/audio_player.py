#!/usr/bin/env python3
"""Cross-platform audio player for claude-voice plugin.

Provides non-blocking audio playback with automatic platform detection.
Supports macOS (afplay), Linux (aplay/paplay/ffplay), and Windows (winsound).
"""

import logging
import os
import platform
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("claude-voice")


def _find_linux_player() -> Optional[str]:
    """Find an available audio player on Linux.

    Tries aplay, paplay, and ffplay in order of preference.

    Returns:
        Name of the available player command, or None.
    """
    for player in ("aplay", "paplay", "ffplay"):
        if shutil.which(player):
            return player
    return None


def _play_with_soundfile(audio_samples, sample_rate: int) -> None:
    """Play audio by writing to a temp WAV file and using system player.

    Args:
        audio_samples: NumPy array of audio samples.
        sample_rate: Audio sample rate in Hz.
    """
    import soundfile as sf

    system = platform.system()

    # Write samples to a temporary WAV file
    with tempfile.NamedTemporaryFile(
        suffix=".wav", delete=False
    ) as tmp_file:
        tmp_path = tmp_file.name
        sf.write(tmp_path, audio_samples, sample_rate)

    try:
        if system == "Darwin":
            subprocess.run(
                ["afplay", tmp_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif system == "Linux":
            player = _find_linux_player()
            if player == "ffplay":
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", tmp_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif player:
                subprocess.run(
                    [player, tmp_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                logger.warning(
                    "No audio player found. "
                    "Install aplay, paplay, or ffplay."
                )
        elif system == "Windows":
            # Try winsound for WAV playback on Windows
            try:
                import winsound

                winsound.PlaySound(tmp_path, winsound.SND_FILENAME)
            except ImportError:
                subprocess.run(
                    [
                        "powershell",
                        "-c",
                        f'(New-Object Media.SoundPlayer "{tmp_path}").PlaySync()',
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        else:
            logger.warning("Unsupported platform: %s", system)
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def play_audio_async(audio_samples, sample_rate: int) -> None:
    """Play audio without blocking Claude's execution.

    Spawns a background thread to handle audio playback so that
    Claude can continue processing while audio is playing.

    Args:
        audio_samples: NumPy array of audio samples.
        sample_rate: Audio sample rate in Hz.
    """
    def _playback_worker():
        try:
            _play_with_soundfile(audio_samples, sample_rate)
        except ImportError:
            logger.error(
                "soundfile not installed. Run: pip3 install soundfile"
            )
        except Exception as e:
            logger.error("Audio playback failed: %s", e)

    thread = threading.Thread(target=_playback_worker, daemon=True)
    thread.start()
    logger.debug("Audio playback started in background thread.")
