from __future__ import annotations

import json
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from llm.base import LLMProvider, LLMResponse, Message


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None, model: str, models: list[str], base_url: str | None, timeout: int):
        self.model = model
        self._models = models or [model]
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    @staticmethod
    def _convert_messages(messages: list[Message]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for m in messages:
            payload: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.tool_call_id:
                payload["tool_call_id"] = m.tool_call_id
            if m.tool_calls:
                payload["tool_calls"] = m.tool_calls
            out.append(payload)
        return out

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
        stream: bool,
    ) -> LLMResponse:
        req_messages = self._convert_messages(messages)
        if system:
            req_messages = [{"role": "system", "content": system}] + req_messages

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=req_messages,
            tools=tools or None,
            temperature=temperature,
            stream=False,
        )
        choice = response.choices[0]
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {"raw": args}
                tool_calls.append(
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": args},
                    }
                )

        stop_reason = "tool_use" if tool_calls else "end_turn"
        usage = response.usage
        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            input_tokens=(usage.prompt_tokens if usage else 0),
            output_tokens=(usage.completion_tokens if usage else 0),
            stop_reason=stop_reason,
        )

    async def stream_complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
    ) -> AsyncIterator[str]:
        req_messages = self._convert_messages(messages)
        if system:
            req_messages = [{"role": "system", "content": system}] + req_messages
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=req_messages,
            tools=tools or None,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta

    def list_models(self) -> list[str]:
        return self._models

