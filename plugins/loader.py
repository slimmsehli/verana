from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from types import ModuleType

from config_models import PluginEntry
from plugins.base import Plugin

logger = logging.getLogger(__name__)


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load plugin module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract_plugin_class(module: ModuleType) -> type[Plugin]:
    for obj in module.__dict__.values():
        if isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin:
            return obj
    raise RuntimeError("No Plugin subclass found")


class PluginManager:
    def __init__(self):
        self.plugins: list[Plugin] = []

    def load(self, plugin_entries: list[PluginEntry], plugin_dir: Path) -> None:
        self.plugins.clear()
        explicit_paths = {Path(p.path).resolve() for p in plugin_entries}
        candidates: list[tuple[Path, dict]] = []

        for entry in plugin_entries:
            if not entry.enabled:
                continue
            candidates.append((Path(entry.path), entry.config))

        if plugin_dir.exists():
            for py in sorted(plugin_dir.glob("*.py")):
                if py.resolve() not in explicit_paths:
                    candidates.append((py, {}))

        for path, cfg in candidates:
            try:
                module = _load_module(path)
                cls = _extract_plugin_class(module)
                self.plugins.append(cls(cfg))
            except Exception as exc:
                logger.warning("Skipping plugin %s: %s", path, exc)

    def emit(self, hook: str, *args, **kwargs) -> None:
        for plugin in self.plugins:
            fn = getattr(plugin, hook, None)
            if callable(fn):
                try:
                    fn(*args, **kwargs)
                except Exception as exc:
                    logger.warning("Plugin hook failed %s/%s: %s", plugin.name, hook, exc)

