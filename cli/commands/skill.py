from __future__ import annotations

import os
from pathlib import Path

import typer
import yaml

from skills.registry import SkillRegistry

skill_app = typer.Typer(help="Manage skills.")


def _registry() -> SkillRegistry:
    reg = SkillRegistry(Path.cwd())
    reg.load()
    return reg


@skill_app.command("list")
def list_skills() -> None:
    for s in _registry().list():
        typer.echo(s)


@skill_app.command("show")
def show_skill(name: str) -> None:
    skill = _registry().get(name)
    typer.echo(yaml.safe_dump(skill.model_dump(), sort_keys=False))


@skill_app.command("create")
def create_skill(name: str) -> None:
    path = Path.cwd() / "config" / "skills" / f"{name}.yaml"
    if path.exists():
        raise typer.BadParameter("Skill already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    template = {
        "name": name,
        "version": "1.0",
        "description": "Describe this skill",
        "system_prompt": "Add behavior instructions here.",
        "preferred_tools": [],
        "suggested_mode": None,
        "few_shot_examples": [],
        "tags": [],
    }
    path.write_text(yaml.safe_dump(template, sort_keys=False), encoding="utf-8")
    typer.echo(str(path))


@skill_app.command("edit")
def edit_skill(name: str) -> None:
    path = Path.cwd() / "config" / "skills" / f"{name}.yaml"
    if not path.exists():
        raise typer.BadParameter("Only user-defined skills are editable here.")
    editor = os.getenv("EDITOR", "vi")
    os.system(f'{editor} "{path}"')


@skill_app.command("delete")
def delete_skill(name: str) -> None:
    path = Path.cwd() / "config" / "skills" / f"{name}.yaml"
    if not path.exists():
        raise typer.BadParameter("Skill not found in config/skills")
    path.unlink()
    typer.echo(f"Deleted {name}")

