from __future__ import annotations

from typing import Any


class Plugin:
    """Base class for all rtl-agent plugins."""

    name: str = "unnamed_plugin"
    version: str = "1.0"
    description: str = ""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def on_session_start(self, context: Any) -> None:
        return None

    def on_session_end(self, context: Any) -> None:
        return None

    def on_before_llm_call(self, messages: list, tools: list) -> None:
        return None

    def on_after_llm_call(self, response: Any) -> None:
        return None

    def on_before_tool_call(self, tool_name: str, arguments: dict) -> None:
        return None

    def on_after_tool_call(self, tool_name: str, arguments: dict, result: dict) -> None:
        return None

    def on_final_answer(self, content: str) -> None:
        return None

    def on_budget_warning(self, budget_status: dict) -> None:
        return None

    def on_budget_exhausted(self, budget_status: dict) -> None:
        return None

