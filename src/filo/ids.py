# SPDX-License-Identifier: Apache-2.0
"""Parse input artifact ids and build stable canonical ids."""
from __future__ import annotations

from filo.ir import ArtifactKind

_KIND_PREFIX = {
    "model": ArtifactKind.MODEL,
    "dataset": ArtifactKind.DATASET,
    "datasets": ArtifactKind.DATASET,
}


def parse_input_id(raw: str) -> tuple[ArtifactKind, str, str]:
    """Parse ``owner/name``, ``model:owner/name`` or ``datasets/owner/name``."""
    kind = ArtifactKind.MODEL
    rest = raw.strip()
    if ":" in rest:
        prefix, rest = rest.split(":", 1)
        if prefix not in _KIND_PREFIX:
            raise ValueError(f"unknown id prefix: {prefix!r}")
        kind = _KIND_PREFIX[prefix]
    elif rest.startswith("datasets/"):
        kind, rest = ArtifactKind.DATASET, rest[len("datasets/") :]
    if rest.count("/") != 1 or rest.startswith("/") or rest.endswith("/"):
        raise ValueError(f"expected owner/name, got {raw!r}")
    namespace, name = rest.split("/", 1)
    return kind, namespace, name


def canonical_id(
    kind: ArtifactKind, namespace: str, name: str, platform: str = "huggingface"
) -> str:
    """Build a stable canonical id, e.g. ``hf:model:owner/name``."""
    tag = "hf" if platform == "huggingface" else platform
    return f"{tag}:{kind.value}:{namespace}/{name}"


def dedup_key(canonical: str) -> str:
    """Lowercased canonical id, used to deduplicate artifacts."""
    return canonical.lower()


def repo_id_of(canonical: str) -> str:
    """Extract ``owner/name`` from a canonical id."""
    return canonical.split(":", 2)[2]
