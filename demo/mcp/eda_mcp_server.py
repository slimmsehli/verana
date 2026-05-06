#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


TOOLS = [
    {
        "name": "verilator_lint",
        "description": "Run verilator lint-only on a source set",
        "input_schema": {
            "type": "object",
            "properties": {
                "sources": {"type": "array", "items": {"type": "string"}},
                "top": {"type": "string"},
            },
            "required": ["sources"],
        },
    },
    {
        "name": "verilator_build",
        "description": "Compile and build simulation binary with verilator",
        "input_schema": {
            "type": "object",
            "properties": {
                "sources": {"type": "array", "items": {"type": "string"}},
                "top": {"type": "string"},
                "binary": {"type": "string"},
            },
            "required": ["sources", "top"],
        },
    },
    {
        "name": "run_binary",
        "description": "Run a produced simulation binary",
        "input_schema": {
            "type": "object",
            "properties": {"binary": {"type": "string"}},
            "required": ["binary"],
        },
    },
    {
        "name": "yosys_synth",
        "description": "Run basic yosys synthesis checks",
        "input_schema": {
            "type": "object",
            "properties": {
                "sources": {"type": "array", "items": {"type": "string"}},
                "top": {"type": "string"},
            },
            "required": ["sources", "top"],
        },
    },
]


def _run(cmd: list[str], cwd: str | None = None) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-8000:],
    }


def verilator_lint(args: dict[str, Any]) -> dict[str, Any]:
    src = args.get("sources", [])
    top = args.get("top")
    cmd = ["verilator", "--lint-only", "-Wall"]
    if top:
        cmd += ["--top-module", top]
    cmd += src
    return _run(cmd)


def verilator_build(args: dict[str, Any]) -> dict[str, Any]:
    src = args.get("sources", [])
    top = args.get("top")
    binary = args.get("binary", "simv_demo")
    cmd = ["verilator", "-Wall", "--binary", "-o", binary]
    if top:
        cmd += ["--top-module", top]
    cmd += src
    return _run(cmd)


def run_binary(args: dict[str, Any]) -> dict[str, Any]:
    bin_path = Path(args.get("binary", "simv_demo"))
    if not bin_path.exists():
        return {"error": f"binary not found: {bin_path}"}
    return _run([str(bin_path.resolve())])


def yosys_synth(args: dict[str, Any]) -> dict[str, Any]:
    src = args.get("sources", [])
    top = args.get("top")
    script = " ".join([f"read_verilog {x};" for x in src])
    script += f" hierarchy -check -top {top}; proc; opt; stat;"
    cmd = ["yosys", "-p", script]
    return _run(cmd)


def handle_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "verilator_lint":
        return verilator_lint(args)
    if name == "verilator_build":
        return verilator_build(args)
    if name == "run_binary":
        return run_binary(args)
    if name == "yosys_synth":
        return yosys_synth(args)
    return {"error": f"unknown tool: {name}"}


def make_response(req_id: Any, result: dict[str, Any] | None = None, error: str | None = None) -> dict[str, Any]:
    if error is not None:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": error}}
    return {"jsonrpc": "2.0", "id": req_id, "result": result or {}}


def main() -> None:
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            method = req.get("method")
            req_id = req.get("id")
            params = req.get("params", {})
            if method == "health":
                resp = make_response(req_id, {"ok": True})
            elif method == "tools/list":
                resp = make_response(req_id, {"tools": TOOLS})
            elif method == "tools/call":
                tname = params.get("name", "")
                targs = params.get("arguments", {})
                resp = make_response(req_id, handle_call(tname, targs))
            else:
                resp = make_response(req_id, error=f"unknown method: {method}")
        except Exception as exc:
            resp = make_response(None, error=str(exc))
        print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    main()

