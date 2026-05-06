from __future__ import annotations

import logging
from typing import Any

from config_models import MCPServerConfig
from mcp.base import MCPClient
from mcp.http_client import HTTPMCPClient
from mcp.stdio_client import StdioMCPClient

logger = logging.getLogger(__name__)


class MCPRegistry:
    def __init__(self):
        self.clients: dict[str, MCPClient] = {}
        self._tools: list[dict[str, Any]] = []

    async def connect_servers(self, servers: list[MCPServerConfig]) -> None:
        self.clients.clear()
        self._tools.clear()
        for server in servers:
            if not server.enabled:
                continue
            client: MCPClient
            if server.transport == "stdio":
                client = StdioMCPClient(server)
            else:
                client = HTTPMCPClient(server)
            try:
                await client.connect()
                self.clients[server.name] = client
                tools = await client.list_tools()
                for tool in tools:
                    namespaced = self._namespace_tool(server.name, tool)
                    self._tools.append(namespaced)
            except Exception as exc:
                logger.warning("Failed to connect MCP server %s: %s", server.name, exc)

    @staticmethod
    def _namespace_tool(server_name: str, tool: dict[str, Any]) -> dict[str, Any]:
        name = tool.get("name", "")
        full_name = f"{server_name}__{name}"
        return {
            "type": "function",
            "function": {
                "name": full_name,
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", tool.get("parameters", {"type": "object"})),
            },
        }

    def unified_tools(self) -> list[dict[str, Any]]:
        dedup: dict[str, dict[str, Any]] = {}
        for t in self._tools:
            dedup[t["function"]["name"]] = t
        return list(dedup.values())

    async def disconnect_all(self) -> None:
        for client in self.clients.values():
            try:
                await client.disconnect()
            except Exception:
                pass

