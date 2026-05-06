from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonlines

from llm.base import Message
from session.models import BudgetState, SessionMessage, SessionMetadata


def _new_session_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{ts}"


class SessionManager:
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        provider: str,
        model: str,
        mode: str,
        active_skills: list[str],
        budget: BudgetState,
        title: str = "",
        planner_provider: str | None = None,
        planner_model: str | None = None,
    ) -> SessionMetadata:
        session_id = _new_session_id()
        sdir = self.storage_dir / session_id
        (sdir / "artifacts").mkdir(parents=True, exist_ok=True)
        metadata = SessionMetadata(
            session_id=session_id,
            provider=provider,
            model=model,
            planner_provider=planner_provider,
            planner_model=planner_model,
            mode=mode,
            active_skills=active_skills,
            title=title,
            budget=budget,
        )
        self.save_metadata(session_id, metadata)
        return metadata

    def session_dir(self, session_id: str) -> Path:
        return self.storage_dir / session_id

    def save_metadata(self, session_id: str, metadata: SessionMetadata) -> None:
        metadata.last_updated = datetime.now(timezone.utc).isoformat()
        path = self.session_dir(session_id) / "metadata.json"
        path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    def load_metadata(self, session_id: str) -> SessionMetadata:
        path = self.session_dir(session_id) / "metadata.json"
        return SessionMetadata.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def append_message(self, session_id: str, msg: SessionMessage) -> None:
        path = self.session_dir(session_id) / "messages.jsonl"
        with jsonlines.open(path, mode="a") as writer:
            writer.write(msg.model_dump())

    def load_messages(self, session_id: str) -> list[Message]:
        path = self.session_dir(session_id) / "messages.jsonl"
        if not path.exists():
            return []
        out: list[Message] = []
        with jsonlines.open(path, mode="r") as reader:
            for row in reader:
                out.append(Message(role=row["role"], content=row["content"], tool_calls=row.get("tool_calls")))
        return out

    def list_sessions(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for p in sorted(self.storage_dir.glob("*"), reverse=True):
            md = p / "metadata.json"
            if md.exists():
                try:
                    out.append(json.loads(md.read_text(encoding="utf-8")))
                except Exception:
                    continue
        return out

