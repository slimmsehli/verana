from __future__ import annotations

from pathlib import Path

import typer
import yaml

from cli.display import budget_line
from session.manager import SessionManager

budget_app = typer.Typer(help="View and configure token budgets.")


@budget_app.command("status")
def budget_status() -> None:
    mgr = SessionManager(Path.cwd() / "sessions")
    rows = mgr.list_sessions()
    if not rows:
        typer.echo("No sessions found")
        return
    md = rows[0]
    b = md.get("budget", {})
    typer.echo(
        budget_line(
            b.get("used_input_tokens", 0),
            b.get("max_input_tokens", 1),
            b.get("used_output_tokens", 0),
            b.get("max_output_tokens", 1),
        )
    )


@budget_app.command("set")
def budget_set(
    input: int = typer.Option(..., "--input"),
    output: int = typer.Option(..., "--output"),
) -> None:
    path = Path.cwd() / "config" / "settings.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("budget", {})
    data["budget"]["max_input_tokens"] = input
    data["budget"]["max_output_tokens"] = output
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    typer.echo("Updated budget defaults in config/settings.yaml")

