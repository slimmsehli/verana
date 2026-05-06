from __future__ import annotations

from pathlib import Path

import typer

from config_loader import load_runtime_config
from plugins.loader import PluginManager

plugin_app = typer.Typer(help="Manage plugins.")


@plugin_app.command("list")
def list_plugins() -> None:
    cfg = load_runtime_config(Path.cwd())
    for p in cfg.plugins.plugins:
        typer.echo(f"{p.name}\tenabled={p.enabled}\t{p.path}")


@plugin_app.command("show")
def show_plugin(name: str) -> None:
    cfg = load_runtime_config(Path.cwd())
    for p in cfg.plugins.plugins:
        if p.name == name:
            typer.echo(p.model_dump_json(indent=2))
            return
    raise typer.BadParameter("Plugin not found")


@plugin_app.command("reload")
def reload_plugins() -> None:
    cfg = load_runtime_config(Path.cwd())
    manager = PluginManager()
    manager.load(cfg.plugins.plugins, Path.cwd() / cfg.settings.plugins.plugin_dir)
    typer.echo(f"Loaded {len(manager.plugins)} plugin(s)")


@plugin_app.command("enable")
def enable_plugin(name: str) -> None:
    _toggle_plugin(name, True)


@plugin_app.command("disable")
def disable_plugin(name: str) -> None:
    _toggle_plugin(name, False)


def _toggle_plugin(name: str, enabled: bool) -> None:
    import yaml

    path = Path.cwd() / "config" / "plugins.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    changed = False
    for row in data.get("plugins", []):
        if row.get("name") == name:
            row["enabled"] = enabled
            changed = True
    if not changed:
        raise typer.BadParameter("Plugin not found")
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    typer.echo(f"{'Enabled' if enabled else 'Disabled'} {name}")

