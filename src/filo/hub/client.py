# SPDX-License-Identifier: Apache-2.0
"""Hugging Face client: repo info + raw README/config, with anomalous-state
mapping. Reads metadata and text files only — never model weights.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from filo.hub.cache import Cache
from filo.hub.fetch import Fetcher
from filo.ir import AccessStatus, ArtifactKind

_API = {ArtifactKind.MODEL: "models", ArtifactKind.DATASET: "datasets"}
_RAW_PREFIX = {ArtifactKind.MODEL: "", ArtifactKind.DATASET: "datasets/"}
_CACHE_TYPE = {ArtifactKind.MODEL: "model", ArtifactKind.DATASET: "dataset"}


@dataclass
class RepoInfo:
    repo_id: str
    kind: ArtifactKind
    access: AccessStatus
    sha: str | None = None
    card_data: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    last_modified: datetime | None = None
    downloads: int | None = None
    access_note: str | None = None


class HFClient:
    def __init__(
        self, fetcher: Fetcher, cache: Cache | None = None, token: str | None = None
    ) -> None:
        self._f = fetcher
        self._cache = cache
        self._token = token

    def _api_url(self, kind: ArtifactKind, repo_id: str) -> str:
        return f"https://huggingface.co/api/{_API[kind]}/{repo_id}"

    def _raw_url(self, kind: ArtifactKind, repo_id: str, sha: str, path: str) -> str:
        return f"https://huggingface.co/{_RAW_PREFIX[kind]}{repo_id}/resolve/{sha}/{path}"

    def info(self, kind: ArtifactKind, repo_id: str) -> RepoInfo:
        r = self._f.get(self._api_url(kind, repo_id), token=self._token)
        if r.status in (401, 403):
            return RepoInfo(
                repo_id, kind, AccessStatus.GATED,
                access_note="access requires accepting terms",
            )
        if r.status == 404:
            return RepoInfo(
                repo_id, kind, AccessStatus.NOT_FOUND,
                access_note="artifact not found or removed",
            )
        if r.status != 200 or not isinstance(r.json_body, dict):
            return RepoInfo(
                repo_id, kind, AccessStatus.ERROR,
                access_note=f"unexpected status {r.status}",
            )
        body = r.json_body
        gated = body.get("gated")
        access = AccessStatus.GATED if gated else AccessStatus.PUBLIC
        return RepoInfo(
            repo_id, kind, access,
            sha=body.get("sha"),
            card_data=body.get("cardData") or {},
            tags=body.get("tags") or [],
            downloads=body.get("downloads"),
        )

    def file(self, kind: ArtifactKind, repo_id: str, sha: str, path: str) -> bytes | None:
        ctype = _CACHE_TYPE[kind]
        if self._cache is not None:
            hit = self._cache.get(ctype, repo_id, sha, path)
            if hit is not None:
                return hit
        r = self._f.get(self._raw_url(kind, repo_id, sha, path), token=self._token)
        if r.status != 200 or r.text is None:
            return None
        data = r.text.encode("utf-8")
        if self._cache is not None:
            self._cache.put(ctype, repo_id, sha, path, data)
        return data

    def readme(self, kind: ArtifactKind, repo_id: str, sha: str) -> str | None:
        data = self.file(kind, repo_id, sha, "README.md")
        return data.decode("utf-8") if data is not None else None
