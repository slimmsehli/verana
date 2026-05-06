from __future__ import annotations

from pathlib import Path

import yaml

from config_models import ModeConfig


class ModeRegistry:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.modes: dict[str, ModeConfig] = {}

    def load(self) -> None:
        self.modes.clear()
        paths = []
        for base in [self.root_dir / "modes" / "builtin", self.root_dir / "config" / "modes"]:
            if base.exists():
                paths.extend(sorted(base.glob("*.yaml")))
        for path in paths:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            mode = ModeConfig.model_validate(data)
            self.modes[mode.name] = mode

    def list(self) -> list[str]:
        return sorted(self.modes.keys())

    def get(self, name: str) -> ModeConfig:
        if name not in self.modes:
            raise KeyError(f"Unknown mode: {name}")
        return self.modes[name]

