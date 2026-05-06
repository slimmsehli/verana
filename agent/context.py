from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from llm.base import Message
from session.models import SessionMetadata


@dataclass
class AgentContext:
    session_id: str
    session_dir: Path
    provider: str
    model: str
    mode: str
    active_skills: list[str] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    metadata: SessionMetadata | None = None
    plan: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

