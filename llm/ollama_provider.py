from __future__ import annotations

from typing import Any, AsyncIterator

import ollama

from llm.base import LLMProvider, LLMResponse, Message


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str, models: list[str]):
        self.model = model
        self._models = models or [model]
        self.client = ollama.AsyncClient(host=base_url)

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
        stream: bool,
    ) -> LLMResponse:
        payload = [{"role": m.role, "content": str(m.content)} for m in messages]
        if system:
            payload = [{"role": "system", "content": system}] + payload
        resp = await self.client.chat(
            model=self.model,
            messages=payload,
            stream=False,
            options={"temperature": temperature},
        )
        content = resp.get("message", {}).get("content", "")
        return LLMResponse(
            content=content,
            tool_calls=[],
            input_tokens=0,
            output_tokens=0,
            stop_reason="end_turn",
        )

    async def stream_complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
    ) -> AsyncIterator[str]:
        payload = [{"role": m.role, "content": str(m.content)} for m in messages]
        if system:
            payload = [{"role": "system", "content": system}] + payload
        stream = await self.client.chat(
            model=self.model,
            messages=payload,
            stream=True,
            options={"temperature": temperature},
        )
        async for chunk in stream:
            text = chunk.get("message", {}).get("content", "")
            if text:
                yield text

    def list_models(self) -> list[str]:
        if self._models:
            return self._models
        try:
            data = ollama.list()
            return [m["model"] for m in data.get("models", [])]
        except Exception:
            return [self.model]

