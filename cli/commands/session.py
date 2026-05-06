from __future__ import annotations

import json
from pathlib import Path

import typer

from session.manager import SessionManager

session_app = typer.Typer(help="Manage saved sessions.")


def _mgr() -> SessionManager:
    return SessionManager(Path.cwd() / "sessions")


@session_app.command("list")
def list_sessions(filter: str = typer.Option("", "--filter")) -> None:
    rows = _mgr().list_sessions()
    for row in rows:
        blob = json.dumps(row)
        if filter and filter not in blob:
            continue
        typer.echo(f"{row.get('session_id')}  {row.get('title', '')}  mode={row.get('mode')}")


@session_app.command("show")
def show_session(session_id: str) -> None:
    md = _mgr().load_metadata(session_id)
    typer.echo(md.model_dump_json(indent=2))


@session_app.command("resume")
def resume_session(session_id: str) -> None:
    typer.echo(f"Use: rtl-agent run --session {session_id}")


@session_app.command("export")
def export_session(session_id: str, format: str = typer.Option("md", "--format")) -> None:
    mgr = _mgr()
    sdir = mgr.session_dir(session_id)
    msg_file = sdir / "messages.jsonl"
    if not msg_file.exists():
        raise typer.BadParameter("No messages found for session")
    lines = []
    for row in msg_file.read_text(encoding="utf-8").splitlines():
        data = json.loads(row)
        lines.append(f"## {data.get('role', 'unknown')}\n\n{data.get('content', '')}\n")
    artifacts = sdir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    if format == "json":
        out = artifacts / "session_export.json"
        out.write_text(msg_file.read_text(encoding="utf-8"), encoding="utf-8")
    elif format == "html":
        out = artifacts / "session_export.html"
        body = "<br/>".join(lines).replace("\n", "<br/>")
        out.write_text(f"<html><body>{body}</body></html>", encoding="utf-8")
    else:
        out = artifacts / "session_export.md"
        out.write_text("\n".join(lines), encoding="utf-8")
    typer.echo(str(out))


@session_app.command("delete")
def delete_session(session_id: str) -> None:
    sdir = _mgr().session_dir(session_id)
    if not sdir.exists():
        raise typer.BadParameter("Session not found")
    for p in sorted(sdir.rglob("*"), reverse=True):
        if p.is_file():
            p.unlink()
        else:
            p.rmdir()
    sdir.rmdir()
    typer.echo(f"Deleted session {session_id}")


@session_app.command("tag")
def tag_session(session_id: str, add: str = typer.Option(..., "--add")) -> None:
    mgr = _mgr()
    md = mgr.load_metadata(session_id)
    if add not in md.tags:
        md.tags.append(add)
    mgr.save_metadata(session_id, md)
    typer.echo(f"Added tag '{add}' to {session_id}")


@session_app.command("artifacts")
def list_artifacts(session_id: str) -> None:
    adir = _mgr().session_dir(session_id) / "artifacts"
    if not adir.exists():
        typer.echo("No artifacts")
        return
    for p in sorted(adir.glob("*")):
        typer.echo(f"{p.name}\t{p.stat().st_size} bytes")

