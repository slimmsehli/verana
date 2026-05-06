from __future__ import annotations

from typing import Any

from mcp.registry import MCPRegistry


class ToolDispatcher:
    def __init__(self, registry: MCPRegistry):
        self.registry = registry

    async def dispatch(self, namespaced_tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if "__" not in namespaced_tool_name:
            raise ValueError(f"Tool name must be namespaced: {namespaced_tool_name}")
        server_name, tool_name = namespaced_tool_name.split("__", 1)
        client = self.registry.clients.get(server_name)
        if not client:
            raise ValueError(f"No MCP server available for tool: {namespaced_tool_name}")
        return await client.call_tool(tool_name, arguments)

