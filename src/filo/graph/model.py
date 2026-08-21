# SPDX-License-Identifier: Apache-2.0
"""Collect upstream links for an artifact from all sources, in priority order."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from filo.ids import is_valid_repo_id
from filo.ir import ArtifactKind, ExtractionMethod, RelationKind
from filo.parse import cardbody, frontmatter

_BASE_TAG = re.compile(r"^base_model:([\w.-]+):([A-Za-z0-9][\w.-]*/[\w.-]+)$")
_REL = {
    "finetune": RelationKind.FINETUNED_FROM,
    "adapter": RelationKind.ADAPTER_OF,
    "quantized": RelationKind.QUANTIZED_FROM,
    "merge": RelationKind.MERGED_FROM,
}


def relation_from_base(relation: str | None) -> RelationKind:
    if relation is None:
        return RelationKind.DERIVED_FROM
    return _REL.get(relation.strip().lower(), RelationKind.DERIVED_FROM)


@dataclass
class UpLink:
    repo_id: str
    kind: ArtifactKind
    relation: RelationKind
    confidence: Literal["declared", "inferred"]
    method: ExtractionMethod
    snippet: str | None = None


def collect_uplinks(info, readme: str | None, *, no_body_scan: bool) -> list[UpLink]:
    out: dict[tuple[ArtifactKind, str], UpLink] = {}

    def add(link: UpLink) -> None:
        # Single choke point: never accept a repo_id that could reach URL
        # construction unvalidated (auto-tags and card-body links included).
        if not is_valid_repo_id(link.repo_id):
            return
        key = (link.kind, link.repo_id)
        prev = out.get(key)
        if prev is None or (prev.confidence == "inferred" and link.confidence == "declared"):
            out[key] = link

    fm = info.card_data or {}
    for repo_id, rel in frontmatter.base_models(fm):
        add(UpLink(repo_id, ArtifactKind.MODEL, relation_from_base(rel),
                   "declared", ExtractionMethod.CARD_FRONTMATTER))
    for ds in frontmatter.datasets(fm):
        add(UpLink(ds, ArtifactKind.DATASET, RelationKind.TRAINED_ON,
                   "declared", ExtractionMethod.CARD_FRONTMATTER))
    for tag in info.tags:
        m = _BASE_TAG.match(tag)
        if m:
            add(UpLink(m.group(2), ArtifactKind.MODEL, relation_from_base(m.group(1)),
                       "declared", ExtractionMethod.HF_AUTO_TAG, snippet=tag))
    if readme and not no_body_scan:
        for hit in cardbody.find_hf_links(readme):
            rel = (
                RelationKind.TRAINED_ON
                if hit.kind is ArtifactKind.DATASET
                else RelationKind.DERIVED_FROM
            )
            add(UpLink(hit.repo_id, hit.kind, rel, "inferred",
                       ExtractionMethod.CARD_BODY_LINK, snippet=hit.snippet))
    return list(out.values())
