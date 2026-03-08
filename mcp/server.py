#!/usr/bin/env python
"""MCP server for claude-voice plugin.

Provides a 'speak' tool that Claude can call to speak text aloud.
Uses stdio transport for communication with Claude Code.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add plugin root to path
PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))

from src.config import load_config
from src.model_manager import ensure_models

logger = logging.getLogger("claude-voice-mcp")

# MCP Protocol Constants
JSONRPC_VERSION = "2.0"


class MCPServer:
    """Simple MCP server implementing the speak tool."""

    def __init__(self):
        self.config = load_config()
        self._initialized = False

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Route incoming JSON-RPC requests to handlers."""
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "initialized":
                return None  # Notification, no response needed
            elif method == "tools/list":
                result = self._handle_tools_list()
            elif method == "tools/call":
                result = self._handle_tools_call(params)
            elif method == "shutdown":
                result = {}
            else:
                return self._error_response(req_id, -32601, f"Method not found: {method}")

            return self._success_response(req_id, result)

        except Exception as e:
            logger.error("Request handling error: %s", e)
            return self._error_response(req_id, -32603, str(e))

    def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request - return server capabilities."""
        self._initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "claude-voice", "version": "2.0.0"},
        }

    def _handle_tools_list(self) -> Dict[str, Any]:
        """Return list of available tools."""
        return {
            "tools": [
                {
                    "name": "speak",
                    "description": "Speak text aloud using text-to-speech. Use this to narrate what you're doing, explain findings, or provide audio feedback.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The text to speak aloud",
                            },
                            "voice": {
                                "type": "string",
                                "description": "Voice to use (default: af_bella)",
                                "default": "af_bella",
                            },
                            "speed": {
                                "type": "number",
                                "description": "Speech speed multiplier (default: 1.1)",
                                "default": 1.1,
                            },
                        },
                        "required": ["text"],
                    },
                }
            ]
        }

    def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name != "speak":
            raise ValueError(f"Unknown tool: {tool_name}")

        # Check if enabled
        if not self.config.get("enabled", True):
            return {"content": [{"type": "text", "text": "TTS is disabled in configuration."}]}

        # Check mode
        mode = self.config.get("mode", "stop")
        if mode not in ("mcp", "both"):
            return {
                "content": [
                    {"type": "text", "text": "MCP mode is not enabled. Set mode to 'mcp' or 'both' in ~/.claude-voice.json"}
                ]
            }

        # Extract parameters
        text = arguments.get("text", "")
        voice = arguments.get("voice", self.config.get("voice", "af_bella"))
        speed = arguments.get("speed", self.config.get("speed", 1.1))

        if not text:
            return {"content": [{"type": "text", "text": "No text provided to speak."}]}

        # Generate and play audio
        try:
            from src.audio_player import play_audio_async
            from src.tts_engine import speak

            result = speak(text, voice=voice, speed=speed)
            if result:
                samples, sample_rate = result
                play_audio_async(samples, sample_rate)
                preview = text[:50] + "..." if len(text) > 50 else text
                return {"content": [{"type": "text", "text": f"Speaking: \"{preview}\""}]}
            else:
                return {
                    "content": [{"type": "text", "text": "TTS synthesis failed. Check if models are installed."}],
                    "isError": True,
                }
        except Exception as e:
            return {"content": [{"type": "text", "text": f"TTS error: {str(e)}"}], "isError": True}

    def _success_response(self, req_id: Any, result: Any) -> Dict[str, Any]:
        """Create a successful JSON-RPC response."""
        return {"jsonrpc": JSONRPC_VERSION, "id": req_id, "result": result}

    def _error_response(self, req_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create an error JSON-RPC response."""
        return {"jsonrpc": JSONRPC_VERSION, "id": req_id, "error": {"code": code, "message": message}}


def read_message(stream) -> Optional[Dict[str, Any]]:
    """Read a JSON-RPC message from stdin."""
    # Read headers
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    # Read content
    content_length = int(headers.get("content-length", 0))
    if content_length == 0:
        return None

    content = stream.read(content_length)
    return json.loads(content)


def write_message(stream, message: Dict[str, Any]) -> None:
    """Write a JSON-RPC message to stdout."""
    content = json.dumps(message)
    header = f"Content-Length: {len(content)}\r\n\r\n"
    stream.write(header)
    stream.write(content)
    stream.flush()


def main():
    """Run the MCP server with stdio transport."""
    # Ensure models are available
    ensure_models()

    server = MCPServer()

    # Use binary mode for proper line handling on Windows
    stdin = sys.stdin
    stdout = sys.stdout

    while True:
        try:
            request = read_message(stdin)
            if request is None:
                break

            response = server.handle_request(request)
            if response:
                write_message(stdout, response)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error("Server error: %s", e)
            continue


if __name__ == "__main__":
    main()
