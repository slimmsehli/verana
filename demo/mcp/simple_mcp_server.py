#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TOOLS = [
    {
        "name": "list_dir",
        "description": "List files in a directory",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "read_text",
        "description": "Read a UTF-8 text file",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_text",
        "description": "Write a UTF-8 text file",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
]


def handle_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "list_dir":
        p = Path(args["path"])
        if not p.exists():
            return {"error": f"path not found: {p}"}
        return {"entries": [x.name for x in sorted(p.iterdir())]}
    if name == "read_text":
        p = Path(args["path"])
        if not p.exists():
            return {"error": f"file not found: {p}"}
        return {"content": p.read_text(encoding="utf-8", errors="ignore")}
    if name == "write_text":
        p = Path(args["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(args["content"], encoding="utf-8")
        return {"ok": True, "path": str(p)}
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

