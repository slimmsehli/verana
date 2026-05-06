from __future__ import annotations


def apply_api_key(
    headers: dict[str, str],
    params: dict[str, str],
    value: str | None,
    header: str | None = None,
    query_param: str | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    if not value:
        return headers, params
    if query_param:
        params[query_param] = value
    else:
        headers[header or "X-API-Key"] = value
    return headers, params

