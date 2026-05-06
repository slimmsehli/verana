from __future__ import annotations

import logging
from typing import Any

import httpx

from config_models import MCPAuthConfig, MCPServerConfig
from mcp.auth.api_key import apply_api_key
from mcp.auth.bearer import apply_bearer
from mcp.auth.oauth import OAuthClientCredentials
from mcp.base import MCPClient

logger = logging.getLogger(__name__)


class HTTPMCPClient(MCPClient):
    def __init__(self, conf: MCPServerConfig):
        self.name = conf.name
        self.description = conf.description
        self.url = conf.url or ""
        self.auth = conf.auth
        self._client = httpx.AsyncClient(timeout=60)
        self._oauth: OAuthClientCredentials | None = None
        if self.auth and self.auth.type == "oauth":
            self._oauth = OAuthClientCredentials(
                token_url=self.auth.token_url or "",
                client_id=self.auth.client_id or "",
                client_secret=self.auth.client_secret or "",
                scopes=self.auth.scopes or [],
            )

    async def connect(self) -> None:
        if self._oauth:
            await self._oauth.get_access_token()

    async def disconnect(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        params: dict[str, str] = {}
        auth: MCPAuthConfig | None = self.auth
        if auth:
            if auth.type == "bearer":
                apply_bearer(headers, auth.token)
            elif auth.type == "api_key":
                headers, params = apply_api_key(headers, params, auth.value, auth.header, auth.query_param)
            elif auth.type == "oauth":
                if not self._oauth:
                    raise RuntimeError("OAuth configuration missing")
                token = await self._oauth.get_access_token()
                apply_bearer(headers, token)
        body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": payload}
        response = await self._client.post(self.url, json=body, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise RuntimeError(f"MCP error: {data['error']}")
        return data.get("result", {})

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self._request("tools/list", {})
        return result.get("tools", [])

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self._request("tools/call", {"name": tool_name, "arguments": arguments})

    async def health_check(self) -> bool:
        try:
            await self._request("health", {})
            return True
        except Exception:
            return False

