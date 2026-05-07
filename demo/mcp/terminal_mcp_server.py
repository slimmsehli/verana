#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


TOOLS = [
    {
        "name": "run_command",
        "description": "Run a Linux shell command in a restricted workspace root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string"},
                "timeout_sec": {"type": "integer", "minimum": 1, "maximum": 300},
            },
            "required": ["command"],
        },
    }
]


def _workspace_root() -> Path:
    env_root = os.environ.get("TERMINAL_MCP_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd().resolve()


def _resolve_cwd(raw_cwd: str | None) -> Path:
    root = _workspace_root()
    if not raw_cwd:
        return root
    candidate = Path(raw_cwd)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    resolved.relative_to(root)
    return resolved


def run_command(args: dict[str, Any]) -> dict[str, Any]:
    command = str(args.get("command", "")).strip()
    if not command:
        return {"error": "command is required"}
    timeout_sec = int(args.get("timeout_sec", 60))
    if timeout_sec < 1:
        timeout_sec = 1
    if timeout_sec > 300:
        timeout_sec = 300
    try:
        cwd = _resolve_cwd(args.get("cwd"))
    except Exception:
        return {"error": "cwd must stay inside TERMINAL_MCP_ROOT"}
    try:
        proc = subprocess.run(
            ["/bin/bash", "-lc", command],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "error": f"command timed out after {timeout_sec}s",
            "stdout": (exc.stdout or "")[-8000:],
            "stderr": (exc.stderr or "")[-8000:],
        }
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "cwd": str(cwd),
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-8000:],
    }


def handle_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "run_command":
        return run_command(args)
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
