from __future__ import annotations

from pathlib import Path

import yaml


def detect_project_context(root_dir: Path) -> str:
    project_yaml = root_dir / "config" / "project.yaml"
    if project_yaml.exists():
        data = yaml.safe_load(project_yaml.read_text(encoding="utf-8")) or {}
        p = data.get("project", {})
        return (
            f"Project: {p.get('name','unknown')}\n"
            f"Top module: {p.get('top_module','unknown')}\n"
            f"Simulator: {p.get('simulator','unknown')}\n"
            f"RTL root: {p.get('rtl_root','./rtl')}\n"
            f"TB root: {p.get('tb_root','./tb')}"
        )

    top_module = _guess_top_module(root_dir)
    simulator = _guess_simulator(root_dir)
    return f"Top module: {top_module or 'unknown'}\nSimulator: {simulator or 'unknown'}"


def _guess_top_module(root_dir: Path) -> str | None:
    for ext in ("*.sv", "*.v"):
        for f in root_dir.rglob(ext):
            if "tb" in f.name.lower():
                continue
            return f.stem
    return None


def _guess_simulator(root_dir: Path) -> str | None:
    makefile = root_dir / "Makefile"
    if not makefile.exists():
        return None
    txt = makefile.read_text(encoding="utf-8", errors="ignore").lower()
    for sim in ("vcs", "questa", "xcelium", "verilator"):
        if sim in txt:
            return sim
    return None

