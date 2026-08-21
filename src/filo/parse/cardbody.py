# SPDX-License-Identifier: Apache-2.0
"""Scan a card body for huggingface.co links (inferred relations)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from filo.ir import ArtifactKind

_LINK = re.compile(r"https?://huggingface\.co/(datasets/)?([A-Za-z0-9][\w.-]*/[\w.-]+)")
_HEADING = re.compile(r"^#{1,6}\s+(.*)$")


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
            kind = ArtifactKind.DATASET if lm.group(1) else ArtifactKind.MODEL
            repo_id = lm.group(2).rstrip(".")
            key = (kind, repo_id)
            if key not in seen:
                seen[key] = LinkHit(kind, repo_id, heading, line.strip()[:200])
    return list(seen.values())
