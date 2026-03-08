#!/bin/bash
# Installation script for claude-voice plugin
# Installs Python dependencies and downloads the Kokoro TTS model

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing claude-voice plugin..."

# Install Python dependencies
echo "→ Installing Python dependencies..."
pip3 install -r "$PLUGIN_DIR/requirements.txt"

# Download Kokoro model if not present
echo "→ Checking TTS model..."
cd "$PLUGIN_DIR"
python3 -c "from src.model_manager import ensure_models; ensure_models()"

echo ""
echo "✓ Claude Voice plugin installed successfully!"
echo "  Toggle with: edit ~/.claude-voice.json"
echo "  Set 'enabled' to false to disable narration."
