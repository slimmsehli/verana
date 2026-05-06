from __future__ import annotations

from typing import Any, AsyncIterator

import google.generativeai as genai

from llm.base import LLMProvider, LLMResponse, Message


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None, model: str, models: list[str], timeout: int):
        self.model = model
        self._models = models or [model]
        genai.configure(api_key=api_key)
        self.timeout = timeout

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
        stream: bool,
    ) -> LLMResponse:
        model = genai.GenerativeModel(self.model, system_instruction=system or "")
        prompt = "\n".join([f"{m.role}: {m.content}" for m in messages])
        response = await model.generate_content_async(prompt)
        text = (response.text or "").strip()
        return LLMResponse(
            content=text,
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
        model = genai.GenerativeModel(self.model, system_instruction=system or "")
        prompt = "\n".join([f"{m.role}: {m.content}" for m in messages])
        response = await model.generate_content_async(prompt, stream=True)
        async for chunk in response:
            text = getattr(chunk, "text", "")
            if text:
                yield text

    def list_models(self) -> list[str]:
        return self._models

