#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


TOOLS = [
    {
        "name": "list_signals",
        "description": "List signal identifiers and names from a VCD",
        "input_schema": {
            "type": "object",
            "properties": {"vcd_file": {"type": "string"}},
            "required": ["vcd_file"],
        },
    },
    {
        "name": "query_signal",
        "description": "Get value changes for a signal in a VCD file",
        "input_schema": {
            "type": "object",
            "properties": {
                "vcd_file": {"type": "string"},
                "signal": {"type": "string"},
                "max_events": {"type": "integer"},
            },
            "required": ["vcd_file", "signal"],
        },
    },
    {
        "name": "detect_xprop",
        "description": "Detect x/z values seen on a signal",
        "input_schema": {
            "type": "object",
            "properties": {
                "vcd_file": {"type": "string"},
                "signal": {"type": "string"},
            },
            "required": ["vcd_file", "signal"],
        },
    },
]


def _read_lines(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return p.read_text(encoding="utf-8", errors="ignore").splitlines()


def _parse_defs(lines: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    id_to_name: dict[str, str] = {}
    name_to_id: dict[str, str] = {}
    for line in lines:
        if line.startswith("$var"):
            parts = line.split()
            if len(parts) >= 5:
                ident = parts[3]
                name = parts[4]
                id_to_name[ident] = name
                name_to_id[name] = ident
        if line.startswith("$enddefinitions"):
            break
    return id_to_name, name_to_id


def _parse_changes(lines: list[str], target_id: str, max_events: int = 200) -> list[dict[str, Any]]:
    t = 0
    out = []
    vec_re = re.compile(r"^b([01xXzZ]+)\s+(.+)$")
    for line in lines:
        if line.startswith("#"):
            try:
                t = int(line[1:])
            except ValueError:
                continue
        elif line:
            m = vec_re.match(line)
            if m:
                val, ident = m.group(1), m.group(2)
                if ident == target_id:
                    out.append({"time": t, "value": val})
            else:
                val = line[0]
                ident = line[1:]
                if ident == target_id:
                    out.append({"time": t, "value": val})
        if len(out) >= max_events:
            break
    return out


def list_signals(args: dict[str, Any]) -> dict[str, Any]:
    lines = _read_lines(args["vcd_file"])
    id_to_name, _ = _parse_defs(lines)
    return {"signals": [{"id": i, "name": n} for i, n in sorted(id_to_name.items())]}


def query_signal(args: dict[str, Any]) -> dict[str, Any]:
    lines = _read_lines(args["vcd_file"])
    _, name_to_id = _parse_defs(lines)
    sig = args["signal"]
    ident = name_to_id.get(sig)
    if not ident:
        return {"error": f"signal not found: {sig}"}
    events = _parse_changes(lines, ident, int(args.get("max_events", 200)))
    return {"signal": sig, "events": events}


def detect_xprop(args: dict[str, Any]) -> dict[str, Any]:
    q = query_signal({"vcd_file": args["vcd_file"], "signal": args["signal"], "max_events": 20000})
    if "error" in q:
        return q
    bad = [e for e in q["events"] if any(ch in str(e["value"]).lower() for ch in ["x", "z"])]
    return {"signal": args["signal"], "x_or_z_events": bad, "count": len(bad)}


def handle_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "list_signals":
        return list_signals(args)
    if name == "query_signal":
        return query_signal(args)
    if name == "detect_xprop":
        return detect_xprop(args)
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

