from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from config_models import MCPServerConfig
from mcp.base import MCPClient


class StdioMCPClient(MCPClient):
    def __init__(self, conf: MCPServerConfig):
        self.name = conf.name
        self.description = conf.description
        self.command = conf.command or ""
        self.args = conf.args
        self.env = conf.env
        self._proc: asyncio.subprocess.Process | None = None
        self._id = 0

    async def connect(self) -> None:
        self._proc = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **self.env},
        )

    async def disconnect(self) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            await self._proc.wait()

    async def _rpc(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self._proc or not self._proc.stdin or not self._proc.stdout:
            raise RuntimeError("stdio MCP client is not connected")
        self._id += 1
        req = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        self._proc.stdin.write((json.dumps(req) + "\n").encode("utf-8"))
        await self._proc.stdin.drain()
        line = await self._proc.stdout.readline()
        if not line:
            raise RuntimeError("No response from MCP stdio server")
        resp = json.loads(line.decode("utf-8"))
        if "error" in resp:
            raise RuntimeError(str(resp["error"]))
        return resp.get("result", {})

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self._rpc("tools/list", {})
        return result.get("tools", [])

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self._rpc("tools/call", {"name": tool_name, "arguments": arguments})

    async def health_check(self) -> bool:
        try:
            await self._rpc("health", {})
            return True
        except Exception:
            return False

