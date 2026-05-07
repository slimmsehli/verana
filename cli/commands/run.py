from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import typer

from agent.core import Agent
from cli.display import (
    budget_line,
    show_action,
    show_final,
    show_observation,
    show_thought,
    show_warning,
)
from session.manager import SessionManager

run_app = typer.Typer(help="Start or resume an agent session.")


@run_app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    provider: str | None = typer.Option(None, "--provider"),
    model: str | None = typer.Option(None, "--model"),
    mode: str | None = typer.Option(None, "--mode"),
    skills: str | None = typer.Option(None, "--skills"),
    session: str | None = typer.Option(None, "--session"),
    title: str = typer.Option("", "--title"),
    budget_input: int | None = typer.Option(None, "--budget-input"),
    budget_output: int | None = typer.Option(None, "--budget-output"),
    env_file: Path | None = typer.Option(None, "--env-file"),
    confirm_terminal: bool = typer.Option(
        True,
        "--confirm-terminal/--no-confirm-terminal",
        help="Require interactive approval before terminal MCP tool calls.",
    ),
    no_stream: bool = typer.Option(False, "--no-stream"),
    quiet: bool = typer.Option(False, "--quiet"),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    root = Path.cwd()
    agent = Agent(root, env_file=env_file)
    active_skills = [s.strip() for s in (skills or "").split(",") if s.strip()]
    current_mode = mode
    manager = SessionManager(root / "sessions")

    typer.echo("Enter your prompt (or /quit):")
    while True:
        user = typer.prompt("> ")
        if user.strip() == "/quit":
            typer.echo("Session saved. Bye.")
            break

        if user.startswith("/"):
            cmd = user.strip()
            if cmd == "/help":
                typer.echo(
                    "/mode <name>, /skill add <name>, /skill remove <name>, /skill list, "
                    "/tools, /budget, /history, /save, /export, /clear, /plan, /quit"
                )
            elif cmd.startswith("/mode "):
                current_mode = cmd.split(maxsplit=1)[1].strip()
                typer.echo(f"Mode set to {current_mode} (next turn).")
            elif cmd.startswith("/skill add "):
                sname = cmd.split(maxsplit=2)[2].strip()
                if sname not in active_skills:
                    active_skills.append(sname)
                typer.echo(f"Added skill: {sname}")
            elif cmd.startswith("/skill remove "):
                sname = cmd.split(maxsplit=2)[2].strip()
                active_skills = [s for s in active_skills if s != sname]
                typer.echo(f"Removed skill: {sname}")
            elif cmd == "/skill list":
                typer.echo(", ".join(active_skills) if active_skills else "(none)")
            elif cmd == "/tools":
                reg = asyncio.run(agent._connect_mcp())
                try:
                    for tool in reg.unified_tools():
                        typer.echo(tool["function"]["name"])
                finally:
                    asyncio.run(reg.disconnect_all())
            elif cmd == "/budget":
                if not session:
                    typer.echo("No active session yet.")
                else:
                    md = manager.load_metadata(session)
                    typer.echo(
                        budget_line(
                            md.budget.used_input_tokens,
                            md.budget.max_input_tokens,
                            md.budget.used_output_tokens,
                            md.budget.max_output_tokens,
                        )
                    )
            elif cmd == "/history":
                if not session:
                    typer.echo("No active session yet.")
                else:
                    md = manager.load_metadata(session)
                    typer.echo(
                        f"messages={md.message_count} in={md.budget.used_input_tokens} out={md.budget.used_output_tokens}"
                    )
            elif cmd == "/save":
                typer.echo("Auto-save is enabled; latest turn is already persisted.")
            elif cmd == "/export":
                if not session:
                    typer.echo("No active session yet.")
                else:
                    sdir = manager.session_dir(session)
                    msg_file = sdir / "messages.jsonl"
                    out = sdir / "artifacts" / "session_export.md"
                    lines = []
                    if msg_file.exists():
                        for row in msg_file.read_text(encoding="utf-8").splitlines():
                            j = json.loads(row)
                            lines.append(f"## {j.get('role','unknown')}\n\n{j.get('content','')}\n")
                    out.write_text("\n".join(lines), encoding="utf-8")
                    typer.echo(f"Exported: {out}")
            elif cmd == "/clear":
                session = None
                title = ""
                typer.echo("Context cleared; next prompt starts a fresh session.")
            elif cmd == "/plan":
                current_mode = "plan"
                typer.echo("Planner mode set for next turn.")
            else:
                typer.echo("Unknown slash command. Use /help.")
            continue

        def on_event(kind: str, payload: str) -> None:
            if quiet:
                return
            if kind == "action":
                show_action(payload)
            elif kind == "thought":
                show_thought(payload)
            elif kind == "observation":
                show_observation(payload)
            elif kind == "warning":
                show_warning(payload)
            elif kind == "final":
                show_final(payload)

        def is_terminal_tool(tool_name: str) -> bool:
            if "__" not in tool_name:
                return False
            server_name, local_tool = tool_name.split("__", 1)
            return "terminal" in server_name or local_tool in {"run_command", "exec_command"}

        def approve_tool_call(tool_name: str, arguments: dict[str, Any]) -> bool:
            if not confirm_terminal or not is_terminal_tool(tool_name):
                return True
            typer.echo(f"\nApproval required for tool call: {tool_name}")
            if arguments:
                try:
                    payload = json.dumps(arguments, indent=2, ensure_ascii=True)
                except Exception:
                    payload = str(arguments)
                if len(payload) > 1200:
                    payload = f"{payload[:1200]}\n...<truncated>..."
                typer.echo(payload)
            allowed = typer.confirm("Allow this terminal action?", default=False)
            if not allowed:
                typer.echo("Tool call denied by user.")
            return allowed

        context = asyncio.run(
            agent.run_once(
                user_text=user,
                provider_name=provider,
                model_name=model,
                mode_name=current_mode,
                skills=active_skills,
                session_id=session,
                title=title,
                budget_input=budget_input,
                budget_output=budget_output,
                on_event=on_event,
                tool_approval_callback=approve_tool_call,
            )
        )
        md = context.metadata
        if md:
            typer.echo(
                budget_line(
                    md.budget.used_input_tokens,
                    md.budget.max_input_tokens,
                    md.budget.used_output_tokens,
                    md.budget.max_output_tokens,
                )
            )
            session = md.session_id

