# SPDX-License-Identifier: Apache-2.0
"""Mermaid diagram of the chain; broken links are visible at a glance."""
from __future__ import annotations

import re

from filo.ir import AccessStatus, Chain, LicenseConfidence

_SAFE = re.compile(r"[^A-Za-z0-9]")


def _node_id(canonical: str) -> str:
    return "n_" + _SAFE.sub("_", canonical)


def _label(a) -> str:
    name = f"{a.namespace}/{a.name}" if a.namespace else a.name
    marks = []
    if any(lic.confidence is LicenseConfidence.ABSENT for lic in a.licenses):
        marks.append("no-licence")
    if any(lic.confidence is LicenseConfidence.OPAQUE for lic in a.licenses):
        marks.append("opaque")
    if a.access is not AccessStatus.PUBLIC:
        marks.append(a.access.value)
    suffix = f" [{', '.join(marks)}]" if marks else ""
    return f"{name}{suffix}".replace('"', "'")


def to_mermaid(chain: Chain) -> str:
    lines = ["graph TD"]
    for a in chain.artifacts.values():
        lines.append(f'    {_node_id(a.id)}["{_label(a)}"]')
    for r in chain.relations:
        lines.append(
            f"    {_node_id(r.source_id)} -->|{r.kind.value}| {_node_id(r.target_id)}"
        )
    return "\n".join(lines)
