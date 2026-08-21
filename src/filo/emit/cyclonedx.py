# SPDX-License-Identifier: Apache-2.0
"""CycloneDX 1.6 (default) / 1.7 exporter, built from the IR Chain.

Not built from API responses. Everything the standard cannot express goes under
the ``filo:`` property namespace (documented in PROPERTIES.md). ``evidence.identity``
is emitted as an array (the single-object form is deprecated since 1.6).
"""
from __future__ import annotations

from filo.emit.validate import spdx_ids
from filo.ir import Artifact, ArtifactKind, Chain, LicenseAssertion, LicenseConfidence

_TYPE = {
    ArtifactKind.MODEL: "machine-learning-model",
    ArtifactKind.DATASET: "data",
    ArtifactKind.CODE: "library",
    ArtifactKind.SERVICE: "application",
}
_CONFIDENCE = {
    LicenseConfidence.DECLARED: 1.0,
    LicenseConfidence.INFERRED: 0.5,
    LicenseConfidence.OPAQUE: 0.2,
    LicenseConfidence.ABSENT: 0.2,
}


def _prop(name: str, value: str) -> dict:
    return {"name": name, "value": value}


def _repo_id(a: Artifact) -> str:
    return f"{a.namespace}/{a.name}" if a.namespace else a.name


def _licenses_block(la: LicenseAssertion) -> list[dict] | None:
    """CycloneDX licenseChoice array for one assertion, or None for absence."""
    if la.confidence is LicenseConfidence.ABSENT:
        return None
    if la.spdx_id and la.spdx_id in spdx_ids():
        return [{"license": {"id": la.spdx_id}}]
    if la.raw_value:
        return [{"license": {"name": la.raw_value}}]
    return None


def _properties(a: Artifact, chain: Chain | None) -> list[dict]:
    props = [
        _prop("filo:access", a.access.value),
        _prop("filo:traversal-depth", str(a.depth)),
    ]
    la = a.licenses[0] if a.licenses else None
    if la is not None:
        props.append(_prop("filo:license-confidence", la.confidence.value))
        props.append(_prop("filo:evidence-method", la.evidence.method.value))
        props.append(_prop("filo:evidence-url", str(la.evidence.url)))
        if la.evidence.repo_sha:
            props.append(_prop("filo:evidence-sha", la.evidence.repo_sha))
        props.append(_prop("filo:evidence-retrieved-at", la.evidence.retrieved_at.isoformat()))
        if la.spdx_id:
            props.append(_prop("filo:spdx-id", la.spdx_id))
        if la.confidence is LicenseConfidence.ABSENT and la.evidence.searched_locations:
            props.append(_prop("filo:searched-locations", ",".join(la.evidence.searched_locations)))
    if chain is not None:
        for r in chain.relations:
            if r.source_id == a.id:
                props.append(_prop("filo:relation", f"{r.kind.value}:{r.confidence}:{r.target_id}"))
    return props


def _identity(a: Artifact) -> list[dict]:
    la = a.licenses[0] if a.licenses else None
    conf = _CONFIDENCE[la.confidence] if la is not None else 0.2
    value = str(la.evidence.url) if la is not None else a.id
    return [
        {
            "field": "name",
            "confidence": conf,
            "methods": [{"technique": "manifest-analysis", "confidence": conf, "value": value}],
        }
    ]


def ancestors_for(source_id: str, chain: Chain) -> list[dict]:
    """Minimal ancestor component stubs for pedigree, from the upstream relations."""
    out: list[dict] = []
    seen: set[str] = set()
    for r in chain.relations:
        if r.source_id != source_id or r.target_id in seen:
            continue
        seen.add(r.target_id)
        target = chain.artifacts.get(r.target_id)
        kind = target.kind if target is not None else ArtifactKind.MODEL
        name = _repo_id(target) if target is not None else r.target_id
        out.append({"bom-ref": r.target_id, "type": _TYPE[kind], "name": name})
    return out


def dependencies_of(chain: Chain) -> list[dict]:
    edges: dict[str, list[str]] = {}
    for r in chain.relations:
        edges.setdefault(r.source_id, [])
        if r.target_id not in edges[r.source_id]:
            edges[r.source_id].append(r.target_id)
    return [{"ref": ref, "dependsOn": deps} for ref, deps in edges.items()]


def component_of(a: Artifact, chain: Chain | None = None) -> dict:
    c: dict = {"type": _TYPE[a.kind], "bom-ref": a.id, "name": _repo_id(a)}
    if a.revision:
        c["version"] = a.revision
    la = a.licenses[0] if a.licenses else None
    lb = _licenses_block(la) if la is not None else None
    if lb is not None:
        c["licenses"] = lb
    evidence: dict = {"identity": _identity(a)}
    if lb is not None:
        evidence["licenses"] = lb
    c["evidence"] = evidence
    if a.kind is ArtifactKind.DATASET:
        c["data"] = [{"type": "dataset", "name": _repo_id(a)}]
    if chain is not None:
        ancestors = ancestors_for(a.id, chain)
        if ancestors:
            c["pedigree"] = {"ancestors": ancestors}
    c["properties"] = _properties(a, chain)
    return c


def to_cyclonedx(chain: Chain, spec_version: str = "1.6") -> dict:
    version = chain.generator.split("/")[-1] if "/" in chain.generator else chain.generator
    meta_props = [
        _prop("filo:generator", chain.generator),
        _prop("filo:truncated", "true" if chain.traversal.truncated else "false"),
    ]
    for reason in chain.traversal.truncation_reasons:
        meta_props.append(_prop("filo:truncation-reason", reason))
    return {
        "bomFormat": "CycloneDX",
        "specVersion": spec_version,
        "version": 1,
        "metadata": {
            "timestamp": chain.generated_at.isoformat(),
            "tools": {"components": [{"type": "application", "name": "filo", "version": version}]},
            "properties": meta_props,
        },
        "components": [component_of(a, chain) for a in chain.artifacts.values()],
        "dependencies": dependencies_of(chain),
    }
