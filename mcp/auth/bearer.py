from __future__ import annotations


def apply_bearer(headers: dict[str, str], token: str | None) -> dict[str, str]:
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

