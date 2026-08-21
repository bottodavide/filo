# SPDX-License-Identifier: Apache-2.0
"""Construction and verification of evidence.

Invariant 1 of the system — *no assertion without evidence* — lives here and in
the IR types. These builders are the sanctioned way to attach provenance to a
claim: they compute the snippet fingerprint, stamp the UTC read time, and refuse
to build malformed absence records.

Low-level primitives (:func:`sha256_hex`, :func:`make_snippet`, :func:`utcnow`)
carry no dependency on :mod:`filo.ir`, so ``ir`` can import them freely. The
builder functions import ``ir`` lazily to avoid an import cycle.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from filo.ir import EvidenceRef, ExtractionMethod, LicenseAssertion

SNIPPET_MAX = 500

__all__ = [
    "sha256_hex",
    "make_snippet",
    "utcnow",
    "build_evidence",
    "absent_evidence",
    "absent_license",
    "verify_evidence",
    "SNIPPET_MAX",
]


def sha256_hex(text: str) -> str:
    """Hex SHA-256 of ``text`` encoded as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def make_snippet(text: str | None) -> tuple[str | None, str | None]:
    """Truncate ``text`` to :data:`SNIPPET_MAX` and return ``(snippet, sha256)``.

    Returns ``(None, None)`` for ``None`` input. The fingerprint is computed over
    the *truncated* snippet, i.e. exactly what is stored.
    """
    if text is None:
        return None, None
    snippet = text[:SNIPPET_MAX]
    return snippet, sha256_hex(snippet)


def build_evidence(
    url: str,
    method: ExtractionMethod | str,
    *,
    repo_sha: str | None = None,
    retrieved_at: datetime | None = None,
    text: str | None = None,
    searched_locations: list[str] | None = None,
) -> EvidenceRef:
    """Build an :class:`~filo.ir.EvidenceRef` with snippet fingerprint and UTC stamp."""
    from filo.ir import EvidenceRef, ExtractionMethod

    method = ExtractionMethod(method)
    snippet, snippet_sha = make_snippet(text if method is not ExtractionMethod.ABSENT else None)
    return EvidenceRef(
        url=url,
        repo_sha=repo_sha,
        retrieved_at=retrieved_at or utcnow(),
        method=method,
        snippet=snippet,
        snippet_sha256=snippet_sha,
        searched_locations=searched_locations or [],
    )


def absent_evidence(
    url: str,
    searched_locations: list[str],
    *,
    repo_sha: str | None = None,
    retrieved_at: datetime | None = None,
) -> EvidenceRef:
    """Build ABSENT evidence: a documented, negative search result (invariant 2)."""
    from filo.ir import ExtractionMethod

    if not searched_locations:
        raise ValueError("absent_evidence requires at least one searched location")
    return build_evidence(
        url,
        ExtractionMethod.ABSENT,
        repo_sha=repo_sha,
        retrieved_at=retrieved_at,
        searched_locations=searched_locations,
    )


def absent_license(
    url: str,
    searched_locations: list[str],
    *,
    repo_sha: str | None = None,
    retrieved_at: datetime | None = None,
) -> LicenseAssertion:
    """Build a license assertion recording that no license was found."""
    from filo.ir import LicenseAssertion, LicenseConfidence

    return LicenseAssertion(
        raw_value="",
        confidence=LicenseConfidence.ABSENT,
        evidence=absent_evidence(
            url, searched_locations, repo_sha=repo_sha, retrieved_at=retrieved_at
        ),
    )


def verify_evidence(evidence: EvidenceRef) -> bool:
    """Re-check an evidence record's internal consistency.

    Useful on data that bypassed model validation (e.g. constructed with
    ``model_construct`` or hand-edited). Checks the snippet fingerprint, the
    UTC-aware timestamp, and the ABSENT invariants.
    """
    from filo.ir import ExtractionMethod

    if evidence.retrieved_at.tzinfo is None:
        return False
    if evidence.snippet is not None:
        if evidence.snippet_sha256 != sha256_hex(evidence.snippet):
            return False
    elif evidence.snippet_sha256 is not None:
        return False
    if evidence.method is ExtractionMethod.ABSENT:
        if evidence.snippet is not None or not evidence.searched_locations:
            return False
    return True
