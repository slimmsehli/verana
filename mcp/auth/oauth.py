from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx


@dataclass
class OAuthToken:
    access_token: str
    expires_at: datetime

    def expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at


class OAuthClientCredentials:
    def __init__(self, token_url: str, client_id: str, client_secret: str, scopes: list[str]):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes
        self._token: OAuthToken | None = None

    async def get_access_token(self) -> str:
        if self._token and not self._token.expired():
            return self._token.access_token

        data = {"grant_type": "client_credentials"}
        if self.scopes:
            data["scope"] = " ".join(self.scopes)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.token_url,
                data=data,
                auth=(self.client_id, self.client_secret),
            )
            resp.raise_for_status()
            body = resp.json()
        token = body["access_token"]
        expires_in = int(body.get("expires_in", 3600))
        self._token = OAuthToken(
            access_token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=max(1, expires_in - 15)),
        )
        return token

