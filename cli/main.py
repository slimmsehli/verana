from __future__ import annotations

from pathlib import Path

import typer
import yaml

from cli.commands.budget import budget_app
from cli.commands.config import config_app
from cli.commands.mcp import mcp_app
from cli.commands.mode import mode_app
from cli.commands.plugin import plugin_app
from cli.commands.run import run_app
from cli.commands.session import session_app
from cli.commands.skill import skill_app
from config_loader import load_runtime_config
from llm.provider_factory import make_provider

app = typer.Typer(help="rtl-agent CLI")

app.add_typer(run_app, name="run")
app.add_typer(session_app, name="session")
app.add_typer(skill_app, name="skill")
app.add_typer(mode_app, name="mode")
app.add_typer(mcp_app, name="mcp")
app.add_typer(plugin_app, name="plugin")
app.add_typer(budget_app, name="budget")
app.add_typer(config_app, name="config")


model_app = typer.Typer(help="List and set models.")
app.add_typer(model_app, name="model")


@model_app.command("list")
def model_list(provider: str | None = typer.Option(None, "--provider")) -> None:
    cfg = load_runtime_config(Path.cwd())
    names = [provider] if provider else sorted(cfg.providers.providers.keys())
    for pname in names:
        if not pname:
            continue
        model_provider = make_provider(pname, None, cfg.providers)
        for m in model_provider.list_models():
            typer.echo(f"{pname}/{m}")


@model_app.command("set")
def model_set(value: str) -> None:
    if "/" not in value:
        raise typer.BadParameter("Use provider/model format")
    provider, model = value.split("/", 1)
    path = Path.cwd() / "config" / "settings.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("agent", {})
    data["agent"]["default_provider"] = provider
    data["agent"]["default_model"] = model
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    typer.echo(f"Updated default model to {provider}/{model}")


if __name__ == "__main__":
    app()

