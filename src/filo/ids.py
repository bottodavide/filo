# SPDX-License-Identifier: Apache-2.0
"""Parse input artifact ids and build stable canonical ids.

``is_valid_repo_id`` is the single choke point that keeps untrusted values
(``base_model``/``datasets`` from third-party cards, card-body links, tags)
from reaching URL construction. Anything that fails it is treated as a
malformed reference and skipped — never interpolated into a request URL.
"""
from __future__ import annotations

import re

from filo.ir import ArtifactKind

_KIND_PREFIX = {
    "model": ArtifactKind.MODEL,
    "dataset": ArtifactKind.DATASET,
    "datasets": ArtifactKind.DATASET,
}

# owner/name: each side starts alphanumeric (blocks leading '.', so '.'/'..'
# segments and dotfiles are rejected) and contains only word chars, '.', '-'.
# \A..\Z (not ^..$): in Python $ also matches just before a trailing newline,
# which would let "owner/name\n" through and crash URL construction downstream.
_REPO_ID = re.compile(r"\A[A-Za-z0-9][\w.-]*/[A-Za-z0-9][\w.-]*\Z")


def is_valid_repo_id(repo_id: str) -> bool:
    """True only for a safe single ``owner/name`` pair (no '.'/'..' segment,
    no path traversal, no control chars, no host/scheme)."""
    if not _REPO_ID.match(repo_id):
        return False
    ns, name = repo_id.split("/", 1)
    return ns not in (".", "..") and name not in (".", "..")


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
    if not is_valid_repo_id(rest):
        raise ValueError(f"expected a safe owner/name, got {raw!r}")
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
