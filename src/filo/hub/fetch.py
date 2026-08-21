# SPDX-License-Identifier: Apache-2.0
"""Fetcher abstraction isolating all HTTP so tests can replay cassettes."""
from __future__ import annotations

import json as _json
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Response:
    status: int
    text: str | None = None
    json_body: dict | list | None = None


class Fetcher(Protocol):
    def get(self, url: str, *, token: str | None = None) -> Response: ...


class HttpxFetcher:
    """Real network fetcher. Not used in tests."""

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    def get(self, url: str, *, token: str | None = None) -> Response:
        import httpx

        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            r = httpx.get(
                url, headers=headers, timeout=self._timeout, follow_redirects=True
            )
        except httpx.TimeoutException:
            return Response(status=599, text="timeout")
        body: dict | list | None = None
        if "application/json" in r.headers.get("content-type", ""):
            try:
                body = r.json()
            except _json.JSONDecodeError:
                body = None
        return Response(status=r.status_code, text=r.text, json_body=body)
