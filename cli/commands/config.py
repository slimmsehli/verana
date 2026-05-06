from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import typer
import yaml

from config_loader import load_runtime_config

config_app = typer.Typer(help="View and edit configuration.")


@config_app.command("show")
def config_show() -> None:
    cfg = load_runtime_config(Path.cwd())
    typer.echo(cfg.model_dump_json(indent=2, exclude={"root_dir"}))


@config_app.command("edit")
def config_edit() -> None:
    path = Path.cwd() / "config" / "settings.yaml"
    editor = os.getenv("EDITOR", "vi")
    os.system(f'{editor} "{path}"')


@config_app.command("get")
def config_get(key: str) -> None:
    data = yaml.safe_load((Path.cwd() / "config" / "settings.yaml").read_text(encoding="utf-8")) or {}
    value = _get_dotted(data, key)
    typer.echo(str(value))


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    path = Path.cwd() / "config" / "settings.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    _set_dotted(data, key, _parse_scalar(value))
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    typer.echo(f"Set {key}={value}")


@config_app.command("validate")
def config_validate() -> None:
    load_runtime_config(Path.cwd())
    typer.echo("Configuration valid.")


@config_app.command("reset")
def config_reset(confirm: bool = typer.Option(False, "--yes")) -> None:
    if not confirm:
        raise typer.BadParameter("Pass --yes to confirm reset.")
    root = Path.cwd()
    defaults = {
        "settings.yaml": root / "config" / "settings.yaml",
        "providers.yaml": root / "config" / "providers.yaml",
        "mcp_servers.yaml": root / "config" / "mcp_servers.yaml",
        "plugins.yaml": root / "config" / "plugins.yaml",
    }
    for name, target in defaults.items():
        src = root / "config" / name
        if src.exists():
            target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    typer.echo("Configuration reset to current checked-in defaults.")


def _get_dotted(data: dict[str, Any], key: str) -> Any:
    cur: Any = data
    for part in key.split("."):
        cur = cur[part]
    return cur


def _set_dotted(data: dict[str, Any], key: str, value: Any) -> None:
    parts = key.split(".")
    cur = data
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


def _parse_scalar(raw: str) -> Any:
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    if raw.lower() in {"null", "none"}:
        return None
    return raw

