# SPDX-License-Identifier: Apache-2.0
"""Content-addressed on-disk cache keyed by (repo_type, repo_id, sha, path).

Once a repo's commit sha is known, that content is immutable, so entries never
expire. Only repo_id -> current sha resolution is volatile (not cached here).
"""
from __future__ import annotations

import hashlib
from pathlib import Path


class Cache:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _slot(self, repo_type: str, repo_id: str, sha: str, path: str) -> Path:
        key = f"{repo_type}\0{repo_id}\0{sha}\0{path}".encode()
        h = hashlib.sha256(key).hexdigest()
        return self.root / h[:2] / h[2:]

    def get(self, repo_type: str, repo_id: str, sha: str, path: str) -> bytes | None:
        slot = self._slot(repo_type, repo_id, sha, path)
        return slot.read_bytes() if slot.exists() else None

    def put(self, repo_type: str, repo_id: str, sha: str, path: str, data: bytes) -> None:
        slot = self._slot(repo_type, repo_id, sha, path)
        slot.parent.mkdir(parents=True, exist_ok=True)
        slot.write_bytes(data)
