from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from config_models import (
    MCPServersFile,
    PluginsFile,
    ProvidersFile,
    RuntimeConfig,
    SettingsFile,
)

ENV_PATTERN = re.compile(r"^\$\{([A-Z0-9_]+)\}$")


def _interpolate_env(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _interpolate_env(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_interpolate_env(v) for v in data]
    if isinstance(data, str):
        match = ENV_PATTERN.match(data.strip())
        if match:
            return os.getenv(match.group(1))
    return data


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _interpolate_env(loaded)


def ensure_default_layout(root_dir: Path) -> None:
    for p in [
        root_dir / "config",
        root_dir / "config" / "skills",
        root_dir / "config" / "modes",
        root_dir / "sessions",
        root_dir / "plugins_user",
        root_dir / "logs",
        root_dir / "skills" / "builtin",
        root_dir / "modes" / "builtin",
    ]:
        p.mkdir(parents=True, exist_ok=True)


def load_runtime_config(root_dir: Path, env_file: Path | None = None) -> RuntimeConfig:
    load_dotenv(root_dir / ".env", override=False)
    if env_file:
        load_dotenv(env_file, override=True)

    ensure_default_layout(root_dir)
    config_dir = root_dir / "config"

    settings = SettingsFile.model_validate(_read_yaml(config_dir / "settings.yaml"))
    providers = ProvidersFile.model_validate(_read_yaml(config_dir / "providers.yaml"))
    mcp_servers = MCPServersFile.model_validate(_read_yaml(config_dir / "mcp_servers.yaml"))
    plugins = PluginsFile.model_validate(_read_yaml(config_dir / "plugins.yaml"))

    return RuntimeConfig(
        root_dir=root_dir,
        settings=settings,
        providers=providers,
        mcp_servers=mcp_servers,
        plugins=plugins,
    )

