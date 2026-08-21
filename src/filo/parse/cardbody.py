# SPDX-License-Identifier: Apache-2.0
"""Scan a card body for huggingface.co links (inferred relations)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from filo.ir import ArtifactKind

_SEG = r"[A-Za-z0-9][\w.-]*"
# A dataset link may be a single canonical name (datasets/code_search_net) or
# owner/name; a model link from prose must be owner/name (a single bare name is
# too noisy — huggingface.co/docs, /blog, org pages).
_LINK = re.compile(rf"https?://huggingface\.co/(datasets/)?({_SEG}(?:/{_SEG})?)")
_HEADING = re.compile(r"^#{1,6}\s+(.*)$")

# Leading path segments on huggingface.co that are NOT repositories: site
# routes, assets, and app pages. A prose link whose first segment is one of
# these is not a dependency (observed phantoms on all-MiniLM-L6-v2:
# front/thumbnails, metrics/rouge, datasets/viewer). Reserved words are matched
# on the segment that follows an optional `datasets/` prefix.
# NOTE: this is a correctness/noise filter, NOT a security boundary. Every link
# that survives it is still re-validated by ids.is_valid_repo_id before any URL
# is built (graph/model.py, graph/walker.py). Do not repurpose it as a trust
# decision.
_RESERVED = frozenset({
    "api", "blog", "brand", "chat", "collections", "datasets", "docs",
    "enterprise", "front", "huggingface", "join", "learn", "login", "logout",
    "metrics", "models", "new", "notifications", "organizations", "papers",
    "posts", "pricing", "privacy", "search", "settings", "spaces", "support",
    "tasks", "terms", "viewer",
})


@dataclass
class LinkHit:
    kind: ArtifactKind
    repo_id: str
    heading: str | None
    snippet: str


def find_hf_links(body: str) -> list[LinkHit]:
    heading: str | None = None
    seen: dict[tuple[ArtifactKind, str], LinkHit] = {}
    for line in body.splitlines():
        m = _HEADING.match(line.strip())
        if m:
            heading = m.group(1).strip()
            continue
        for lm in _LINK.finditer(line):
            repo_id = lm.group(2).rstrip(".")
            if repo_id.split("/", 1)[0].lower() in _RESERVED:
                continue  # site route / asset / app page, not a repository
            if lm.group(1):
                kind = ArtifactKind.DATASET
            else:
                kind = ArtifactKind.MODEL
                if "/" not in repo_id:
                    continue  # bare single-name model link: too noisy
            key = (kind, repo_id)
            if key not in seen:
                seen[key] = LinkHit(kind, repo_id, heading, line.strip()[:200])
    return list(seen.values())
