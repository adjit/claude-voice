# claude-voice

> Giving Claude Code a voice — adds conversational TTS narration to your Claude coding sessions using local AI models.

Claude Voice is a plugin for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that makes Claude **narrate what it's doing** — like having a senior engineer pair-programming with you, talking through their thought process.

All speech synthesis runs **locally** on your machine using the [Kokoro](https://github.com/thewh1teagle/kokoro-onnx) ONNX model. No API calls, no cloud services, complete privacy.

## How It Works

Claude Voice offers two modes of operation:

### Stop Mode (Default)
When Claude finishes responding, a brief summary of the response is automatically spoken aloud. This provides passive, low-distraction narration.

### MCP Mode
An MCP server provides a `speak` tool that Claude can call explicitly to narrate what it's doing. This gives Claude control over when and what to speak.

### Both Mode
Both behaviors active simultaneously for maximum audio feedback.

**All modes use:**
- **Local TTS** — Kokoro ONNX model generates natural-sounding speech entirely on your machine
- **Non-blocking** — Audio plays in a background thread so Claude keeps working

### Example Narrations

- *"I'm searching through your authentication code now."*
- *"Found the issue. The API endpoint is missing error handling."*
- *"Tests are passing. Creating the pull request now."*

## Prerequisites

- **Python 3.8+**
- **Claude Code** CLI
- **Linux:** One of `aplay`, `paplay`, or `ffplay` for audio playback
  ```bash
  # Debian/Ubuntu
  sudo apt install alsa-utils
  ```
- **macOS:** No additional dependencies (uses built-in `afplay`)
- **Windows:** No additional dependencies (uses built-in `winsound`)

## Installation

### Install as a Claude Code Plugin

1. Open Claude Code and run:
   ```
   /install-plugin https://github.com/adjit/claude-voice
   ```

2. Run the install script to fetch the TTS model and dependencies:
   ```bash
   bash scripts/install.sh
   ```

3. **(For MCP mode)** Add the MCP server:
   ```bash
   claude mcp add claude-voice -- python /path/to/claude-voice/mcp/server.py
   ```

4. Restart Claude Code — narration will be active.

### Local Installation (from source)

1. Clone this repository:
   ```bash
   git clone https://github.com/adjit/claude-voice.git
   cd claude-voice
   ```

2. Run the install script:
   ```bash
   bash scripts/install.sh
   ```

3. Register the plugin:
   ```
   /install-plugin file:///path/to/claude-voice
   ```

4. **(For MCP mode)** Add the MCP server:
   ```bash
   claude mcp add claude-voice -- python /path/to/claude-voice/mcp/server.py
   ```

### Manual Dependency Installation

```bash
pip install -r requirements.txt
python -c "from src.model_manager import ensure_models; ensure_models()"
```

## Configuration

Create `~/.claude-voice.json` to configure the plugin:

```json
{
  "enabled": true,
  "mode": "both",
  "voice": "af_bella",
  "speed": 1.1,
  "summary_max_length": 200
}
```

### Mode Options

| Mode | Behavior |
|------|----------|
| `"stop"` | Speaks summary when Claude finishes responding (default) |
| `"mcp"` | Claude calls `speak` tool explicitly for narration |
| `"both"` | Both Stop hook and MCP server active |

### All Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable narration |
| `mode` | string | `"stop"` | Operation mode: `"stop"`, `"mcp"`, or `"both"` |
| `voice` | string | `"af_bella"` | Kokoro voice identifier |
| `speed` | float | `1.1` | Speech speed multiplier |
| `summary_max_length` | int | `200` | Max characters for Stop hook summaries |
| `model_path` | string | `"models/kokoro-v0_19.onnx"` | Path to ONNX model |
| `voices_path` | string | `"models/voices.json"` | Path to voice configs |

### Quick Toggle

Disable narration:
```bash
echo '{"enabled": false}' > ~/.claude-voice.json
```

Switch to MCP-only mode:
```bash
echo '{"mode": "mcp"}' > ~/.claude-voice.json
```

## Project Structure

```
claude-voice/
├── .claude-plugin/
│   ├── plugin.json           # Plugin manifest with Stop hook
│   └── marketplace.json      # Marketplace metadata
├── .mcp.json                  # MCP server configuration
├── hooks/
│   ├── stop_hook.py          # Speaks summary when Claude stops
│   ├── system_prompt.py      # Injects mode-aware instructions
│   └── on_output.py          # DEPRECATED (kept for reference)
├── mcp/
│   └── server.py             # MCP server with speak tool
├── src/
│   ├── __init__.py
│   ├── config.py             # Configuration loader with mode validation
│   ├── tts_engine.py         # Kokoro TTS wrapper
│   ├── audio_player.py       # Cross-platform audio playback
│   └── model_manager.py      # Auto-download Kokoro model
├── config/
│   └── default_config.json   # Default configuration
├── models/
│   └── .gitkeep              # Models downloaded on first run
├── scripts/
│   └── install.sh            # Post-install setup script
├── tests/
│   └── test_plugin.py        # Unit tests
├── requirements.txt
├── README.md
└── LICENSE
```

## MCP Server Usage

When using MCP mode, Claude has access to a `speak` tool:

```
speak(text, voice?, speed?)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | required | Text to speak aloud |
| `voice` | string | from config | Voice identifier |
| `speed` | float | from config | Speech speed multiplier |

The MCP server will only respond to speak requests when `mode` is set to `"mcp"` or `"both"`.

## Troubleshooting

### No audio playing

1. **Check if enabled:** Verify `~/.claude-voice.json` has `"enabled": true`
2. **Check mode:** Ensure `mode` matches your setup (`"stop"` for hook, `"mcp"` for MCP server)
3. **Check audio player:** Run `which aplay paplay ffplay afplay` to see what's available
4. **Check model files:** Ensure `~/.cache/claude-voice/` contains `kokoro-v0_19.onnx` and `voices.json`

### MCP server not working

1. **Check mode:** Set `"mode": "mcp"` or `"mode": "both"` in `~/.claude-voice.json`
2. **Verify registration:** Run `claude mcp list` to see if `claude-voice` is registered
3. **Check server path:** Ensure the path in `claude mcp add` points to `mcp/server.py`

### Model download fails

- Check your internet connection
- Try downloading manually from the [kokoro-onnx releases](https://github.com/thewh1teagle/kokoro-onnx/releases)
- Place files in `~/.cache/claude-voice/`

### Import errors

```bash
pip install -r requirements.txt
```

### Linux: No sound

Install an audio player:
```bash
# ALSA (most common)
sudo apt install alsa-utils

# PulseAudio
sudo apt install pulseaudio-utils

# FFmpeg
sudo apt install ffmpeg
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Platform Notes

| Platform | Audio Player | Notes |
|----------|-------------|-------|
| macOS | `afplay` (built-in) | Works out of the box |
| Linux | `aplay` / `paplay` / `ffplay` | Need to install one |
| Windows | `winsound` (built-in) | Works out of the box |

## License

[MIT](LICENSE) — see LICENSE file for details.
