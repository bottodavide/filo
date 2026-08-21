# SPDX-License-Identifier: Apache-2.0
"""Breadth-first upstream traversal that assembles a Chain from the IR."""
from __future__ import annotations

from collections import deque

from filo.evidence import absent_license, build_evidence, utcnow
from filo.graph.model import collect_uplinks
from filo.hub.client import HFClient, RepoInfo
from filo.ids import canonical_id, dedup_key, is_valid_repo_id, namespace_name, parse_input_id
from filo.ir import (
    AccessStatus,
    Artifact,
    ArtifactKind,
    Chain,
    ExtractionMethod,
    LicenseAssertion,
    LicenseConfidence,
    Relation,
    TraversalParams,
    Warning,
)
from filo.parse.licenses import is_opaque, to_spdx


def _license_for(info: RepoInfo, api_url: str) -> LicenseAssertion:
    fm = info.card_data or {}
    raw = fm.get("license") if isinstance(fm.get("license"), str) else None
    name = fm.get("license_name") if isinstance(fm.get("license_name"), str) else None
    link = fm.get("license_link") if isinstance(fm.get("license_link"), str) else None
    if not raw:
        return absent_license(api_url, ["cardData.license", "frontmatter", "tags"])
    conf = LicenseConfidence.OPAQUE if is_opaque(raw, name, link) else LicenseConfidence.DECLARED
    ev = build_evidence(
        api_url, ExtractionMethod.CARD_FRONTMATTER, repo_sha=info.sha, text=f"license: {raw}"
    )
    return LicenseAssertion(
        raw_value=raw, spdx_id=to_spdx(raw), license_name=name,
        license_link=link, confidence=conf, evidence=ev,
    )


def walk(
    roots, client: HFClient, params: TraversalParams | None = None, *,
    generator: str = "filo/0.0.1",
) -> Chain:
    params = params or TraversalParams()
    artifacts: dict[str, Artifact] = {}
    relations: list[Relation] = []
    reasons: list[str] = []
    warnings: list[Warning] = []
    visited: set[str] = set()

    root_ids: list[str] = []
    queue: deque[tuple[ArtifactKind, str, int]] = deque()
    for raw in roots:
        kind, repo_id = parse_input_id(raw)
        root_ids.append(canonical_id(kind, repo_id))
        queue.append((kind, repo_id, 0))

    while queue:
        kind, repo_id, depth = queue.popleft()
        ns, name = namespace_name(repo_id)
        cid = canonical_id(kind, repo_id)
        if dedup_key(cid) in visited:
            continue
        visited.add(dedup_key(cid))

        if params.max_artifacts is not None and len(artifacts) >= params.max_artifacts:
            reasons.append(f"max_artifacts {params.max_artifacts} reached")
            break

        info = client.info(kind, repo_id)
        api_url = client._api_url(kind, repo_id)  # noqa: SLF001 (same package)
        readme = None
        if info.access is AccessStatus.PUBLIC and info.sha:
            readme = client.readme(kind, repo_id, info.sha)

        artifacts[cid] = Artifact(
            id=cid, kind=kind, platform="huggingface", namespace=ns, name=name,
            revision=info.sha, url=f"https://huggingface.co/{repo_id}",
            access=info.access, access_note=info.access_note,
            licenses=[_license_for(info, api_url)],
            downloads=info.downloads, retrieved_at=utcnow(), depth=depth,
            raw_tags=info.tags,
        )

        if depth >= params.max_depth:
            if info.access is AccessStatus.PUBLIC:
                reasons.append(f"max_depth {params.max_depth} reached at {cid}")
            continue

        for link in collect_uplinks(info, readme, no_body_scan=params.no_body_scan):
            # Fail closed: a malformed upstream reference is recorded as a
            # documented warning and skipped, never interpolated into a URL.
            if not is_valid_repo_id(link.repo_id):
                warnings.append(
                    Warning(
                        code="malformed_upstream_reference",
                        message=f"skipped malformed upstream reference {link.repo_id!r}",
                        artifact_id=cid,
                    )
                )
                continue
            tid = canonical_id(link.kind, link.repo_id)
            ev = build_evidence(api_url, link.method, repo_sha=info.sha, text=link.snippet)
            relations.append(
                Relation(source_id=cid, target_id=tid, kind=link.relation,
                         confidence=link.confidence, evidence=ev)
            )
            queue.append((link.kind, link.repo_id, depth + 1))

    truncated = bool(reasons)
    return Chain(
        roots=root_ids, artifacts=artifacts, relations=relations,
        generated_at=utcnow(), generator=generator,
        traversal=params.model_copy(
            update={"truncated": truncated, "truncation_reasons": reasons}
        ),
        warnings=warnings,
    )
