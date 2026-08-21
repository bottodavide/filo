# SPDX-License-Identifier: Apache-2.0
"""Parse input artifact ids and build stable canonical ids.

``is_valid_repo_id`` is the single choke point that keeps untrusted values
(``base_model``/``datasets`` from third-party cards, card-body links, tags)
from reaching URL construction. Anything that fails it is treated as a
malformed reference and skipped — never interpolated into a request URL.

A repo id is either ``owner/name`` or a single canonical ``name`` (legacy HF
datasets/models such as ``code_search_net`` or ``bert-base-uncased``). Both
segments are constrained to safe characters and anchored with ``\\A..\\Z`` (not
``^..$``: ``$`` also matches before a trailing newline, which would let
``owner/name\\n`` through and crash URL construction downstream).
"""
from __future__ import annotations

import re

from filo.ir import ArtifactKind

_KIND_PREFIX = {
    "model": ArtifactKind.MODEL,
    "dataset": ArtifactKind.DATASET,
    "datasets": ArtifactKind.DATASET,
}

# each segment starts alphanumeric (blocks leading '.', so '.'/'..' segments
# and dotfiles are rejected) and contains only word chars, '.', '-'.
_SEG = r"[A-Za-z0-9][\w.-]*"
_REPO_ID = re.compile(rf"\A{_SEG}(?:/{_SEG})?\Z")


def is_valid_repo_id(repo_id: str) -> bool:
    """True only for a safe ``owner/name`` pair or a single canonical ``name``
    (no '.'/'..' segment, no traversal, no control chars, no host/scheme)."""
    if not _REPO_ID.match(repo_id):
        return False
    return all(seg not in (".", "..") for seg in repo_id.split("/"))


def parse_input_id(raw: str) -> tuple[ArtifactKind, str]:
    """Parse ``owner/name``, ``name``, ``model:owner/name`` or
    ``datasets/owner/name`` into ``(kind, repo_id)``."""
    kind = ArtifactKind.MODEL
    rest = raw.strip()
    if ":" in rest:
        prefix, rest = rest.split(":", 1)
        if prefix not in _KIND_PREFIX:
            raise ValueError(f"unknown id prefix: {prefix!r}")
        kind = _KIND_PREFIX[prefix]
    elif rest.startswith("datasets/"):
        kind, rest = ArtifactKind.DATASET, rest[len("datasets/") :]
    if not is_valid_repo_id(rest):
        raise ValueError(f"expected a safe owner/name or name, got {raw!r}")
    return kind, rest


def canonical_id(kind: ArtifactKind, repo_id: str, platform: str = "huggingface") -> str:
    """Build a stable canonical id, e.g. ``hf:model:owner/name`` or
    ``hf:dataset:code_search_net``."""
    tag = "hf" if platform == "huggingface" else platform
    return f"{tag}:{kind.value}:{repo_id}"


def dedup_key(canonical: str) -> str:
    """Lowercased canonical id, used to deduplicate artifacts."""
    return canonical.lower()


def repo_id_of(canonical: str) -> str:
    """Extract the repo id (``owner/name`` or ``name``) from a canonical id."""
    return canonical.split(":", 2)[2]


def namespace_name(repo_id: str) -> tuple[str | None, str]:
    """Split a repo id into ``(namespace, name)``; namespace is None for a
    single canonical name."""
    if "/" in repo_id:
        ns, name = repo_id.split("/", 1)
        return ns, name
    return None, repo_id
