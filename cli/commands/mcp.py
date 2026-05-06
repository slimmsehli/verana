from __future__ import annotations

import asyncio
from pathlib import Path

import typer
import yaml

from config_loader import load_runtime_config
from mcp.registry import MCPRegistry

mcp_app = typer.Typer(help="Manage MCP server connections.")


@mcp_app.command("list")
def list_mcp() -> None:
    cfg = load_runtime_config(Path.cwd())
    for s in cfg.mcp_servers.mcp_servers:
        typer.echo(f"{s.name}\t{s.transport}\tenabled={s.enabled}")


@mcp_app.command("status")
def status_mcp() -> None:
    cfg = load_runtime_config(Path.cwd())
    reg = MCPRegistry()

    async def _run() -> None:
        await reg.connect_servers(cfg.mcp_servers.mcp_servers)
        for name, client in reg.clients.items():
            healthy = await client.health_check()
            typer.echo(f"{name}\t{'ok' if healthy else 'down'}")
        await reg.disconnect_all()

    asyncio.run(_run())


@mcp_app.command("reload")
def reload_mcp() -> None:
    typer.echo("MCP hot reload is applied on next run invocation.")


@mcp_app.command("add")
def add_mcp() -> None:
    path = Path.cwd() / "config" / "mcp_servers.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    row = {
        "name": typer.prompt("name"),
        "description": typer.prompt("description", default=""),
        "transport": typer.prompt("transport (stdio/http)", default="stdio"),
        "enabled": True,
    }
    if row["transport"] == "stdio":
        row["command"] = typer.prompt("command")
        row["args"] = []
        row["auth"] = None
    else:
        row["url"] = typer.prompt("url")
        row["auth"] = None
    data.setdefault("mcp_servers", []).append(row)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    typer.echo(f"Added {row['name']}")


@mcp_app.command("remove")
def remove_mcp(name: str) -> None:
    path = Path.cwd() / "config" / "mcp_servers.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    servers = data.get("mcp_servers", [])
    kept = [s for s in servers if s.get("name") != name]
    if len(kept) == len(servers):
        raise typer.BadParameter("Server not found")
    data["mcp_servers"] = kept
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    typer.echo(f"Removed {name}")


@mcp_app.command("tools")
def tools_mcp(name: str) -> None:
    cfg = load_runtime_config(Path.cwd())
    server = next((s for s in cfg.mcp_servers.mcp_servers if s.name == name), None)
    if not server:
        raise typer.BadParameter("Unknown server")
    reg = MCPRegistry()

    async def _run() -> None:
        await reg.connect_servers([server])
        client = reg.clients.get(name)
        if not client:
            typer.echo("Failed to connect")
            return
        tools = await client.list_tools()
        for t in tools:
            typer.echo(t.get("name", ""))
        await reg.disconnect_all()

    asyncio.run(_run())


@mcp_app.command("enable")
def enable_mcp(name: str) -> None:
    path = Path.cwd() / "config" / "mcp_servers.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    changed = False
    for row in data.get("mcp_servers", []):
        if row.get("name") == name:
            row["enabled"] = True
            changed = True
    if not changed:
        raise typer.BadParameter("Server not found")
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    typer.echo(f"Enabled {name}")


@mcp_app.command("disable")
def disable_mcp(name: str) -> None:
    path = Path.cwd() / "config" / "mcp_servers.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    changed = False
    for row in data.get("mcp_servers", []):
        if row.get("name") == name:
            row["enabled"] = False
            changed = True
    if not changed:
        raise typer.BadParameter("Server not found")
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    typer.echo(f"Disabled {name}")

