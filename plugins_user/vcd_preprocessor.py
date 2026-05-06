from __future__ import annotations

from pathlib import Path

from plugins.base import Plugin


class VCDPreprocessorPlugin(Plugin):
    name = "vcd_preprocessor"
    description = "Pre-process oversized VCD file paths before MCP tool calls"

    def __init__(self, config: dict):
        super().__init__(config)
        self.max_signals = config.get("max_signals", 500)

    def on_before_tool_call(self, tool_name: str, arguments: dict) -> None:
        if "waveform" not in tool_name:
            return
        path = arguments.get("file_path", "")
        if path and Path(path).suffix.lower() in {".vcd", ".fsdb"}:
            arguments.setdefault("max_signals", self.max_signals)

