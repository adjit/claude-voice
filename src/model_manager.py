#!/usr/bin/env python3
"""Model manager for claude-voice plugin.

Handles downloading and caching the Kokoro ONNX model and voice
configuration files required for text-to-speech synthesis.
"""

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger("claude-voice")

# Model configuration
MODEL_FILENAME = "kokoro-v0_19.onnx"
VOICES_FILENAME = "voices.json"
MODEL_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files/kokoro-v0_19.onnx"
)
VOICES_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files/voices.json"
)

CACHE_DIR = Path.home() / ".cache" / "claude-voice"
PLUGIN_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = PLUGIN_DIR / "models"


def _download_file(url: str, dest: Path, description: str) -> bool:
    """Download a file from a URL with progress reporting.

    Args:
        url: URL to download from.
        dest: Destination path for the downloaded file.
        description: Human-readable description for progress display.

    Returns:
        True if download was successful, False otherwise.
    """
    try:
        import requests
        from tqdm import tqdm
    except ImportError:
        logger.error(
            "Missing dependencies. Run: pip3 install requests tqdm"
        )
        return False

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Downloading %s...", description)
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        with open(dest, "wb") as f, tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            desc=description,
        ) as progress:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                progress.update(len(chunk))

        logger.info("Downloaded %s to %s", description, dest)
        return True

    except Exception as e:
        logger.error("Failed to download %s: %s", description, e)
        if dest.exists():
            dest.unlink()
        return False


def _ensure_file(
    filename: str, url: str, description: str
) -> Optional[Path]:
    """Ensure a model file exists, downloading if necessary.

    Checks the plugin models/ directory first, then the user cache
    directory. Downloads the file if not found in either location.

    Args:
        filename: Name of the file to ensure.
        url: URL to download from if file is missing.
        description: Human-readable description for progress display.

    Returns:
        Path to the file, or None if unavailable.
    """
    # Check plugin models directory
    plugin_path = MODELS_DIR / filename
    if plugin_path.exists() and plugin_path.stat().st_size > 0:
        return plugin_path

    # Check cache directory
    cache_path = CACHE_DIR / filename
    if cache_path.exists() and cache_path.stat().st_size > 0:
        # Create symlink in models directory
        _link_to_models(cache_path, plugin_path)
        return plugin_path

    # Download to cache
    if _download_file(url, cache_path, description):
        _link_to_models(cache_path, plugin_path)
        return plugin_path

    return None


def _link_to_models(source: Path, dest: Path) -> None:
    """Create a symlink from cache to plugin models directory.

    Args:
        source: Path to the cached file.
        dest: Path for the symlink in models directory.
    """
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        dest.symlink_to(source)
        logger.debug("Linked %s -> %s", dest, source)
    except OSError as e:
        # Fallback: copy the file if symlink fails (e.g., Windows)
        logger.debug("Symlink failed, copying: %s", e)
        shutil.copy2(source, dest)


def ensure_models() -> bool:
    """Ensure all required model files are available.

    Downloads missing models from the official kokoro-onnx releases
    and stores them in ~/.cache/claude-voice/ with symlinks in models/.

    Returns:
        True if all models are available, False otherwise.
    """
    model_path = _ensure_file(MODEL_FILENAME, MODEL_URL, "Kokoro TTS model")
    voices_path = _ensure_file(VOICES_FILENAME, VOICES_URL, "Voice configs")

    if model_path and voices_path:
        logger.info("All models are ready.")
        return True

    logger.error("Some models could not be downloaded.")
    return False


def get_model_path() -> Optional[Path]:
    """Get the path to the Kokoro ONNX model file.

    Returns:
        Path to the model file, or None if not available.
    """
    path = MODELS_DIR / MODEL_FILENAME
    if path.exists():
        return path

    cache_path = CACHE_DIR / MODEL_FILENAME
    if cache_path.exists():
        return cache_path

    return None


def get_voices_path() -> Optional[Path]:
    """Get the path to the voices.json configuration file.

    Returns:
        Path to the voices file, or None if not available.
    """
    path = MODELS_DIR / VOICES_FILENAME
    if path.exists():
        return path

    cache_path = CACHE_DIR / VOICES_FILENAME
    if cache_path.exists():
        return cache_path

    return None
