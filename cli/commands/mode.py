from __future__ import annotations

import os
from pathlib import Path

import typer
import yaml

from modes.registry import ModeRegistry

mode_app = typer.Typer(help="Manage modes.")


def _registry() -> ModeRegistry:
    reg = ModeRegistry(Path.cwd())
    reg.load()
    return reg


@mode_app.command("list")
def list_modes() -> None:
    for m in _registry().list():
        typer.echo(m)


@mode_app.command("show")
def show_mode(name: str) -> None:
    mode = _registry().get(name)
    typer.echo(yaml.safe_dump(mode.model_dump(), sort_keys=False))


@mode_app.command("create")
def create_mode(name: str) -> None:
    path = Path.cwd() / "config" / "modes" / f"{name}.yaml"
    if path.exists():
        raise typer.BadParameter("Mode already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    template = {
        "name": name,
        "description": "Describe this mode",
        "system_prompt_suffix": "",
        "preferred_skills": [],
        "use_planner": False,
        "plan_approval": False,
        "react_loop": {
            "max_iterations": 15,
            "show_thought": True,
            "show_action": True,
            "show_observation": True,
            "abort_on_error": False,
            "iteration_warning": 10,
            "output_format": "markdown",
        },
    }
    path.write_text(yaml.safe_dump(template, sort_keys=False), encoding="utf-8")
    typer.echo(str(path))


@mode_app.command("edit")
def edit_mode(name: str) -> None:
    path = Path.cwd() / "config" / "modes" / f"{name}.yaml"
    if not path.exists():
        raise typer.BadParameter("Only user-defined modes are editable here.")
    editor = os.getenv("EDITOR", "vi")
    os.system(f'{editor} "{path}"')

