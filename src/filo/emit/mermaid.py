# SPDX-License-Identifier: Apache-2.0
"""Mermaid diagram of the chain; broken links are visible at a glance."""
from __future__ import annotations

from filo.ir import AccessStatus, Chain, LicenseConfidence


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
    # keep the label a single, quote-free line
    return f"{name}{suffix}".replace('"', "'").replace("\n", " ").replace("|", "/")


def to_mermaid(chain: Chain) -> str:
    # Deterministic, collision-free node ids: index by first appearance. Using a
    # sanitised canonical id could collapse distinct ids (acme/a.b vs acme/a-b).
    order: list[str] = list(chain.artifacts)
    for r in chain.relations:  # include any dangling relation endpoints
        for cid in (r.source_id, r.target_id):
            if cid not in order:
                order.append(cid)
    node_id = {cid: f"n{i}" for i, cid in enumerate(order)}

    lines = ["graph TD"]
    for cid in order:
        a = chain.artifacts.get(cid)
        label = _label(a) if a is not None else cid.replace('"', "'")
        lines.append(f'    {node_id[cid]}["{label}"]')
    for r in chain.relations:
        lines.append(
            f"    {node_id[r.source_id]} -->|{r.kind.value}| {node_id[r.target_id]}"
        )
    return "\n".join(lines)
