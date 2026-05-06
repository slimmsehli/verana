from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator


@dataclass
class Message:
    role: str
    content: str | list[Any]
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    react_step: str | None = None


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict[str, Any]]
    input_tokens: int
    output_tokens: int
    stop_reason: str


class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
        stream: bool,
    ) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream_complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    @abstractmethod
    def list_models(self) -> list[str]:
        raise NotImplementedError

