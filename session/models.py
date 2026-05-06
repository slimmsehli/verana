from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BudgetState(BaseModel):
    max_input_tokens: int
    max_output_tokens: int
    used_input_tokens: int = 0
    used_output_tokens: int = 0

    def input_pct(self) -> float:
        if self.max_input_tokens <= 0:
            return 0.0
        return (self.used_input_tokens / self.max_input_tokens) * 100.0

    def output_pct(self) -> float:
        if self.max_output_tokens <= 0:
            return 0.0
        return (self.used_output_tokens / self.max_output_tokens) * 100.0

    def consumed_pct(self) -> float:
        return max(self.input_pct(), self.output_pct())


class SessionMetadata(BaseModel):
    session_id: str
    created_at: str = Field(default_factory=utc_now_iso)
    last_updated: str = Field(default_factory=utc_now_iso)
    provider: str
    model: str
    model_locked: bool = True
    planner_provider: str | None = None
    planner_model: str | None = None
    mode: str
    active_skills: list[str] = Field(default_factory=list)
    title: str = ""
    tags: list[str] = Field(default_factory=list)
    message_count: int = 0
    budget: BudgetState


class SessionMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Any
    tool_calls: list[dict[str, Any]] | None = None
    tool_results: list[dict[str, Any]] | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    timestamp: str = Field(default_factory=utc_now_iso)
    react_step: Literal["thought", "action", "observation", "final"] | None = None

