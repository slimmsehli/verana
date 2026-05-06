from __future__ import annotations

from pathlib import Path

import yaml

from config_models import SkillConfig


class SkillRegistry:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.skills: dict[str, SkillConfig] = {}

    def load(self) -> None:
        self.skills.clear()
        paths = []
        for base in [self.root_dir / "skills" / "builtin", self.root_dir / "config" / "skills"]:
            if base.exists():
                paths.extend(sorted(base.glob("*.yaml")))
        for path in paths:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            skill = SkillConfig.model_validate(data)
            self.skills[skill.name] = skill

    def list(self) -> list[str]:
        return sorted(self.skills.keys())

    def get(self, name: str) -> SkillConfig:
        if name not in self.skills:
            raise KeyError(f"Unknown skill: {name}")
        return self.skills[name]

