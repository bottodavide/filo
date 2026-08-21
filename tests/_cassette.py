# SPDX-License-Identifier: Apache-2.0
"""Cassette replay fetcher for tests. No test makes a real network call."""
from __future__ import annotations

import json
from pathlib import Path

from filo.hub.fetch import Response


class CassetteFetcher:
    def __init__(self, root):
        self.root = Path(root)
        self.index = json.loads((self.root / "index.json").read_text())

    def get(self, url: str, *, token: str | None = None) -> Response:
        entry = self.index.get(url)
        assert entry is not None, f"unrecorded URL in test: {url}"
        raw = (self.root / entry["file"]).read_text()
        body = None
        if entry["file"].endswith(".json"):
            body = json.loads(raw)
        return Response(status=entry.get("status", 200), text=raw, json_body=body)
