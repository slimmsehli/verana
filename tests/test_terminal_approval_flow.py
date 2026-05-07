from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, AsyncIterator

from agent.core import Agent
from config_models import MCPServerConfig
from llm.base import LLMProvider, LLMResponse, Message


class ScriptedProvider(LLMProvider):
    """Deterministic provider that emits two terminal tool calls then final text."""

    def __init__(self) -> None:
        self._step = 0

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
        stream: bool,
    ) -> LLMResponse:
        self._step += 1
        if self._step == 1:
            return LLMResponse(
                content="Create summary.txt first.",
                tool_calls=[
                    {
                        "id": "tc-1",
                        "function": {
                            "name": "terminal-tools__run_command",
                            "arguments": {
                                "command": "printf 'Summary file created\\n' > summary.txt",
                            },
                        },
                    }
                ],
                input_tokens=10,
                output_tokens=20,
                stop_reason="tool_use",
            )
        if self._step == 2:
            return LLMResponse(
                content="Append a second line.",
                tool_calls=[
                    {
                        "id": "tc-2",
                        "function": {
                            "name": "terminal-tools__run_command",
                            "arguments": {
                                "command": "printf 'Additional text added\\n' >> summary.txt",
                            },
                        },
                    }
                ],
                input_tokens=10,
                output_tokens=20,
                stop_reason="tool_use",
            )
        return LLMResponse(
            content="Done. File was created and updated.",
            tool_calls=[],
            input_tokens=5,
            output_tokens=10,
            stop_reason="end_turn",
        )

    async def stream_complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system: str | None,
        temperature: float,
    ) -> AsyncIterator[str]:
        yield "streaming not used in this test"

    def list_models(self) -> list[str]:
        return ["scripted-test-model"]


def test_terminal_tool_calls_require_and_use_approval(monkeypatch: Any, tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    work_dir = tmp_path / "work"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Replace live provider creation with deterministic scripted behavior.
    monkeypatch.setattr("agent.core.make_provider", lambda *_args, **_kwargs: ScriptedProvider())

    agent = Agent(repo_root)
    terminal_server = MCPServerConfig(
        name="terminal-tools",
        description="Terminal test server",
        transport="stdio",
        enabled=True,
        command="python3",
        args=[str(repo_root / "demo" / "mcp" / "terminal_mcp_server.py")],
        env={"TERMINAL_MCP_ROOT": str(work_dir)},
        auth=None,
    )
    agent.cfg.mcp_servers.mcp_servers = [terminal_server]

    approvals: list[tuple[str, dict[str, Any]]] = []

    def approve(tool_name: str, arguments: dict[str, Any]) -> bool:
        approvals.append((tool_name, arguments))
        return True

    context = asyncio.run(
        agent.run_once(
            user_text="Create a summary file, then append text.",
            provider_name="openai",
            model_name="gpt-4o",
            mode_name="debug",
            session_id=None,
            tool_approval_callback=approve,
        )
    )
    print(f" ================================================= \n\n\n TEST CHECKPOINT START\n\n\n")
    summary = work_dir / "summary.txt"
    print(f"summary path: {summary}")
    print(f"summary exists: {summary.exists()}")
    assert summary.exists()
    content = summary.read_text(encoding="utf-8")
    
    print(f"summary content:\n{content}")
    assert "Summary file created" in content
    assert "Additional text added" in content
    assert len(approvals) == 2
    assert all(name == "terminal-tools__run_command" for name, _ in approvals)
    assert "Done." in str(context.messages[-1].content)
    print(f"\n\n\n TEST CHECKPOINT END \n\n\n =================================================")
