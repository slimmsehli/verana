from __future__ import annotations

from typing import Any

from plugins.base import Plugin


class ExampleHookPlugin(Plugin):
    name = "example_hook"
    description = "Example plugin showing hook usage"

    def on_session_start(self, context: Any) -> None:
        return None

