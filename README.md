# claude-voice 🔊

> Giving Claude Code a voice — adds conversational TTS narration to your Claude coding sessions using local AI models.

Claude Voice is a plugin for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that makes Claude **narrate what it's doing** in real time — like having a senior engineer pair-programming with you, talking through their thought process.

All speech synthesis runs **locally** on your machine using the [Kokoro](https://github.com/thewh1teagle/kokoro-onnx) ONNX model. No API calls, no cloud services, complete privacy.

## How It Works

1. **System Prompt Hook** — Injects narration instructions so Claude naturally provides spoken updates
2. **Output Hook** — Detects `[NARRATE: "..."]` markers in Claude's output, sends them to the TTS engine, and removes them from the displayed text
3. **Local TTS** — Kokoro ONNX model generates natural-sounding speech entirely on your machine
4. **Non-blocking** — Audio plays in a background thread so Claude keeps working

### Example Narrations

When Claude is working, you'll hear updates like:

- *"I'm searching through your authentication code now."*
- *"Found three API endpoints. The login handler looks solid, but I see a potential issue in the password reset flow."*
- *"Tests are passing. I'm creating the pull request now."*

## Prerequisites

- **Python 3.8+**
- **Claude Code** CLI
- **Linux:** `espeak-ng` and one of `aplay`, `paplay`, or `ffplay` for audio playback
  ```bash
  # Debian/Ubuntu
  sudo apt install espeak-ng alsa-utils
  ```
- **macOS:** No additional dependencies (uses built-in `afplay`)
- **Windows:** No additional dependencies (uses built-in `winsound`)

## Installation

### Install as a Claude Code Plugin

The recommended way to install claude-voice is directly through Claude Code:

1. Open Claude Code and run the slash command:
   ```
   /install-plugin https://github.com/adjit/claude-voice
   ```

2. Claude Code will clone the repository and register the plugin. Once registered, run the install script to fetch the TTS model and dependencies:
   ```bash
   bash scripts/install.sh
   ```

3. Restart Claude Code (or start a new session) — narration will be active.

### Local Installation (from source)

If you prefer to install manually from a local copy:

1. Clone this repository:
   ```bash
   git clone https://github.com/adjit/claude-voice.git
   cd claude-voice
   ```

2. Run the install script to fetch dependencies and the TTS model:
   ```bash
   bash scripts/install.sh
   ```

   This will:
   - Install Python dependencies (`kokoro-onnx`, `soundfile`, `requests`, `tqdm`)
   - Download the Kokoro TTS model (~82MB) to `~/.cache/claude-voice/`

3. Register the plugin with Claude Code by pointing it at the cloned directory (note the three slashes for `file://` + absolute path):
   ```
   /install-plugin file:///home/youruser/claude-voice
   ```

4. Restart Claude Code — the plugin will activate on your next session.

### Manual Dependency Installation

If you only need to install the Python dependencies and model without the plugin registration step:

```bash
pip3 install -r requirements.txt
python3 -c "from src.model_manager import ensure_models; ensure_models()"
```

## Configuration

Default settings are in `config/default_config.json`:

```json
{
  "enabled": true,
  "voice": "af_bella",
  "speed": 1.1,
  "model_path": "models/kokoro-v0_19.onnx",
  "voices_path": "models/voices.json"
}
```

### User Overrides

Create `~/.claude-voice.json` to override any setting:

```json
{
  "enabled": true,
  "voice": "af_bella",
  "speed": 1.0
}
```

### Available Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable narration |
| `voice` | string | `"af_bella"` | Kokoro voice identifier |
| `speed` | float | `1.1` | Speech speed multiplier |
| `model_path` | string | `"models/kokoro-v0_19.onnx"` | Path to ONNX model |
| `voices_path` | string | `"models/voices.json"` | Path to voice configs |

### Quick Toggle

Disable narration temporarily:
```bash
echo '{"enabled": false}' > ~/.claude-voice.json
```

Re-enable:
```bash
echo '{"enabled": true}' > ~/.claude-voice.json
```

## Project Structure

```
claude-voice/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest with hooks
├── hooks/
│   ├── system_prompt.py      # Injects narration instructions
│   └── on_output.py          # Detects and speaks narration markers
├── models/
│   └── .gitkeep              # Models downloaded on first run
├── src/
│   ├── __init__.py
│   ├── config.py             # Configuration loader
│   ├── tts_engine.py         # Kokoro TTS wrapper
│   ├── audio_player.py       # Cross-platform audio playback
│   └── model_manager.py      # Auto-download Kokoro model
├── config/
│   └── default_config.json   # Default configuration
├── scripts/
│   └── install.sh            # Post-install setup script
├── tests/
│   └── test_plugin.py        # Unit tests
├── requirements.txt
├── README.md
└── LICENSE
```

## Troubleshooting

### No audio playing

1. **Check if enabled:** Verify `~/.claude-voice.json` has `"enabled": true`
2. **Check audio player:** Run `which aplay paplay ffplay afplay` to see what's available
3. **Check model files:** Ensure `~/.cache/claude-voice/` contains `kokoro-v0_19.onnx` and `voices.json`
4. **Re-download models:** Delete `~/.cache/claude-voice/` and run `python3 -c "from src.model_manager import ensure_models; ensure_models()"`

### Model download fails

- Check your internet connection
- Try downloading manually from the [kokoro-onnx releases](https://github.com/thewh1teagle/kokoro-onnx/releases)
- Place files in `~/.cache/claude-voice/`

### Import errors

```bash
pip3 install -r requirements.txt
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
python3 -m pytest tests/ -v
```

Or with unittest:

```bash
python3 -m unittest tests.test_plugin -v
```

## Platform Notes

| Platform | Audio Player | Notes |
|----------|-------------|-------|
| macOS | `afplay` (built-in) | Works out of the box |
| Linux | `aplay` / `paplay` / `ffplay` | Need to install one |
| Windows | `winsound` (built-in) | Works out of the box |

## License

[MIT](LICENSE) — see LICENSE file for details.
