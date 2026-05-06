from __future__ import annotations

import httpx

from plugins.base import Plugin


class SlackNotifierPlugin(Plugin):
    name = "slack_notifier"
    description = "Posts a Slack message when the agent produces a final answer"

    def __init__(self, config: dict):
        super().__init__(config)
        self.webhook_url = config.get("webhook_url", "")

    def on_final_answer(self, content: str) -> None:
        if not self.webhook_url:
            return
        httpx.post(self.webhook_url, json={"text": f"rtl-agent: {content[:200]}"}, timeout=10)

