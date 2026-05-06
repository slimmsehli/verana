from __future__ import annotations

from typing import Any, AsyncIterator

from anthropic import AsyncAnthropic

from llm.base import LLMProvider, LLMResponse, Message


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str | None, model: str, models: list[str], base_url: str | None, timeout: int):
        self.model = model
        self._models = models or [model]
        self.client = AsyncAnthropic(api_key=api_key, base_url=base_url, timeout=timeout)

    @staticmethod
    def _convert_messages(messages: list[Message]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for m in messages:
            role = m.role if m.role in {"user", "assistant"} else "user"
            out.append({"role": role, "content": m.content if isinstance(m.content, str) else str(m.content)})
        return out

    @staticmethod
    def _convert_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        converted = []
        for t in tools:
            fn = t.get("function", {})
            converted.append(
                {
                    "name": fn.get("name"),
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
                }
            )
        return converted

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
        stream: bool,
    ) -> LLMResponse:
        resp = await self.client.messages.create(
            model=self.model,
            system=system or "",
            messages=self._convert_messages(messages),
            tools=self._convert_tools(tools),
            temperature=temperature,
            max_tokens=4096,
        )
        tool_calls: list[dict[str, Any]] = []
        text_parts: list[str] = []
        for block in resp.content:
            btype = getattr(block, "type", "")
            if btype == "text":
                text_parts.append(block.text)
            if btype == "tool_use":
                tool_calls.append(
                    {
                        "id": block.id,
                        "type": "function",
                        "function": {"name": block.name, "arguments": block.input or {}},
                    }
                )
        stop_reason = "tool_use" if tool_calls else "end_turn"
        usage = getattr(resp, "usage", None)
        return LLMResponse(
            content="\n".join(text_parts).strip(),
            tool_calls=tool_calls,
            input_tokens=getattr(usage, "input_tokens", 0),
            output_tokens=getattr(usage, "output_tokens", 0),
            stop_reason=stop_reason,
        )

    async def stream_complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
    ) -> AsyncIterator[str]:
        stream = await self.client.messages.stream(
            model=self.model,
            system=system or "",
            messages=self._convert_messages(messages),
            tools=self._convert_tools(tools),
            temperature=temperature,
            max_tokens=4096,
        )
        async with stream as s:
            async for text in s.text_stream:
                yield text

    def list_models(self) -> list[str]:
        return self._models

